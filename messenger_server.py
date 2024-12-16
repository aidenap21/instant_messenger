import os
import re
import sys
import datetime
import time
import random
import sqlite3
from multiprocessing import Process, Value, Manager, Lock
from socket import *

''' Class that runs for a client's specific server connection '''
class MessengerServer:
    def __init__(self, server_port):
        ''' Open new socket for new client connection '''
        self.server_socket = socket(AF_INET,SOCK_STREAM)
        self.server_socket.bind(('', server_port))
        self.server_socket.listen()
        print(f"New client connection with port: {server_port}")
        self.client_socket, addr = self.server_socket.accept()

        ''' Save database paths'''
        self.users_db_path = "users.db"
        self.msg_db_path   = "messages.db"

        '''
        SERVER STATES
        -1 = Exit State

        0  = Initial State

        1  = Login or Create New Account
        2  = Login, enter username
        3  = Login, enter password

        4  = Create New, enter username
        5  = Create New, enter password

        6  = Menu Screen, enter user to message

        7  = Messaging Screen, enter message to send to user
        '''

        ''' Initialize server state '''
        self.state         = Value("i", 0)

        ''' Create dictionary of client and recipient to share between sending and receiving processes'''
        self.communicators = Manager().dict()
        self.communicators["username"]  = ""
        self.communicators["recipient"] = ""

        ''' Create lock to block race conditions between sending and receiving processes'''
        self.lock = Lock()


    def get_state_responses(self):
        ''' Initialize return values '''
        return_args   = []
        return_msg    = ""
        return_prompt = ""

        ''' Match to current state'''
        match self.state.value:
            case -1:
                return_args.append("EXT")
                return_msg = "Exiting..."

            case 1:
                return_args.append("CLR")
                return_msg    = "Login [L] or Create New Account? [C]"
                return_prompt = "CHOICE"

            case 2:
                return_msg    = "Enter username or return [!back]"
                return_prompt = "USERNAME"

            case 3:
                return_msg    = "Enter password or return [!back]"
                return_prompt = "PASSWORD"
            case 4:
                return_msg    = "Enter username or return [!back]"
                return_prompt = "USERNAME"

            case 5:
                return_msg    = "Enter password or return [!back]"
                return_prompt = "PASSWORD"

            case 6:
                ''' Locks so that only one process generating output '''
                with self.lock:
                    ''' Opens user database '''
                    user_db        = sqlite3.connect(self.users_db_path)
                    user_db_cursor = user_db.cursor()

                    return_args.append("CLR")

                    ''' Get active users '''
                    user_db_cursor.execute("SELECT * FROM registered_users WHERE active=TRUE")
                    db_fetch       = user_db_cursor.fetchall()
                    return_msg    += "Active users:\n\n"

                    for entry in db_fetch:
                        return_msg += entry[0] + "\n"

                    return_msg += "\n"

                    return_prompt = "USER TO MESSAGE"

            case 7:
                ''' Locks so that only one process generating output '''
                with self.lock:
                    ''' Opens message database'''
                    msg_db        = sqlite3.connect(self.msg_db_path)
                    msg_db_cursor = msg_db.cursor()

                    return_args.append("CLR")
                    return_msg = ""

                    ''' Gets all messages between user and recipient and orders by the time sent '''
                    query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                    msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], self.communicators["recipient"], self.communicators["username"]))
                    db_fetch = msg_db_cursor.fetchall()

                    for message in db_fetch:
                        return_msg += f"{message[0]}: {message[3]}\n"

                    return_prompt = f"MESSAGE {self.communicators['recipient']}"

        return return_args, return_msg, return_prompt


    def perform_actions(self, args, msg):
        ''' Initialize return values '''
        return_args    = []
        return_msg     = ""
        return_prompt  = ""

        ''' Open user database '''
        user_db        = sqlite3.connect(self.users_db_path)
        user_db_cursor = user_db.cursor()

        ''' Process arguments '''
        for arg in args:
            match arg:
                case "EXT":
                    ''' Log out user and get response values'''
                    self.state.value                       = -1
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    query                                  = "UPDATE registered_users SET active=FALSE WHERE username=?"
                    user_db_cursor.execute(query, (self.communicators["username"],))
                    user_db.commit()
                
                case _:
                    print(f"INVALID ARGUMENT: {arg}")
        
        ''' Log out user and get response values'''
        if msg == "!exit":
            self.state.value                       = -1
            return_args, return_msg, return_prompt = self.get_state_responses()
            query                                  = "UPDATE registered_users SET active=FALSE WHERE username=?"
            user_db_cursor.execute(query, (self.communicators["username"],))
            user_db.commit()

        ''' State related actions '''
        match self.state.value:
            # Initial Connection 
            case 0:
                self.state.value = 1
                return_args, return_msg, return_prompt = self.get_state_responses()

            # Login or Create New Account
            case 1:
                # Login chosen
                if msg.lower() == "l":
                    self.state.value = 2

                # Create new account chosen
                elif msg.lower() == "c":
                    self.state.value = 4

                return_args, return_msg, return_prompt = self.get_state_responses()

                if self.state.value == 1:
                    return_msg = "Invalid choice\n" + return_msg


            # Login chosen, get username
            case 2:
                if msg == "!back":
                    self.state.value = 1
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    ''' Search database for inputted username '''
                    query    = "SELECT * FROM registered_users WHERE username=? AND active=FALSE"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    ''' Checks if username was found '''
                    if len(db_fetch) > 0:
                        ''' Stores client's username '''
                        self.communicators["username"]         = msg
                        self.state.value                       = 3
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Username does not exist or is already logged in\n" + return_msg

            # Login chosen, get password
            case 3:
                if msg == "!back":
                    self.state.value                       = 2
                    self.communicators["username"]         = ""
                    return_args, return_msg, return_prompt = self.get_state_responses()
                
                else:
                    ''' Searches for password match with username '''
                    query    = "SELECT * FROM registered_users WHERE username=? AND password=?"
                    user_db_cursor.execute(query, (self.communicators["username"], msg))
                    db_fetch = user_db_cursor.fetchall()

                    ''' Logs in if password matches '''
                    if len(db_fetch) > 0:
                        query = "UPDATE registered_users SET active=TRUE WHERE username=?"
                        user_db_cursor.execute(query, (self.communicators["username"],))
                        user_db.commit()
                        self.state.value                       = 6
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg                             = "Password does not match\n" + return_msg


            # Create new account chosen, get username
            case 4:
                if msg == "!back":
                    self.state.value = 1
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    ''' Search database for inputted username '''
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    ''' Progresses if username is unique '''
                    if len(db_fetch) == 0:
                        self.communicators["username"]         = msg
                        self.state.value                       = 5
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Username already exists\n" + return_msg

            # Create new account chosen, get password
            case 5:
                if msg == "!back":
                    self.state.value                       = 4
                    self.communicators["username"]         = ""
                    return_args, return_msg, return_prompt = self.get_state_responses()
                
                else:
                    ''' Adds new user to the database with the new username and password '''
                    query = "INSERT INTO registered_users VALUES (?, ?, TRUE)"
                    user_db_cursor.execute(query, (self.communicators["username"], msg))
                    user_db.commit()

                    self.state.value                       = 6
                    return_args, return_msg, return_prompt = self.get_state_responses()

            
            # Menu screen, get user to message
            case 6:
                if msg == self.communicators["username"]:
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    return_msg += "You cannot message yourself\n"
                
                else:
                    ''' Search database for recipient entered by user '''
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    ''' Progresses if recipient found '''
                    if len(db_fetch) > 0:
                        self.communicators["recipient"]        = msg
                        self.state.value                       = 7
                        return_args, return_msg, return_prompt = self.get_state_responses()

                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg += "User does not exist"


            # Messaging screen, send message to chosen user
            case 7:
                if msg == "!back":
                    self.state.value                = 6
                    self.communicators["recipient"] = ""

                else:
                    ''' Opens message database '''
                    msg_db        = sqlite3.connect(self.msg_db_path)
                    msg_db_cursor = msg_db.cursor()

                    ''' Adds new message to the database '''
                    query = "INSERT INTO sent_messages VALUES (?, ?, DATETIME('now'), ?)"
                    msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], msg))
                    msg_db.commit()

                return_args, return_msg, return_prompt = self.get_state_responses()

        return return_args, return_msg, return_prompt


    def encapsulate(self, args, msg, prompt):
        ''' Add header '''
        encapsulated_msg = "<<<"
        
        ''' Add arguments '''
        for arg in args:
            encapsulated_msg += "$$$" + arg + "$$$"

        ''' Add message '''
        encapsulated_msg += msg
        
        ''' Add prompt '''
        if len(prompt) > 0:
            encapsulated_msg += "|||" + prompt

        ''' Add footer '''
        encapsulated_msg += ">>>"

        return encapsulated_msg
    

    def decapsulate(self, msg):
        ''' Initialize return values '''
        return_args = []
        return_msg  = ""

        ''' Matches completed message '''
        msg_pattern       = r"<<<(.*?)>>>"
        complete_messages = re.findall(msg_pattern, msg, re.DOTALL)
        
        ''' Fails if no complete message found '''
        if len(complete_messages) == 0:
            return_args.append("EXT")
            return_msg = "Message from user corrupted, exiting..."

        else:
            ''' Saves the message in the return '''
            return_msg = complete_messages[0]

            ''' Obtain any arguments given and remove from separate them from basic message '''
            arg_pattern = r"\$\$\$(.*?)\$\$\$"
            return_args = re.findall(arg_pattern, return_msg, re.DOTALL)
            return_msg  = re.sub(arg_pattern, '', return_msg, flags=re.DOTALL)

        ''' Return argument list and message from client '''
        return return_args, return_msg


    def receive_and_send(self):
        ''' Receive from client '''
        received_msg = (self.client_socket.recv(1024)).decode()

        ''' Decapsulate message '''
        args_from_client, msg_from_client = self.decapsulate(received_msg)

        ''' Perform server actions based on message from client '''
        args_to_client, msg_to_client, prompt_to_client = self.perform_actions(args_from_client, msg_from_client)

        ''' Encapsulate return values '''
        encapsulated_msg = self.encapsulate(args_to_client, msg_to_client, prompt_to_client)

        ''' Send to client '''
        self.client_socket.send(encapsulated_msg.encode())

        print(f"Send response of ARGS: [{args_from_client}] and MSG: [{msg_from_client}] to {self.communicators['username']} using PID: {os.getpid()}")


    def send_for_state(self):
        ''' Get message data based on current state '''
        args, msg, prompt = self.get_state_responses()

        ''' Ensures responses for given '''
        if len(args) == 0 and msg == "" and prompt == "":
            return False

        ''' Encapsulate return values '''
        encapsulatead_msg = self.encapsulate(args, msg, prompt)

        ''' Send to client '''
        self.client_socket.send(encapsulatead_msg.encode())

        return True


    def background_update(self):
        ''' Open user and message databases '''
        user_db        = sqlite3.connect(self.users_db_path)
        msg_db         = sqlite3.connect(self.msg_db_path)
        user_db_cursor = user_db.cursor()
        msg_db_cursor  = msg_db.cursor()

        ''' List to store previous database query responses'''
        previous_fetch = []

        ''' Start loop to look for database changes in the background '''
        while self.state.value >= 0:
            # Menu screen state
            if self.state.value == 6:
                ''' Searches for active users '''
                user_db_cursor.execute("SELECT * FROM registered_users WHERE active=TRUE")
                db_fetch       = user_db_cursor.fetchall()

                ''' Checks if database has changed '''
                if db_fetch != previous_fetch:
                    ''' Updates previous if client was successfully notified '''
                    if self.send_for_state():
                        previous_fetch = db_fetch

            # Messaging screen state
            elif self.state.value == 7:
                ''' Searches for messages between client and recipient '''
                query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], self.communicators["recipient"], self.communicators["username"]))
                db_fetch = msg_db_cursor.fetchall()

                ''' Checks if database has changed '''
                if db_fetch != previous_fetch:
                    ''' Updates previous if client was successfully notified '''
                    if self.send_for_state():
                        previous_fetch = db_fetch


    def connect_to_client(self):
        ''' Create process to check database changes in the background '''
        process = Process(target = self.background_update)
        process.start()

        ''' Start loop to handle client messages '''
        while self.state.value >= 0:
            self.receive_and_send()

        ''' Catch all child processes '''
        process.join()


    def __del__(self):
        try:
            ''' Send final message to client to close down '''
            self.state.value  = -1
            args, msg, prompt = self.get_state_responses()
            encapsulated_msg  = self.encapsulate(args, msg, prompt)
            self.client_socket.send(encapsulated_msg.encode())

            ''' Close down connection '''
            print("CONNECTION ENDED")
            self.server_socket.close()
            self.client_socket.close()

        except:
            ''' Failed due to values not being initialized in child process '''
            print("CHILD ENDING")

import os
import re
import sys
import datetime
import time
import random
import sqlite3
from multiprocessing import Value, Manager, Lock
from socket import *

''' Class that runs for a client's specific server connection '''
class MessengerServer:
    def __init__(self, server_port):
        self.server_socket = socket(AF_INET,SOCK_STREAM)
        self.server_socket.bind(('', server_port))
        self.server_socket.listen()
        print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {server_port}")
        self.client_socket, addr = self.server_socket.accept()

        self.user_db     = sqlite3.connect("users.db")
        self.msg_db      = sqlite3.connect("messages.db")
        self.state       = Value("i", 0)

        self.communicators = Manager().dict() # stores username and recipient for background process
        self.communicators["username"]  = ""
        self.communicators["recipient"] = ""

        self.lock = Lock()

        '''
        SERVER STATES
        -1 = Exit State

        0  = Initial State

        1  = Login or Create New Account
        2 = Login, enter username
        3 = Login, enter password

        4 = Create New, enter username
        5 = Create New, enter password

        6  = Menu Screen, enter user to message

        7  = Messaging Screen, enter message to send to user
        '''

    def get_state_responses(self):
        return_args   = []
        return_msg    = ""
        return_prompt = ""

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
                with self.lock:

                    user_db_cursor = self.user_db.cursor()

                    return_args.append("CLR")

                    # Get active users
                    user_db_cursor.execute("SELECT * FROM registered_users WHERE active=TRUE")
                    db_fetch       = user_db_cursor.fetchall()
                    return_msg    += "Active users:\n\n"

                    for entry in db_fetch:
                        return_msg += entry[0] + "\n"

                    return_msg += "\n"

                    return_prompt = "USER TO MESSAGE"

            case 7:
                with self.lock:
                    msg_db_cursor = self.msg_db.cursor()

                    return_args.append("CLR")
                    return_msg = ""

                    query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                    msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], self.communicators["recipient"], self.communicators["username"]))
                    db_fetch = msg_db_cursor.fetchall()

                    # print(f"{len(db_fetch)} MESSAGES FOUND")

                    for message in db_fetch:
                        return_msg += f"{message[0]}: {message[3]}\n"

                    return_prompt = f"MESSAGE {self.communicators['recipient']}"


        return return_args, return_msg, return_prompt


    def perform_actions(self, args, msg):
        return_args    = []
        return_msg     = ""
        return_prompt  = ""
        user_db_cursor = self.user_db.cursor()

        ''' Check arguments '''
        for arg in args:
            match arg:
                case "EXT":
                    self.state.value = -1
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    query      = "UPDATE registered_users SET active=FALSE WHERE username=?"
                    user_db_cursor.execute(query, (self.communicators["username"],))
                    self.user_db.commit()
                
                case _:
                    print(f"INVALID ARGUMENT: {arg}")
        
        if msg == "!exit":
            self.state.value = -1
            return_args, return_msg, return_prompt = self.get_state_responses()
            query      = "UPDATE registered_users SET active=FALSE WHERE username=?"
            user_db_cursor.execute(query, (self.communicators["username"],))
            self.user_db.commit()

        ''' State related actions '''
        match self.state.value:
            # Initial Connection 
            case 0.0:
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
                    return_msg    = "Invalid choice\n" + return_msg


            # Login chosen, get username
            case 2:
                if msg == "!back":
                    self.state.value = 1
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    query    = "SELECT * FROM registered_users WHERE username=? AND active=FALSE"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username found in database
                    if len(db_fetch) > 0:
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
                    query    = "SELECT * FROM registered_users WHERE username=? AND password=?"
                    user_db_cursor.execute(query, (self.communicators["username"], msg))
                    db_fetch = user_db_cursor.fetchall()

                    # Username and password matched in database
                    if len(db_fetch) > 0:
                        query = "UPDATE registered_users SET active=TRUE WHERE username=?"
                        user_db_cursor.execute(query, (self.communicators["username"],))
                        self.user_db.commit()
                        self.state.value = 6
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Password does not match\n" + return_msg


            # Create new account chosen, get username
            case 4:
                if msg == "!back":
                    self.state.value = 1
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username not found in database
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
                    query = "INSERT INTO registered_users VALUES (?, ?, TRUE)"
                    user_db_cursor.execute(query, (self.communicators["username"], msg))
                    self.user_db.commit()
                    self.state.value = 6
                    return_args, return_msg, return_prompt = self.get_state_responses()

            
            # Menu screen, get user to message
            case 6:
                if msg == self.communicators["username"]:
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    return_msg += "You cannot message yourself\n"
                
                else:
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username found in database
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
                    msg_db_cursor = self.msg_db.cursor()
                    query         = "INSERT INTO sent_messages VALUES (?, ?, DATETIME('now'), ?)"
                    msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], msg))
                    self.msg_db.commit()
                return_args, return_msg, return_prompt = self.get_state_responses()


        return return_args, return_msg, return_prompt


    def encapsulate(self, args, msg, prompt):
        ''' Add header '''
        encapsulated_msg = "<<<"
        
        ''' Add arguments '''
        for arg in args:
            encapsulated_msg += "$$$" + arg + "$$$" # wrap argument and add it to the message

        ''' Add message '''
        encapsulated_msg += msg
        
        ''' Add prompt ''' # might need to change this depending on if client expects ||| regardless of prompt being there or not
        if len(prompt) > 0:
            encapsulated_msg += "|||" + prompt

        ''' Add footer '''
        encapsulated_msg += ">>>"

        return encapsulated_msg
    

    def decapsulate(self, msg):
        return_args = [] # such as clearing the terminal
        return_msg  = "" # message to print

        ''' Ensure entire message from the server is received '''
        msg_pattern       = r"<<<(.*?)>>>"
        complete_messages = re.findall(msg_pattern, msg, re.DOTALL)
        
        if len(complete_messages) == 0:
            return_args.append("EXT")
            return_msg = "Message from user corrupted, exiting..."

        else:
            return_msg = complete_messages[0]

            ''' Obtain any arguments given in the message from the server '''
            arg_pattern = r"\$\$\$(.*?)\$\$\$"
            return_args = re.findall(arg_pattern, return_msg, re.DOTALL)
            return_msg  = re.sub(arg_pattern, '', return_msg, flags=re.DOTALL)

        ''' Return argument list and message from client '''
        return return_args, return_msg #, return_prompt


    def receive_and_send(self):
        print(f"Current State before receiving: {self.state.value}")
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

        print(f"Send response of ARGS: [{args_from_client}] and MSG: [{msg_from_client}] to client using PID: {os.getpid()}")


    def send_for_state(self):
        ''' Get message data based on current state '''
        args, msg, prompt = self.get_state_responses()

        if len(args) == 0 and msg == "" and prompt == "":
            return False

        ''' Encapsulate return values '''
        encapsulatead_msg = self.encapsulate(args, msg, prompt)

        ''' Send to client '''
        self.client_socket.send(encapsulatead_msg.encode())

        return True


    def connect_to_client(self):
        user_db_cursor = self.user_db.cursor()
        msg_db_cursor  = self.msg_db.cursor()
        previous_fetch = []

        pid = os.fork()

        while self.state.value >= 0:
            # Parent listens and responds to client
            if pid > 0:
                self.receive_and_send()

            # Child watches for DB changes to update the client
            else:
                if self.state.value == 6:
                    user_db_cursor.execute("SELECT * FROM registered_users WHERE active=TRUE")
                    db_fetch       = user_db_cursor.fetchall()

                    if db_fetch != previous_fetch:
                        print("Child sending update")
                        if self.send_for_state():
                            # Update if message was formed and sent
                            previous_fetch = db_fetch

                elif self.state.value == 7:
                    query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                    msg_db_cursor.execute(query, (self.communicators["username"], self.communicators["recipient"], self.communicators["recipient"], self.communicators["username"]))
                    db_fetch = msg_db_cursor.fetchall()

                    if db_fetch != previous_fetch:
                        print(f"Child sending update {self.communicators}")
                        if self.send_for_state():
                            # Update if message was formed and sent
                            previous_fetch = db_fetch

        if pid > 0:
            os.waitpid(pid, 0)

        else:
            os._exit(0)


    def __del__(self):
        user_db_cursor    = self.user_db.cursor()
        self.state.value        = -1
        args, msg, prompt = self.get_state_responses()
        query             = "UPDATE registered_users SET active=FALSE WHERE username=?"
        user_db_cursor.execute(query, (self.communicators["username"],))
        self.user_db.commit()
        encapsulated_msg = self.encapsulate(args, msg, prompt)
        self.client_socket.send(encapsulated_msg.encode())
        print("CONNECTION ENDED")
        self.server_socket.close()
        self.client_socket.close()
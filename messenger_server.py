import os
import sys
import datetime
import time
import random
import sqlite3
from multiprocessing import Value, Manager
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
        self.state       = Value("f", 0.0)
        self.username    = "" # stores users own username
        self.recepient   = "" # stores username user is messaging

        self.communicators = Manager().list(["username", "recepient"]) # stores username and recepient for background process

        '''
        SERVER STATES
        -1.0 = Exit State

        0.0  = Initial State

        1.0  = Login or Create New Account
        1.10 = Login, enter username
        1.11 = Login, enter password

        1.20 = Create New, enter username
        1.21 = Create New, enter password

        2.0  = Menu Screen, enter user to message

        3.0  = Messaging Screen, enter message to send to user
        '''

    def get_state_responses(self):
        return_args   = []
        return_msg    = ""
        return_prompt = ""

        match self.state.value:
            case -1.0:
                return_args.append("EXT")
                return_msg = "Exiting..."

            case 1.0:
                return_args.append("CLR")
                return_msg    = "Login [L] or Create New Account? [C]"
                return_prompt = "CHOICE"

            case 1.10:
                return_msg    = "Enter username or return [!back]"
                return_prompt = "USERNAME"

            case 1.11:
                return_msg    = "Enter password or return [!back]"
                return_prompt = "PASSWORD"
            case 1.20:
                return_msg    = "Enter username or return [!back]"
                return_prompt = "USERNAME"

            case 1.21:
                return_msg    = "Enter password or return [!back]"
                return_prompt = "PASSWORD"

            case 2.0:
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

            case 3.0:
                msg_db_cursor = self.msg_db.cursor()

                return_args.append("CLR")
                return_msg    = ""

                query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                msg_db_cursor.execute(query, (self.username, self.recepient, self.recepient, self.username))
                db_fetch = msg_db_cursor.fetchall()

                for message in db_fetch:
                    return_msg += f"{message[0]}: {message[3]}\n"

                return_prompt = f"MESSAGE {self.recepient}"


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
                    self.state.value = -1.0
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    query      = "UPDATE registered_users SET active=FALSE WHERE username=?"
                    user_db_cursor.execute(query, (self.username,))
                    self.user_db.commit()
                
                case _:
                    print(f"INVALID ARGUMENT: {arg}")
        
        if msg == "!exit":
            self.state.value = -1.0
            return_args, return_msg, return_prompt = self.get_state_responses()
            query      = "UPDATE registered_users SET active=FALSE WHERE username=?"
            user_db_cursor.execute(query, (self.username,))
            self.user_db.commit()

        ''' State related actions '''
        match self.state.value:
            # Initial Connection 
            case 0.0:
                self.state.value = 1.0
                return_args, return_msg, return_prompt = self.get_state_responses()
            

            # Login or Create New Account
            case 1.0:
                # Login chosen
                if msg.lower() == "l":
                    self.state.value = 1.10

                # Create new account chosen
                elif msg.lower() == "c":
                    self.state.value = 1.20

                return_args, return_msg, return_prompt = self.get_state_responses()

                if self.state.value == 1.0:
                    return_msg    = "Invalid choice\n" + return_msg


            # Login chosen, get username
            case 1.10:
                if msg == "!back":
                    self.state.value = 1.0
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username found in database
                    if len(db_fetch) > 0:
                        self.username                          = msg
                        self.communicators[0]                  = self.username
                        self.state.value                       = 1.11
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Username does not exist\n" + return_msg

            # Login chosen, get password
            case 1.11:
                if msg == "!back":
                    self.state.value      = 1.10
                    self.username         = ""
                    self.communicators[0] = ""
                    return_args, return_msg, return_prompt = self.get_state_responses()
                
                else:
                    query    = "SELECT * FROM registered_users WHERE username=? AND password=?"
                    user_db_cursor.execute(query, (self.username, msg))
                    db_fetch = user_db_cursor.fetchall()

                    # Username and password matched in database
                    if len(db_fetch) > 0:
                        query = "UPDATE registered_users SET active=TRUE WHERE username=?"
                        user_db_cursor.execute(query, (self.username,))
                        self.user_db.commit()
                        self.state.value = 2.0
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Password does not match\n" + return_msg


            # Create new account chosen, get username
            case 1.20:
                if msg == "!back":
                    self.state.value = 1.0
                    return_args, return_msg, return_prompt = self.get_state_responses()

                else:
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username not found in database
                    if len(db_fetch) == 0:
                        self.username                          = msg
                        self.communicators[0]                  = self.username
                        self.state.value                       = 1.21
                        return_args, return_msg, return_prompt = self.get_state_responses()
                    
                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg = "Username already exists\n" + return_msg

            # Create new account chosen, get password
            case 1.21:
                if msg == "!back":
                    self.state.value      = 1.20
                    self.username         = ""
                    self.communicators[0] = ""
                    return_args, return_msg, return_prompt = self.get_state_responses()
                
                else:
                    query = "INSERT INTO registered_users VALUES (?, ?, TRUE)"
                    user_db_cursor.execute(query, (self.username, msg))
                    self.user_db.commit()
                    self.state.value = 2.0
                    return_args, return_msg, return_prompt = self.get_state_responses()

            
            # Menu screen, get user to message
            case 2.0:
                if msg == self.username:
                    return_args, return_msg, return_prompt = self.get_state_responses()
                    return_msg += "You cannot message yourself\n"
                
                else:
                    query    = "SELECT * FROM registered_users WHERE username=?"
                    user_db_cursor.execute(query, (msg,))
                    db_fetch = user_db_cursor.fetchall()

                    # Username found in database
                    if len(db_fetch) > 0:
                        self.recepient = msg
                        self.communicators[1] = self.recepient
                        self.state.value     = 3.0
                        return_args, return_msg, return_prompt = self.get_state_responses()

                    else:
                        return_args, return_msg, return_prompt = self.get_state_responses()
                        return_msg += "User does not exist"


            # Messaging screen, send message to chosen user
            case 3.0:
                if msg == "!back":
                    self.state.value     = 2.0
                    self.recepient = ""
                    self.communicators[1] = ""

                else:
                    msg_db_cursor = self.msg_db.cursor()
                    query         = "INSERT INTO sent_messages VALUES (?, ?, DATETIME('now'), ?)"
                    msg_db_cursor.execute(query, (self.username, self.recepient, msg))
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
        return_args   = [] # such as clearing the terminal
        return_msg    = "" # message to print

        ''' Ensure entire message from the server is received '''
        if msg[:3] == "<<<":
            msg_complete = False
            attempt = 0
            while not(msg_complete):
                if msg[-3:] == ">>>":
                    msg = msg[3:-3] # remove header and footer
                    msg_complete = True

                else: # end of message not fully received
                    msg += (self.client_socket.recv(1024)).decode()
                    attempt +=1

                if attempt == 10:
                    print("Message from client corrupted, exiting...")
                    return_args.append("EXT")
                    return return_args, return_msg
                
        else:
            print("Message from client corrupted, exiting...")
            return_args.append("EXT")
            return return_args, return_msg

        ''' Obtain any arguments given in the message from the server '''
        num_args = msg.count("$$$") // 2
        for i in range(num_args):
            if msg[:3] == "$$$" and msg[6:9] == "$$$":
                return_args.append(msg[3:6])
                msg = msg[9:]

            else: # argument format invalid, '$$$' likely part of message
                break

        ''' Get direct input from the user from the client '''
        return_msg = msg

        ''' Return argument list and message from client '''
        return return_args, return_msg #, return_prompt


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

        print(f"Send response of ARGS: [{args_from_client}] and MSG: [{msg_from_client}] to client using PID: {os.getpid()}")


    def send_for_state(self):
        ''' Get message data based on current state '''
        args, msg, prompt = self.get_state_responses()

        ''' Encapsulate return values '''
        encapsulatead_msg = self.encapsulate(args, msg, prompt)

        ''' Send to client '''
        self.client_socket.send(encapsulatead_msg.encode())


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
                if self.state.value == 2.0:
                    user_db_cursor.execute("SELECT * FROM registered_users WHERE active=TRUE")
                    db_fetch       = user_db_cursor.fetchall()

                    if db_fetch != previous_fetch:
                        self.send_for_state()
                        previous_fetch = db_fetch

                elif self.state.value == 3.0:
                    query = "SELECT * FROM sent_messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY message_time"
                    msg_db_cursor.execute(query, (self.communicators[0], self.communicators[1], self.communicators[1], self.communicators[0]))
                    db_fetch = msg_db_cursor.fetchall()

                    if db_fetch != previous_fetch:
                        self.send_for_state()
                        previous_fetch = db_fetch


    def __del__(self):
        user_db_cursor    = self.user_db.cursor()
        self.state.value        = -1.0
        args, msg, prompt = self.get_state_responses()
        query             = "UPDATE registered_users SET active=FALSE WHERE username=?"
        user_db_cursor.execute(query, (self.username,))
        self.user_db.commit()
        encapsulated_msg = self.encapsulate(args, msg, prompt)
        self.client_socket.send(encapsulated_msg.encode())
        print("CONNECTION ENDED")
        self.server_socket.close()
        self.client_socket.close()
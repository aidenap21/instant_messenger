import os
import sys
import datetime
import time
import random
from socket import *

''' Class that runs for a client's specific server connection '''
class MessengerServer:
    def __init__(self, server_ip, server_port):
        self.server_socket = socket(AF_INET,SOCK_STREAM)
        self.server_socket.bind(('', server_port))
        self.server_socket.listen()
        print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {server_port}")
        self.client_socket, addr = self.server_socket.accept()


    def perform_actions(self, args, msg):
        return_args   = []
        return_msg    = ""
        return_prompt = ""

        ''' Check arguments '''
        for arg in args:
            match arg:
                case "EXT":
                    return_args.append("EXT")
                    return_msg = "Exiting..."
                    # NEED TO KILL SERVER CONNECTION WHEN THIS IS RECEIVED
                
                case _:
                    print(f"INVALID ARGUMENT: {arg}")
        
        ''' Dummy response for now '''
        return_args.append("CLR")
        return_msg    = "This is some message"
        return_prompt = "Type something here"

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
                    print("Message from server corrupted, exiting...")
                    return_msg = "$$$EXIT$$$"
                    return return_args, return_msg
        else:
            print("Message from server corrupted, exiting...")
            return_msg = "$$$EXIT$$$"
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

        ''' Return argument list, message, and prompt from server '''
        return return_args, return_msg #, return_prompt


    def receive_and_send(self):
        # connected = True      # LOOP NEEDS TO BE IMPLEMENTED SOMEWHERE ELSE
        # while connected:
        ''' Receive from client '''
        msg_from_client = (self.client_socket.recv(1024)).decode()
        # print(msg_from_client.decode())
        ''' Decapsulate message '''
        args_from_client, msg_from_client = self.decapsulate(msg_from_client)

        ''' Perform server actions based on message from client '''
        args_to_client, msg_to_client, prompt_to_client = self.perform_actions(args_from_client, msg_to_client)

        ''' Encapsulate return values '''
        encapsulated_msg = self.encapsulate(args_to_client, msg_to_client, prompt_to_client)

        ''' Send to client '''
        self.client_socket.send(encapsulated_msg.encode())

        print(f"Send response of ARGS: [{args_from_client}] and MSG: [{msg_from_client}] to client using PID: {os.getpid()}")


    def __del__(self):
        print("CONNECTION ENDED")
        self.server_socket.close()
        self.client_socket.close()
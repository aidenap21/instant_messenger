import os
import re
import sys
import datetime
from socket import *
from multiprocessing import Value, Manager

class MessengerClient:
    def __init__(self, server_ip, server_port):
        server_address = (server_ip, server_port)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        connected = False
        while not connected:
            try:
                self.client_socket.connect(server_address)
                connected = True
            except:
                print("Failed to initialize, trying again")


    def encapsulate(self, args, msg):
        ''' Add header '''
        encapsulated_msg = "<<<"
        
        ''' Add arguments '''
        for arg in args:
            encapsulated_msg += "$$$" + arg + "$$$" # wrap argument and add it to the message

        ''' Add message and footer '''
        encapsulated_msg += msg + ">>>"

        return encapsulated_msg
    

    def decapsulate(self, msg):
        return_args   = [] # such as clearing the terminal
        return_prompt = "" # prompt for input line

        ''' Obtain any arguments given in the message from the server '''
        arg_pattern = r"\$\$\$(.*?)\$\$\$"
        return_args = re.findall(arg_pattern, msg, re.DOTALL)
        msg         = re.sub(arg_pattern, '', msg, flags=re.DOTALL)

        ''' Get input prompt portion of the message from the server '''
        prompt_pattern  = r"\|\|\|(.*)"
        prompt_match    = re.findall(prompt_pattern, msg, re.DOTALL)
        msg             = re.sub(prompt_pattern, '', msg, flags=re.DOTALL)

        if len(prompt_match) > 0:
            return_prompt = prompt_match[0]
        
        else:
            return_prompt = ""

        ''' Return argument list, message, and prompt from server '''
        return return_args, msg, return_prompt


    def send(self, args, msg):
        ''' Encapsulate message '''
        msg_to_server = self.encapsulate(args, msg)

        ''' Send to server '''
        self.client_socket.sendall(msg_to_server.encode())
    

    def receive(self):
        ''' Receive from server '''
        msg_from_server = (self.client_socket.recv(1024)).decode()

        ''' Return decapsulated message '''
        return self.decapsulate(msg_from_server)
    

    def connect_to_server(self):
        ''' Sets up initial connetion message elements '''
        args_to_server = []
        msg_to_server  = "Initial Connection"

        server_output      = ""
        args_from_server   = []
        msg_from_server    = ""
        prompt_from_server = Manager().list([""])

        msg_pattern = r"<<<(.*?)>>>"

        connected = Value("b", True)

        pid = os.fork()

        while connected.value:
            if pid > 0:
                client_ended = False
                self.send(args_to_server, msg_to_server)

                args_to_server = []
                msg_to_server  = ""

                if connected.value and not client_ended:
                    # if prompt_from_server[0] == "":
                    #     msg_to_server = input()
                    # else:
                    #     msg_to_server = input(prompt_from_server[0] + ": ")
                    while msg_to_server == "":
                        msg_to_server = input()
                    
                    if msg_to_server == "!exit":
                        args_to_server.append("EXT")
                        msg_to_server = ""
                        client_ended  = True
            
            else:
                ''' Receive from server '''
                server_output    += (self.client_socket.recv(1024)).decode()

                complete_messages = re.findall(msg_pattern, server_output, re.DOTALL)
                server_output     = re.sub(msg_pattern, "", server_output, flags=re.DOTALL)

                for msg in complete_messages:
                    args_from_server, msg_from_server, prompt_from_server[0] = self.decapsulate(msg)

                    for arg in args_from_server:
                        match arg:
                            case "EXT":
                                connected.value = False
                            case "CLR":
                                os.system('cls' if os.name == 'nt' else 'clear')
                            case _:
                                print("INVALID ARGUMENT FROM SERVER")
                    
                    # print(f"LENGTH OF MSG: {len(msg_from_server)}")
                    print(msg_from_server)
                    print(prompt_from_server[0])

        if pid > 0:
            os.waitpid(pid, 0)

        else:
            os._exit(0)


    def __del__(self):
        print("CONNECTION ENDED")
        self.client_socket.close()
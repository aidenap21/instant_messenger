import os
import sys
import datetime
from socket import *

class MessengerClient:
    def __init__(self, server_ip, server_port):
        server_address = (server_ip, server_port)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(server_address)


    def encapsulate(self, args, msg):
        ''' Prepare message for sending to server '''
        encapsulated_msg = "<<<" # add header to the message
        
        for arg in args:
            encapsulated_msg += "$$$" + arg + "$$$" # wrap argument and add it to the message

        encapsulated_msg += msg + ">>>" # add msg and footer to the message

        return encapsulated_msg
    

    def decapsulate(self, msg):
        return_args   = [] # such as clearing the terminal
        return_msg    = "" # message to print
        return_prompt = "" # prompt for input line

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
                    return return_args, return_msg, return_prompt
        else:
            print("Message from server corrupted, exiting...")
            return_msg = "$$$EXIT$$$"
            return return_args, return_msg, return_prompt

        ''' Obtain any arguments given in the message from the server '''
        num_args = msg.count("$$$") // 2
        for i in range(num_args):
            if msg[:3] == "$$$" and msg[6:9] == "$$$":
                return_args.append(msg[3:6])
                msg = msg[9:]

            else: # argument format invalid, '$$$' likely part of message
                break

        ''' Get print out portion of the message from the server '''
        for i in range(len(msg)):
            if msg[:3] == "|||": # checks if end of print out message
                msg = msg[3:]
                break
            else:
                return_msg += msg[0]
                msg = msg[1:]

        ''' Get input prompt portion of the message from the server '''
        return_prompt = msg

        ''' Return argument list, message, and prompt from server '''
        return return_args, return_msg, return_prompt


    def send_and_receive(self, args, msg):
        ''' Encapsulate message '''
        msg_to_server = self.encapsulate(args, msg)

        ''' Send and receive '''
        self.client_socket.sendall(msg_to_server.encode())

        msg_from_server = (self.client_socket.recv(1024)).decode()

        ''' Return decapsulated message '''
        return self.decapsulate(msg_from_server)


    def __del__(self):
        self.client_socket.close()


def main(): # handles welcome port connection and passes client specific port to MessengerClient
    connection_port = "Unavailable"
    connection_attempts = 0

    ''' Connect to welcoming socket '''
    while connection_port == "Unavailable" and connection_attempts < 10:
        server_ip       = "192.168.56.1"#sys.argv[1]
        welcome_port    = 50000#int(sys.argv[2])
        server_address  = (server_ip, welcome_port)
        client_socket   = socket(AF_INET, SOCK_STREAM)
        client_socket.connect(server_address)
        connection_port = (client_socket.recv(1024)).decode()
        client_socket.close()

        if connection_port == "Unavailable":
            print("Initial connection failed, trying again...")
            connection_attempts += 1


    if connection_attempts == 10:
        print("Server is currently unavailable")
        exit()
    
    else:
        connection_port = int(connection_port)
        client          = MessengerClient(server_ip, connection_port)

        args_to_server = []
        msg_to_server  = "Initial Connection"

        args_from_server   = []
        msg_from_server    = ""
        prompt_from_server = ""

        connected = True

        while connected:
            args_from_server, msg_from_server, prompt_from_server = client.send_and_receive(args_to_server, msg_to_server)

            for arg in args_from_server:
                match arg:
                    case "EXT":
                        connected = False
                    case "CLR":
                        os.system('cls' if os.name == 'nt' else 'clear')
                    case _:
                        print("INVALID ARGUMENT FROM SERVER")
            
            print(msg_from_server)
            
            if connected:
                if prompt_from_server == "":
                    msg_to_server = input(prompt_from_server)
                else:
                    msg_to_server = input(prompt_from_server + ": ")

        del client

main()
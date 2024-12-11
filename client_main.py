import os
import sys
import datetime
from socket import *
from messenger_client import MessengerClient


def main(): # handles welcome port connection and passes client specific port to MessengerClient
    connection_port = "Unavailable"
    connection_attempts = 0

    ''' Connect to welcoming socket '''
    while connection_port == "Unavailable" and connection_attempts < 10:
        server_ip       = sys.argv[1]
        welcome_port    = int(sys.argv[2])
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
                        print("Told to exit by the server")
                        connected = False
                        break # delete later
                    case "CLR":
                        os.system('cls' if os.name == 'nt' else 'clear')
                    case _:
                        print("INVALID ARGUMENT FROM SERVER")
            
            print(msg_from_server)
            
            args_to_server = []
            msg_to_server  = ""

            if connected:
                if prompt_from_server == "":
                    msg_to_server = input(prompt_from_server)
                else:
                    msg_to_server = input(prompt_from_server + ": ")
                
                if msg_to_server == "!exit":
                    args_to_server.append("EXT")
                    msg_to_server = ""

        print("CONNECTION ENDED")
        del client

main()
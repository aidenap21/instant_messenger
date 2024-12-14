import os
import sys
import datetime
from socket import *
from messenger_client import MessengerClient


def main():
    ''' Initialize port value '''
    connection_port     = "Unavailable"
    connection_attempts = 0

    ''' Connect to welcoming socket '''
    while connection_port == "Unavailable" and connection_attempts < 10:
        server_ip       = sys.argv[1]
        welcome_port    = int(sys.argv[2])
        server_address  = (server_ip, welcome_port)
        client_socket   = socket(AF_INET, SOCK_STREAM)
        client_socket.connect(server_address)

        ''' Receive client specific port from server '''
        connection_port = (client_socket.recv(1024)).decode()
        client_socket.close()

        if connection_port == "Unavailable":
            print("Initial connection failed, trying again...")
            connection_attempts += 1

    ''' Times out if server is unavailable '''
    if connection_attempts == 10:
        print("Server is currently unavailable")
        exit()
    
    else:
        ''' Run client interaction with the server '''
        connection_port = int(connection_port)
        client          = MessengerClient(server_ip, connection_port)
        client.connect_to_server()
        del client


if __name__ == "__main__":
    main()
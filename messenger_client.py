import sys
import datetime
from socket import *

class MessengerClient:
    def __init__(self, server_ip, server_port):
        server_address = (server_ip, server_port)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(server_address)

        sentence             = "Initial Connection"
        self.client_socket.send(sentence.encode())

        server_prompt        = self.client_socket.recv(1024)
        print(server_prompt.decode())

        #get user input here and send it back to the server


        # self.client_socket.close() # don't want to close until log out?

def main(): # handles welcome port connection and passes client specific port to MessengerClient
    connection_port = "unavailable"
    connection_attempts = 0
    while connection_port == "unavailable" and connection_attempts < 10:
        server_ip = sys.argv[1]
        welcome_port = int(sys.argv[2])
        server_address = (server_ip, welcome_port)
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect(server_address)

        sentence = "Requesting Port"
        client_socket.send(sentence.encode())

        connection_port = (client_socket.recv(1024)).decode()


        if connection_port == "unavailable":
            print("Initial connection failed, trying again...")
            connection_attempts += 1

    if connection_attempts == 10:
        print("Server is currently unavailable")
        exit()
    
    else:
        connection_port = int(connection_port)
        client = MessengerClient(server_ip, connection_port)
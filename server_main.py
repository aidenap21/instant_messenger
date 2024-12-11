import os
import sys
import datetime
import time
import random
from socket import *
from messenger_server import MessengerServer

''' Welcoming Socket '''
serverPort   = int(50000)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen()
print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")

welcoming = True

while welcoming:
    connectionSocket, addr = serverSocket.accept()
    new_port = random.randint(50001, 60000)

    print("Received connection")

    pid = os.fork()

    # Child process runs new client connection
    if pid == 0:
        serverSocket.close()
        welcoming = False
        print(f"Child PID: {pid}")
        server = MessengerServer(new_port)
        server.connect_client()
    # Parent process runs welcoming socket
    else:
        connectionSocket.sendall(str(new_port).encode())

    connectionSocket.close()
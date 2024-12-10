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

parent_pid = os.getpid()
pid        = parent_pid

while pid == parent_pid:
    connectionSocket, addr = serverSocket.accept()
    new_port = random.randint(50001, 60000)

    connectionSocket.sendall(str(new_port).encode())
    connectionSocket.close()

    print("Received connection")

    pid = os.fork()
    if pid != parent_pid:
        serverSocket.close()
        print(f"Child PID: {pid}")
        # ADD SERVER LOOP HERE
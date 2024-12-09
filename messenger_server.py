import sys
import datetime
import time
import random
from socket import *

serverPort   = int(50000)
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")

connectionSocket, addr = serverSocket.accept()
new_port = random.randint(50001, 60000)

connectionSocket.send(str(new_port).encode())
connectionSocket.close()
print("Received connection")


while True:
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind(('', new_port))
    serverSocket.listen(1)
    print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {new_port}")

    connectionSocket, addr = serverSocket.accept()

    msg_to_client = "<<<$$$CLR$$$this is my test message|||response?"
    connectionSocket.send(msg_to_client.encode())
    print("Received connection")
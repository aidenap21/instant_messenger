import sys
import datetime
import time
import random
from socket import *

serverPort   = int(50000)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen()
print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")

connectionSocket, addr = serverSocket.accept()
new_port = random.randint(50001, 60000)

connectionSocket.sendall(str(new_port).encode())
connectionSocket.close()
serverSocket.close()
print("Received connection")

serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('', new_port))
serverSocket.listen()
print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {new_port}")
connectionSocket, addr = serverSocket.accept()

connected = True
while connected:
    msg_from_client = connectionSocket.recv(1024)
    print(msg_from_client.decode())
    if "$$$EXT$$$" in msg_from_client.decode():
        msg_to_client = "<<<$$$EXT$$$Exiting...>>>"
        connected = False
    else:
        msg_to_client = "<<<$$$CLR$$$this is my test message|||response?>>>"
    connectionSocket.send(msg_to_client.encode())
    print("Received connection")

serverSocket.close()
connectionSocket.close()
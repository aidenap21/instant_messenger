import sys
import datetime
import time
from socket import *

serverPort   = int(sys.argv[1])
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")
while True:
	connectionSocket, addr = serverSocket.accept()
	currentTime		       = str(datetime.datetime.now())

	connectionSocket.send(currentTime.encode())
	connectionSocket.close()
	print("Received connection")
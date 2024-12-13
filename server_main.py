import os
import sys
import datetime
import time
import random
import sqlite3
from socket import *
from messenger_server import MessengerServer

def main():
    ''' Welcoming Socket '''
    serverPort   = int(50000)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")

    welcoming = True

    active_ports = []

    user_db        = sqlite3.connect("users.db")
    user_db_cursor = user_db.cursor()
    user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
    user_db.commit()
    
    try:
        while welcoming:
            connectionSocket, addr = serverSocket.accept()

            valid_port = False
            while not valid_port:
                new_port = random.randint(50001, 60000)
                if new_port not in active_ports:
                    active_ports.append(new_port)
                    valid_port = True

            print("Received connection")

            pid = os.fork()

            # Child process runs new client connection
            if pid == 0:
                serverSocket.close()
                welcoming = False
                print(f"Child PID: {pid}")
                server = MessengerServer(new_port)
                server.connect_to_client()
                del server

            # Parent process runs welcoming socket
            else:
                connectionSocket.sendall(str(new_port).encode())

            connectionSocket.close()

    except KeyboardInterrupt:
        serverSocket.close()

        user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
        user_db.commit()

        print("Server shutting down...")


if __name__ == "__main__":
    main()
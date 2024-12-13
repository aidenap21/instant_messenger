import os
import sys
import datetime
import time
import random
import sqlite3
from socket import *
from messenger_server import MessengerServer
from multiprocessing import Process

def new_connection(port):
    server = MessengerServer(port)
    server.connect_to_client()
    del server

def main():
    ''' Welcoming Socket '''
    serverPort   = int(50000)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    serverSocket.settimeout(1.0)
    print(f"The server is ready to receive at IP {gethostbyname(gethostname())} with port: {serverPort}")

    welcoming = True

    active_ports = []

    user_db        = sqlite3.connect("users.db")
    user_db_cursor = user_db.cursor()
    user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
    user_db.commit()

    processes = []

    try:
        while welcoming:
            try:
                connectionSocket, addr = serverSocket.accept()

            # Times out periodically to handle KeyboardInterrupt
            except TimeoutError:
                continue

            valid_port = False
            while not valid_port:
                new_port = random.randint(50001, 60000)
                if new_port not in active_ports:
                    active_ports.append(new_port)
                    valid_port = True

            print("Received connection")

            processes.append(Process(target = new_connection, args = (new_port,)))
            processes[-1].start()
            
            connectionSocket.sendall(str(new_port).encode())
            connectionSocket.close()

    except KeyboardInterrupt:
        serverSocket.close()

        user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
        user_db.commit()

        for process in processes:
            process.join()

        print("Server shutting down...")


if __name__ == "__main__":
    main()
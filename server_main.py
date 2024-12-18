import os
import sys
import datetime
import time
import random
import sqlite3
from socket import *
from messenger_server import MessengerServer
from multiprocessing import Process

''' This function was created with help from stackoverflow '''
def get_local_ip():
    ''' Try to connect to public server '''
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.connect(("8.8.8.8", 80))

    ''' Get local IP from connection '''
    local_ip = serverSocket.getsockname()[0]
    return local_ip


def new_connection(port):
    ''' Handle client interaction '''
    server = MessengerServer(port)
    server.connect_to_client()
    del server


def main():
    ''' Create welcoming socket '''
    serverPort   = int(50000)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', serverPort))
    serverSocket.listen()
    serverSocket.settimeout(1.0)
    print(f"The server is ready to receive at IP {get_local_ip()} with port: {serverPort}")

    ''' List of port numbers already used '''
    active_ports = []

    ''' Reset all user's connection status '''
    user_db        = sqlite3.connect("users.db")
    user_db_cursor = user_db.cursor()
    user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
    user_db.commit()

    ''' List of client-specific server processes '''
    processes = []

    ''' Start welcoming loop '''
    try:
        while True:
            try:
                ''' Accept new connection to welcoming socket '''
                connectionSocket, addr = serverSocket.accept()

            except TimeoutError:
                ''' Times out periodically to handle KeyboardInterrupt '''
                continue

            except:
                ''' Catches other errors in initializing welcome socket '''
                raise

            ''' Gets a new port for the client to connect to '''
            valid_port = False
            while not valid_port:
                new_port = random.randint(50001, 60000)
                if new_port not in active_ports:
                    active_ports.append(new_port)
                    valid_port = True

            print("Received connection")

            ''' Start new client-specific process '''
            processes.append(Process(target = new_connection, args = (new_port,)))
            processes[-1].start()
            
            ''' Send port number to the new connection '''
            connectionSocket.sendall(str(new_port).encode())
            connectionSocket.close()

    except:
        ''' Catches errors in welcoming server '''
        ''' Close welcoming socket '''
        serverSocket.close()

        ''' Log out users '''
        user_db_cursor.execute("UPDATE registered_users SET active=FALSE")
        user_db.commit()

        ''' Catch all client-specific connections '''
        for process in processes:
            process.terminate()

        print("Server shutting down...")


if __name__ == "__main__":
    main()
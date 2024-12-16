Python Instant Messenger
=======================
Server Setup
------------
To start up the host server of the messaging application run the server_main.py file.
```
python server_main.py
```
This get the IP address of your local system and outputs it with the welcoming port number of 50000. Any device within the server's local network should now be able to connect to the server

Client Connection
-----------------
Run the client_main.py file with the given IP and welcoming port that the server outputs after start up.
```
python client_main.py xxx.xxx.xxx.xxx 50000
```
This will connect the client to the welcoming socket of the server, before assigning it to a new port that the server opens up.

Client Interaction
------------------
After the client has been connected, they can login to the application and then begin messaging. On the menu screen the client can view all the active users, including themselves. They can choose any valid username to message, whether the user is active or no, so long as the account has been created. Usernames are case sensitive for both logging in and when entering whom to message on the menu.

Useful Commands
---------------
There are back commands and exit commands built in for the user.
If the user enters `!back` in the command line, they will return to the previous screen, with the exception of the initial login pages. 
If the user enters `!exit` in the command line, the client will send a final message to tell the server they are disconnecting, and then will shut down the client's application.

Security Flaws
--------
As this project was done primarily to focus on the network and application sides of things, the security of it is majorly flawed.
1. Passwords and messages between users are all stored in plaintext within their respective SQLite databases. That being said, databases are completely local to the machine running the server, so clients ideally cannot just open them up to read the contents.
2. Header, footer, argument, and prompt identifiers within each message can easily be exploited. If the client is aware of how the message is encapsulated before being sent to the server, they can inject the identifiers into their input strings and potentially cause harm to the program.
3. The server currently prints out lots of debug messages which contain the messages received from clients. In theory, the person running the server or anyone who may have access to its output would be able to see everything the clients are sending, as they send it.

Platforms
----------
The programs are both tested to run on Windows systems. The architecture was initially created for Linux, but then was changed to ensure Windows users are able to utilize it. Both server and client should be able to run on Linux systems still, but it is untested as of right now.

Future Improvements
-------------------
If time allows, there are many things that could vastly improve this project.
1. **Graphical User Interface:** Creating a proper GUI for the client program would enhance the user experience. It would remove the need for the command line commands and allow for buttons to exist to send messages to the server when specific text input is not needed.
2. **Message Encryption:** Adding encryption to each message that it sent from the client and server would make it where the server runner does not have access to reading the data of users easily.
3. **Password Encryption:** Encrypting each password within the database by using some sort of hash function would prevent someone from looking at the database and uncovering every users' password.
4. **Publicly Available Server:** Setting up the server to allow it to connect to devices outside of its local network would allow for the messenger to be usable with people from all over.

import os
import re
import sys
import datetime
import tkinter
from socket import *
from multiprocessing import Process, Value, Manager, Queue

class ClientGui:
    def __init__(self, root, queue):
        self.root = root
        self.queue = queue

        # Setting up GUI elements
        self.text_area = tkinter.Text(root, state='disabled', wrap = 'word', height = 20, width = 50)
        self.text_area.pack(pady = 10)

        self.entry = tkinter.Entry(root, width = 40)
        self.entry.pack(side=tkinter.LEFT, padx = 10)

        self.send_button = tkinter.Button(root, text = "Send", command=self.pass_message)
        self.send_button.pack(side=tkinter.LEFT, padx = 10)

    def pass_message(self):
        message = self.entry.get()
        if message:
            self.queue.put(message)
            self.entry.delete(0, tkinter.END)

    def update_window(self, msg):
        self.text_area.config(state = "normal")
        self.text_area.insert(tkinter.END, msg + "\n")
        self.text_area.config(state = "disabled")
        self.text_area.see(tkinter.END)

    def start(self)
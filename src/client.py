"""CD Chat client program"""
import logging
import sys
import socket 
import selectors
import os
import fcntl

from .protocol import CDProto

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.channel = ""
        self.host = "localhost"
        self.port = 5000
        self.selector = selectors.DefaultSelector()
        self.clientChannels = []

        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.selector.register(sys.stdin, selectors.EVENT_READ, self.send_msg)
        print("Client {} as been initialized".format(self.name))

    

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect((self.host, self.port))
        self.selector.register(self.sock, selectors.EVENT_READ, self.receive)
        CDProto.send_msg(self.sock, CDProto.register(self.name))
        logging.debug(f"Connected to chat server")

        print("Connection established with chat server")

    def receive(self, sock, mask):
        """Receive message from server."""
        msg = CDProto.recv_msg(self.sock)
        print(f'\n< {msg.message}')
        logging.debug(f"Received message: {msg}")



    def loop(self):
        """Loop indefinetely."""
        while True:
            sys.stdout.write(">")
            sys.stdout.flush()
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def send_msg(self, stdin, mask):

        message = stdin.readline().strip()

        #condicao para saida do server
        if message == "exit" and len(message.split(" ")) == 1:
            print(f'{self.name} left the server.')
            self.selector.unregister(self.sock)
            self.sock.close()
            sys.exit()

        #entrar numa sala de chat
        elif message.split(" ")[0] == "/join" and len(message.split(" ")) == 2:
            self.channel = message.split(" ")[1]

            if self.channel in self.clientChannels:
                print(f'Error. {self.name} is already in this channel: "{self.channel}".')

            else:
                self.clientChannels.append(self.channel) 
                print(f"{self.name} has joined {self.channel}")
                joinMessage = CDProto.join(self.channel)
                CDProto.send_msg(self.sock, joinMessage)

        #enviar mensagem para uma sala de chat
        else:
            normalMessage = CDProto.message(message, self.channel)
            CDProto.send_msg(self.sock, normalMessage)

        

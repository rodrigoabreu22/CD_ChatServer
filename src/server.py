"""CD Chat server program."""
import logging
import socket 
import selectors
import json
from .protocol import CDProto

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""

    def __init__(self):
        """Initialize the server."""
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket()
        self.sock.bind(('localhost', 5000))
        self.sock.listen(100)
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        print("Server Chat-Client. Listening on localhost: 5000") 
        self.name = {} # dicionario que guarda o nome de cada utilizador
        self.channels = {} # dicionario que guarda os canais de chat de cada utilizador

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    
    def accept(self, sock, mask):
        conn, addr = sock.accept() 
        print('accepted', conn, 'from', addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)
        #Regista ações no respetivo ficheiro
        logging.debug(f"Accepted connection from {addr}")
        
    def read(self, conn, mask):

        header = int.from_bytes(conn.recv(2), 'big') 
        data = conn.recv(header).decode("utf-8") 

        if data:
            print('Received: ' + data)

            try:
                data_info = json.loads(data)
            except json.JSONDecodeError:
                print("Error reading json")
                return
            
            command = data_info["command"]

            if command == "register":
                user = data_info["user"]

                if user != None:
                    # o utilizador encontra-se no canal default
                    self.name[conn] = user
                    self.channels[conn] = [None]
                    print(user + ' registered with success')
                    logging.debug(f"{user} joined the chat")
                else:
                    print("Error registering user")

            # o utilizador junta-se a um canal
            elif command == "join":
                channel = data_info["channel"]
                channels = self.channels.get(conn)

                if channel == None:
                    print("Error. Invalid channel name")

                elif channel in channels:
                    print("User already in " + channel)

                else:
                    if channels == [None]:
                        self.channels[conn] = [channel]

                    else:
                        self.channels[conn].append(channel)

                    print(f"{self.name[conn]} joined: {channel}")
                    logging.debug(f"{self.name[conn]} joined: {channel}")

                #mensagem para um canal
            elif command == "message": 

                message = data_info["message"]

                if message != None:
                    #manda mensagens para os utilizadores que estão no mesmo canal
                    channel = data_info["channel"] 
                    msgToSend = CDProto.message(f'({self.name[conn]}): {message}')
                    msgEcho = CDProto.message(f'{message}')
                    print(f'{self.name[conn]} -> {message} (channel: {channel})')
                    logging.debug(f'{self.name[conn]} -> {message} (channel: {channel})')

                    for user in self.channels.keys():
                        if channel == "" and user != conn:
                            CDProto.send_msg(user, msgToSend)
                            #mensagem de retorno do exemplo do professor
                            CDProto.send_msg(conn, msgEcho)

                        elif user != conn and channel in self.channels[user]:
                            CDProto.send_msg(user, msgToSend)
                            #mensagem de retorno do exemplo do professor
                            CDProto.send_msg(conn, msgEcho)

                else:
                    print("User cannot send message. Invalid format")
                        
            else:
                print("Invalid command")

        else:
            print('Closing', conn)
            try:
                logging.debug(f'{self.name[conn]} left the server')
                del self.name[conn]
                del self.channels[conn]
            except KeyError as err:
                self.name = {}
            self.sel.unregister(conn)
            conn.close()
    
    



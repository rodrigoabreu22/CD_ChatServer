"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self,command) -> None:
        self.command = command

    def __to_json__(self):
        data = {"command": self.command}
        return json.dumps(data)
    
    def __str__(self):
        return self.__to_json__()

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self,channel: str):
        super().__init__("join")
        self.channel = channel
    
    def __to_json__(self):
        data = {"command": self.command, "channel": self.channel}
        return json.dumps(data)

    def __str__(self):
        return self.__to_json__()

class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, user: str):
        super().__init__("register")
        self.user = user

    def __to_json__(self):
        data = {"command": self.command, "user": self.user}
        return json.dumps(data)
    
    def __str__(self):
        return self.__to_json__()
    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, message: str, channel: str, ts: int):
        super().__init__("message")
        self.message = message
        self.channel = channel
        self.ts = ts

    def __to_json__(self):
        if self.channel is None:
            data = {"command": self.command, "message": self.message, "ts": self.ts}
        else:
            data = {"command": self.command, "message": self.message, "channel": self.channel, "ts": self.ts}

        return json.dumps(data)
    
    def __str__(self):
        return self.__to_json__()

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(message, channel, int(datetime.now().timestamp()))

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        
        message_json = msg.__to_json__()  
        message_bytes = message_json.encode("utf-8") 

        header = len(message_bytes).to_bytes(2, "big") 
        try:
            connection.sendall(header + message_bytes)
        except IOError:
            raise CDProtoBadFormat(msg)


    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        try:
            header = connection.recv(2)
            n = int.from_bytes(header, "big")
            data = connection.recv(n)
            msg = json.loads(data.decode("utf-8"))
        except Exception as e:
            raise CDProtoBadFormat(f"Error decoding message: {str(e)}")

        if msg["command"] == "register":
            return CDProto.register(msg.get("user"))
        
        elif msg["command"] == "join":
            return CDProto.join(msg.get("channel"))
        
        elif msg["command"] == "message":
            message = msg.get("message", "")
            channel = msg.get("channel", None)
            return CDProto.message(message, channel)
        
        else:
            raise CDProtoBadFormat("Unknown command in message")
    


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")

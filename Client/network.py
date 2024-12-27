import socket
import struct
from config import *

class ClientSocket:
    def __init__(self):
        self.host = SERVER_HOST
        self.port = SERVER_PORT
        self.buffer_size = BUFFER_SIZE
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print(f"[DEBUG] Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError as e:
            print("[ERROR]: Connection failed. Make sure the server is running.")
            raise e

    def send_packet(self, packet):
        try:
            self.socket.sendall(packet)
            print(f"[DEBUG] Sent packet: {packet}")
        except Exception as e:
            print("[ERROR]: Failed to send packet.")
            raise e

    def receive_packet(self, nonblocking=False):
        try:
            if nonblocking:
                self.socket.settimeout(0.1)
            else:
                self.socket.settimeout(None)

            data = self.socket.recv(self.buffer_size)
            print(f"[DEBUG] Received raw packet: {data}")

            if len(data) < 2:
                raise ValueError("[ERROR]: Invalid response length")

            status = struct.unpack("!B", data[0:1])[0]
            message_length = struct.unpack("!B", data[1:2])[0]
            message = data[2:2 + message_length].decode()

            print(f"[DEBUG] Unpacked response: Status = {status}, Message = {message}")
            return status, message
        except socket.timeout:
            if nonblocking:
                return None, None
            raise
        finally:
            self.socket.settimeout(None)

    def close(self):
        self.socket.close()
        print("[DEBUG] Connection closed.")
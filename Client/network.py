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

            # Lire les 5 premiers octets (statut + longueur totale sur 4 octets)
            header = self.socket.recv(5)
            if len(header) < 5:
                raise ValueError("[ERROR]: Header incomplete")

            # Décoder le statut et la longueur
            status = header[0]
            message_length = struct.unpack("!I", header[1:])[0]  # 4 octets pour la longueur

            # Lire le message complet
            message_data = b""
            while len(message_data) < message_length:
                chunk = self.socket.recv(min(self.buffer_size, message_length - len(message_data)))
                if not chunk:
                    raise ValueError("[ERROR]: Connection closed during message reception")
                message_data += chunk

            # Log pour tout le paquet brut reçu
            print(f"[DEBUG] Received raw packet: {header + message_data}")

            # Décoder le message
            message = message_data.decode()
            print(f"[DEBUG] Unpacked response: Status = {status}, Message = {message}")
            return status, message

        except socket.timeout:
            if nonblocking:
                return None, None
            raise
        except Exception as e:
            print(f"[ERROR] Exception in receive_packet: {e}")
            raise
        finally:
            self.socket.settimeout(None)

    def close(self):
        self.socket.close()
        print("[DEBUG] Connection closed.")
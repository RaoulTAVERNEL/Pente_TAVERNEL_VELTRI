import socket

class ClientSocket:
    def __init__(self, host, port, buffer_size):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            print("Connection failed. Make sure the server is running.")
            raise

    def send_packet(self, packet):
        self.socket.sendall(packet)

    def receive_packet(self):
        return self.socket.recv(self.buffer_size)

    def close(self):
        self.socket.close()
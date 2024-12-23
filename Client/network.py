import socket

class ClientSocket:
    def __init__(self, host, port, buffer_size):
        """
        Initializes the network socket with server host, port, and buffer size.
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Establishes a connection to the server."""
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except ConnectionRefusedError:
            print("Connection failed. Make sure the server is running.")
            raise

    def send_packet(self, packet):
        """Sends a packet of data to the server."""
        self.socket.sendall(packet)

    def receive_packet(self):
        """Receives a packet of data from the server."""
        return self.socket.recv(self.buffer_size)

    def receive_packet_nonblocking(self):
        """Receives a packet of data from the server in non-blocking mode."""
        try:
            self.socket.settimeout(0.1)  # Set a small timeout for non-blocking behavior
            return self.socket.recv(self.buffer_size)
        except socket.timeout:
            return None
        finally:
            self.socket.settimeout(None)  # Reset to blocking mode

    def close(self):
        """Closes the network connection."""
        self.socket.close()

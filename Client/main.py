import socket

# Define the server address and port
SERVER_HOST = '127.0.0.1'  # Localhost (assuming the server is running on the same machine)
SERVER_PORT = 55555  # Port to connect to


def main():
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
    except ConnectionRefusedError:
        print("Connection failed. Make sure the server is running.")
        return

    while True:
        # Ask the user for input
        message = input("Enter message to send to the server (type 'quit' to exit): ")

        if message.lower() == "quit":
            print("Exiting...")
            break

        try:
            # Send the message to the server
            client_socket.sendall(message.encode())  # Encode the string to bytes

            # Receive the server's response
            response = client_socket.recv(1024)  # Buffer size of 1024 bytes

            # Print the server's response
            print(f"Server response: {response.decode()}")  # Decode the bytes to string
        except Exception as e:
            print(f"Error: {e}")
            break

    # Close the socket after exiting the loop
    client_socket.close()


if __name__ == "__main__":
    main()

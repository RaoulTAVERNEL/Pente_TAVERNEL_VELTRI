import socket
import struct

# Define packet constants
PKT_CONNECT = 10
PKT_LIST_GAME = 21
PKT_CREATE_GAME = 23
PKT_JOIN = 42

# Define the server address and port
SERVER_HOST = '127.0.0.1'  # Localhost (assuming the server is running on the same machine)
SERVER_PORT = 55555  # Port to connect to

# Packet format constants
USERNAME_MAX_LENGTH = 16  # Maximum length for username
PASSWORD_MAX_LENGTH = 16  # Maximum length for password


def pack_credentials(username, password):
    username_bytes = username.encode('utf-8')[:USERNAME_MAX_LENGTH]
    password_bytes = password.encode('utf-8')[:PASSWORD_MAX_LENGTH]

    # Calculate the lengths for packing
    username_length = len(username_bytes)
    password_length = len(password_bytes)

    # Pack the data
    packed_data = struct.pack(
        f"!B{USERNAME_MAX_LENGTH}sB{PASSWORD_MAX_LENGTH}s",
        username_length,
        username_bytes.ljust(USERNAME_MAX_LENGTH, b'\x00'),  # Fill with zeros
        password_length,
        password_bytes.ljust(PASSWORD_MAX_LENGTH, b'\x00')   # Fill with zeros
    )

    # Prepend the packet type to the packed data
    final_packet = struct.pack("!B", PKT_CONNECT) + packed_data

    return final_packet


def unpack_response(response):
    if len(response) < 2:  # Check for at least status and length bytes
        return None, "No response received"

    # Unpack status and message length
    status = response[0]
    message_length = response[1]

    # Ensure we have enough data for the message
    if len(response) < 2 + message_length:
        return None, "Incomplete response received"

    message = response[2:2 + message_length].decode().strip()  # Extract message based on length

    return status, message


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
        # Ask the user for username
        username = input("Enter username (type 'quit' to exit): ")
        if username.lower() == "quit":
            print("Exiting...")
            break

        # Ask for the password
        password = input("Enter password: ")
        print(f"Password length: {len(password)}")  # Debug: Display the length of the password

        packed_message = pack_credentials(username, password)
        print(f"Packed message: {packed_message}")  # Display the packed message
        print(f"Packed message length: {len(packed_message)}")  # Display the packed message length

        try:
            # Send the packed username and password to the server
            client_socket.sendall(packed_message)

            # Receive the server's response
            response = client_socket.recv(1024)  # Buffer size of 1024 bytes

            # Unpack the server's response
            status, message = unpack_response(response)

            # Print the server's response
            print(f"Server response: Status = {status}, Message = '{message}'")

        except Exception as e:
            print(f"Error: {e}")
            break

    # Close the socket after exiting the loop
    client_socket.close()


if __name__ == "__main__":
    main()

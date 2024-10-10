import socket
import struct

# Define the server address and port
SERVER_HOST = '127.0.0.1'  # Localhost (assuming the server is running on the same machine)
SERVER_PORT = 55555  # Port to connect to

# Packet format constants
USERNAME_MAX_LENGTH = 32  # Maximum length for username

def pack_credentials(username):
    """
    Pack the username into a binary format.
    The structure is as follows:
    [username_length (1 byte)][username (up to 32 bytes)]
    """
    username_bytes = username.encode()[:USERNAME_MAX_LENGTH]  # Limit to max length

    username_length = len(username_bytes)

    # Pack the data
    packed_data = struct.pack(
        f"!B{USERNAME_MAX_LENGTH}s",
        1,
        username_bytes.ljust(USERNAME_MAX_LENGTH, b'\x00')
    )
    return packed_data


def unpack_response(response):
    if len(response) < 1:
        return None, "No response received"

    # Unpack status byte
    status = response[0]
    print(f"Raw message received: {response[1:]}")  # Debugging line
    message = response[1:].decode().strip()
    print(f"Decoded message: '{message}'")  # Debugging line

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

        # Pack the username
        packed_message = pack_credentials(username)

        try:
            # Send the packed username to the server
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

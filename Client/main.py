import socket
import struct
from time import sleep

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 55555
BUFFER_SIZE = 1024
AUTH_MAX_LENGTH = 16



##############################################
#                   STATES                   #
##############################################

CURRENT_STATE = None
INITIAL_STATE = 1
LOBBY_STATE = 2
INACTIVE_GAME_STATE = 3
PLAYING_STATE = 4
WAITING_STATE = 5



##############################################
#                  PACKETS                   #
##############################################

# PKT starts with the same number as its corresponding state
PKT_CONNECT = 10
PKT_LIST_GAME = 21
PKT_DISCONNECT = 22
PKT_CREATE_GAME = 23
PKT_JOIN = 24
PKT_QUIT = 30
PKT_MOVE = 40
PKT_GAME_OVER = 41
PKT_ABANDON = 50



##############################################
#                  FUNCTIONS                 #
##############################################

def unpack_response(response):
    if len(response) < 2:
        raise ValueError(f"Response too short: expected at least 2 bytes, got {len(response)} bytes.")

    status = struct.unpack("!B", response[0:1])[0]
    message_length = struct.unpack("!B", response[1:2])[0]

    if len(response) < 2 + message_length:
        raise ValueError(f"Message length mismatch: expected {message_length} bytes, got {len(response[2:])} bytes.")

    message = response[2:2 + message_length].decode()

    return status, message



def pack_credentials(username, password):
    username_bytes = username.encode('utf-8')[:AUTH_MAX_LENGTH]
    password_bytes = password.encode('utf-8')[:AUTH_MAX_LENGTH]

    username_length = len(username_bytes)
    password_length = len(password_bytes)

    packed_data = struct.pack(
        f"!B{AUTH_MAX_LENGTH}sB{AUTH_MAX_LENGTH}s",
        username_length,
        username_bytes.ljust(AUTH_MAX_LENGTH, b'\x00'), # Fill with zeros
        password_length,
        password_bytes.ljust(AUTH_MAX_LENGTH, b'\x00') # Fill with zeros
    )

    final_packet = struct.pack("!B", PKT_CONNECT) + packed_data

    return final_packet



def authenticate(client_socket):
    global CURRENT_STATE
    username = input("Enter username : ")
    password = input("Enter password: ")
    packed_message = pack_credentials(username, password)
    try:
        client_socket.sendall(packed_message)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}")
        if status == 0:
            CURRENT_STATE = LOBBY_STATE
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()



def request_game_list(client_socket):
    game_list_packet = struct.pack("!B", PKT_LIST_GAME)
    try:
        client_socket.sendall(game_list_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}\nTo create a new game, press \"-1\"")
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()



def create_game(client_socket):
    global CURRENT_STATE
    create_game_packet = struct.pack("!B", PKT_CREATE_GAME)
    try:
        client_socket.sendall(create_game_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}")
        if status == 0:
            CURRENT_STATE = INACTIVE_GAME_STATE
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()



def join_game(client_socket, user_input):
    global CURRENT_STATE
    try:
        game_id = int(user_input)
        join_game_packet = struct.pack("!BI", PKT_JOIN, game_id)
        try:
            client_socket.sendall(join_game_packet)
            response = client_socket.recv(BUFFER_SIZE)
            status, message = unpack_response(response)
            print(f"{message}")
            if status == 3:  # If another player joined the game
                CURRENT_STATE = WAITING_STATE  # Move to the active game state
                print("Waiting move from the other player")
            elif status == 2:
                CURRENT_STATE = PLAYING_STATE
                print("Please make a move")
        except Exception as e:
            print(f"Error: {e}")
            client_socket.close()
    except ValueError:
        print("Invalid game ID. Please enter a valid number.")



def handle_inactive_game(client_socket):
    global CURRENT_STATE
    try:
        response = client_socket.recv(BUFFER_SIZE)
        if response:  # Only process if we received something
            status, message = unpack_response(response)
            print(f"{message}")

            if status == 3:  # If another player joined the game
                CURRENT_STATE = WAITING_STATE  # Move to the active game state
                print("Waiting move from the other player")
            elif status == 2:
                CURRENT_STATE = PLAYING_STATE
                print("Please make a move")
            else:
                print(f"Unhandled status: {status}")

    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
        return  # Ensure we exit if there is an error



def determine_winner(client_socket):
    global CURRENT_STATE
    game_over_packet = struct.pack("!B", PKT_GAME_OVER)
    try:
        client_socket.sendall(game_over_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}")
        CURRENT_STATE = LOBBY_STATE
        print("Returning to the lobby.")
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
        return

def handle_waiting(client_socket):
    global CURRENT_STATE

    try:
        response = client_socket.recv(BUFFER_SIZE)
        if response:  # Only process if we received something
            status, message = unpack_response(response)
            print(f"{message}")
            CURRENT_STATE = LOBBY_STATE
            print("Returning to the lobby.")
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
        return  # Ensure we exit if there is an error



##############################################
#                MAIN FUNCTION               #
##############################################

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
    global CURRENT_STATE

    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT)) # Connect to the server
        print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
    except ConnectionRefusedError:
        print("Connection failed. Make sure the server is running.")
        return

    CURRENT_STATE = INITIAL_STATE # Set initial state to disconnected

    print(f"Currently in STATE: {CURRENT_STATE}")

    while True:
        if CURRENT_STATE == INITIAL_STATE:
            authenticate(client_socket)

        elif CURRENT_STATE == LOBBY_STATE:
            request_game_list(client_socket)
            user_input = input()
            if user_input == "-1":
                create_game(client_socket)
            else:
                join_game(client_socket, user_input)

        elif CURRENT_STATE == INACTIVE_GAME_STATE:
            handle_inactive_game(client_socket)

        elif CURRENT_STATE == PLAYING_STATE:
            sleep(4)
            determine_winner(client_socket)

        elif CURRENT_STATE == WAITING_STATE:
            handle_waiting(client_socket)

if __name__ == "__main__":
    main()
import socket
import struct
import pygame
import pygame_gui

# Pygame and GUI initialization
pygame.init()
screen = pygame.display.set_mode((800, 600))
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))
manager = pygame_gui.UIManager((800, 600))
clock = pygame.time.Clock()

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
        username_bytes.ljust(AUTH_MAX_LENGTH, b'\x00'),
        password_length,
        password_bytes.ljust(AUTH_MAX_LENGTH, b'\x00')
    )
    final_packet = struct.pack("!B", PKT_CONNECT) + packed_data
    return final_packet


def authenticate(client_socket, username_textbox, password_textbox, auth_status_label):
    global CURRENT_STATE
    username = username_textbox.get_text()
    password = password_textbox.get_text()

    if username and password:
        packed_message = pack_credentials(username, password)
        try:
            client_socket.sendall(packed_message)
            response = client_socket.recv(BUFFER_SIZE)
            status, message = unpack_response(response)
            print(f"{message}")
            if status == 0:
                CURRENT_STATE = LOBBY_STATE
                auth_status_label.set_text("Authentication successful")
            else:
                auth_status_label.set_text("Authentication failed")
                username_textbox.set_text("")
                password_textbox.set_text("")
        except Exception as e:
            print(f"Error: {e}")
            client_socket.close()
            auth_status_label.set_text("Authentication failed")


def request_game_list(client_socket):
    game_list_packet = struct.pack("!B", PKT_LIST_GAME)
    try:
        client_socket.sendall(game_list_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)

        if status == 1:  # No game available
            print("No game available")
            return "No game available"
        else:
            print(f"{message}\nTo create a new game, press \"-1\"")
            return message  # Assuming the response contains the game list or game details
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
        return ""


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


def join_game(client_socket, game_id):
    global CURRENT_STATE
    try:
        join_game_packet = struct.pack("!BI", PKT_JOIN, game_id)
        client_socket.sendall(join_game_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}")
        if status == 3:  # If another player joined the game
            CURRENT_STATE = WAITING_STATE  # Move to the waiting state
            print("Waiting for a move from the other player")
        elif status == 2:
            CURRENT_STATE = PLAYING_STATE
            print("Your turn, make a move!")
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()


def logout(client_socket):
    global CURRENT_STATE
    logout_packet = struct.pack("!B", PKT_DISCONNECT)
    try:
        client_socket.sendall(logout_packet)
        response = client_socket.recv(BUFFER_SIZE)
        status, message = unpack_response(response)
        print(f"{message}")
        CURRENT_STATE = INITIAL_STATE
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()


##############################################
#                MAIN FUNCTION               #
##############################################

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global CURRENT_STATE

    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
    except ConnectionRefusedError:
        print("Connection failed. Make sure the server is running.")
        return

    CURRENT_STATE = INITIAL_STATE

    # Create the GUI elements for login
    username_textbox = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((300, 200), (200, 30)),
        manager=manager
    )
    password_textbox = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((300, 250), (200, 30)),
        manager=manager
    )
    login_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((350, 300), (100, 50)),
        text="Login",
        manager=manager
    )

    # Create a label for authentication status
    auth_status_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((300, 350), (200, 30)),
        text="",
        manager=manager
    )

    # Authentication screen
    is_running = True
    while is_running:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == login_button:
                authenticate(client_socket, username_textbox, password_textbox, auth_status_label)

        manager.update(time_delta)
        screen.blit(background, (0, 0))  # Effacer l'écran
        manager.draw_ui(screen)
        pygame.display.update()

        # Une fois authentifié, on passe au lobby
        if CURRENT_STATE == LOBBY_STATE:
            break

    # Une fois authentifié, on affiche le lobby
    if CURRENT_STATE == LOBBY_STATE:
        # Effacer l'écran avant d'afficher le lobby
        screen.fill(pygame.Color('#000000'))  # Réinitialise l'écran à un fond noir
        manager.clear_and_reset()  # Optionnel: réinitialise le gestionnaire d'UI

        # Envoie immédiatement la requête de la liste des jeux
        game_list = request_game_list(client_socket)

        is_running = True
        join_button = None  # Initialiser join_button ici pour éviter l'erreur de variable avant affectation
        last_request_time = pygame.time.get_ticks()  # Pour contrôler l'intervalle des requêtes

        while is_running:
            # Display active games
            if pygame.time.get_ticks() - last_request_time >= 5000:  # 5000 ms = 5 secondes
                game_list = request_game_list(client_socket)
                last_request_time = pygame.time.get_ticks()

            if game_list == "No game available":
                # Afficher un message si aucune partie n'est disponible
                no_game_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect((300, 200), (200, 30)),
                    text="No game available",
                    manager=manager
                )

                # Créer seulement les boutons Create New Game et Logout
                create_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((150, 450), (200, 50)),
                    text="Create New Game",
                    manager=manager
                )
                logout_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((550, 450), (100, 50)),
                    text="Logout",
                    manager=manager
                )

            else:
                # Afficher les jeux disponibles et le bouton Join Game
                join_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((300, 450), (100, 50)),
                    text="Join Game",
                    manager=manager
                )
                create_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((150, 450), (200, 50)),
                    text="Create New Game",
                    manager=manager
                )
                logout_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((550, 450), (100, 50)),
                    text="Logout",
                    manager=manager
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False

                manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == join_button:
                        game_id = int(input("Enter the game ID to join: "))
                        join_game(client_socket, game_id)

                    if event.ui_element == create_button:
                        create_game(client_socket)

                    if event.ui_element == logout_button:
                        logout(client_socket)
                        is_running = False

            manager.update(clock.tick(60) / 1000.0)
            screen.blit(background, (0, 0))
            manager.draw_ui(screen)
            pygame.display.update()

    client_socket.close()


if __name__ == "__main__":
    main()

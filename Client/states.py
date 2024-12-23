from constants import *
from utils import unpack_response, pack_credentials
import struct

def parse_game_list(message):
    """
    Parses the game list received from the server into a structured format.
    """
    games = []
    lines = message.split("\n")
    for line in lines[1:]:
        if line.strip():
            games.append(line.strip())
    return games

class StateManager:
    def __init__(self, client_socket):
        """
        Manages the state transitions and server communications for the client.
        """
        self.client_socket = client_socket
        self.current_state = INITIAL_STATE

    def authenticate(self, username, password):
        """
        Sends authentication credentials to the server.
        Updates the state based on the server's response.
        """
        packed_message = pack_credentials(username, password, AUTH_MAX_LENGTH)
        self.client_socket.send_packet(packed_message)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 0:
            self.current_state = LOBBY_STATE
            print("Authentication successful")
        else:
            print("Authentication failed")

    def request_game_list(self):
        """
        Requests the list of available games from the server.
        Returns a list of games if successful.
        """
        packet = struct.pack("!B", PKT_LIST_GAME)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        return parse_game_list(message) if status == 0 else []

    def create_game(self):
        """
        Sends a request to create a new game. Updates the state upon success.
        """
        packet = struct.pack("!B", PKT_CREATE_GAME)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 0:
            self.current_state = INACTIVE_GAME_STATE
            print("Game created successfully")
        else:
            print("Failed to create game")

    def logout(self):
        """
        Sends a logout request to the server. Resets the client state to INITIAL_STATE.
        """
        packet = struct.pack("!B", PKT_DISCONNECT)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 0:
            self.current_state = INITIAL_STATE
            print("Logged out successfully")
        else:
            print("Failed to log out")

    def join_game(self, game_text):
        """
        Sends a request to join a game with the given game text.
        Extracts the game ID from the text even if it contains additional details.
        """
        try:
            # Extract the game ID (assumes "Game X:" format)
            game_id_str = game_text.split(":")[0].split(" ")[1]
            game_id = int(game_id_str)
            print(f"Attempting to join game with ID: {game_id}")

            # Send the join game packet
            packet = struct.pack("!BI", PKT_JOIN, game_id)
            self.client_socket.send_packet(packet)

            # Receive the server's response
            response = self.client_socket.receive_packet()
            status, message = unpack_response(response)
            print(f"Server response: {status}, {message}")

            if status == 2:
                self.current_state = PLAYING_STATE
            elif status == 3:
                self.current_state = WAITING_STATE
            else:
                print("Failed to join game.")
        except ValueError:
            print("Invalid game ID. Ensure the button text follows the format 'Game X: ...'.")
        except Exception as e:
            print(f"An error occurred while attempting to join the game: {e}")

    def handle_playing_state(self):
        """
        Handles the logic for the playing state. Sends the GameOver packet to the server.
        """
        try:
            print("[DEBUG] Entering playing state.")
            packet = struct.pack("!B", PKT_GAME_OVER)
            self.client_socket.send_packet(packet)
            response = self.client_socket.receive_packet()
            status, message = unpack_response(response)
            print(f"[DEBUG] Playing state response: {status}, {message}")
            if status in [0, 1]:
                self.current_state = LOBBY_STATE
        except Exception as e:
            print(f"[ERROR] Issue in playing state: {e}")

    def handle_waiting_state(self):
        """
        Handles the logic for the waiting state. Awaits server notification to transition.
        """
        try:
            response = self.client_socket.receive_packet_nonblocking()
            if response:
                status, message = unpack_response(response)
                print(f"[DEBUG] Waiting state response: {status}, {message}")
                if status == 2:
                    self.current_state = PLAYING_STATE
                elif status in [0, 1]:
                    self.current_state = LOBBY_STATE
        except Exception as e:
            print(f"[ERROR] Issue in waiting state: {e}")

    def process_server_response_nonblocking(self):
        """
        Traite les réponses du serveur en mode non-bloquant.
        """
        try:
            response = self.client_socket.receive_packet_nonblocking()
            if response:
                status, message = unpack_response(response)
                print(f"[DEBUG] Réponse non-bloquante du serveur : Status={status}, Message={message}")

                if status == 2:  # Joueur actif
                    self.current_state = PLAYING_STATE
                    print("[DEBUG] Transition vers PLAYING_STATE (Votre tour de jouer)")
                elif status == 3:  # Joueur en attente
                    self.current_state = WAITING_STATE
                    print("[DEBUG] Transition vers WAITING_STATE (En attente de l'adversaire)")
        except Exception as e:
            print(f"[ERREUR] Échec du traitement des réponses non-bloquantes : {e}")

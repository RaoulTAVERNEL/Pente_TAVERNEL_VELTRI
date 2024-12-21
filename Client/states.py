from constants import *
from utils import unpack_response, pack_credentials
import struct


def parse_game_list(message):
    games = []
    lines = message.split("\n")
    for line in lines[1:]:
        if line.strip():
            games.append(line.strip())
    return games


class StateManager:
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.current_state = INITIAL_STATE

    def authenticate(self, username, password):
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
        packet = struct.pack("!B", PKT_LIST_GAME)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)

        if status == 0:
            return parse_game_list(message)
        else:
            return []

    def create_game(self):
        packet = struct.pack("!B", PKT_CREATE_GAME)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 0:
            self.current_state = INACTIVE_GAME_STATE
            print("Game created successfully")
        else:
            print("Failed to create game")

    def join_game(self, game_id):
        packet = struct.pack("!BI", PKT_JOIN, game_id)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 2:
            self.current_state = PLAYING_STATE
            print("Your turn to play")
        elif status == 3:
            self.current_state = WAITING_STATE
            print("Waiting for the opponent")

    def logout(self):
        packet = struct.pack("!B", PKT_DISCONNECT)
        self.client_socket.send_packet(packet)
        response = self.client_socket.receive_packet()
        status, message = unpack_response(response)
        if status == 0:
            self.current_state = INITIAL_STATE
            print("Logged out successfully")
        else:
            print("Failed to log out")
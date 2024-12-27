import struct
from config import *

class User:
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.current_state = INITIAL_STATE
        self.board_state = [[0] * 19 for _ in range(19)]

    @staticmethod
    def _pack_credentials(username, password):
        username_bytes = username.encode('utf-8')[:AUTH_MAX_LENGTH]
        password_bytes = password.encode('utf-8')[:AUTH_MAX_LENGTH]

        username_length = len(username_bytes)
        password_length = len(password_bytes)

        packed_data = struct.pack(
            f"!B{username_length}sB{password_length}s",
            username_length, username_bytes, password_length, password_bytes)

        return struct.pack("!B", PKT_CONNECT) + packed_data

    def authenticate(self, username, password):
        try:
            print(f"[DEBUG] Attempting authentication with username: {username}, password: {password}")

            # Préparer et envoyer les données d'authentification
            auth_pack = self._pack_credentials(username, password)
            self.client_socket.send_packet(auth_pack)
            # Recevoir la réponse
            status, message = self.client_socket.receive_packet(False)

            # Gestion des états en fonction du statut reçu
            if status == STATUS_AUTH_SUCCESS:
                self.current_state = LOBBY_STATE
                print(f"[DEBUG] Authentication successful: {message}")
            elif status == STATUS_AUTH_FAILED:
                self.current_state = INITIAL_STATE
                print(f"[DEBUG] Authentication failed: {message}")

            return status

        except Exception as e:
            print(f"[ERROR]: Authentication error: {e}")
            raise

    def logout(self):
        try:
            logout_pack = bytes([PKT_DISCONNECT])
            self.client_socket.send_packet(logout_pack)
            status, message = self.client_socket.receive_packet(False)

            if status == STATUS_LOGOUT_SUCCESS:
                self.current_state = INITIAL_STATE
                print(f"[DEBUG] Disconnection successful: {message}")

            return status
        except Exception as e:
            print(f"[ERROR]: during logout: {e}")
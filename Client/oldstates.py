from config import *
from network import ClientSocket

def _decode_board_update(message):
    try:
        data = message.split()
        if data[0] != "BOARD_UPDATE":
            return None

        flat_board = list(map(int, data[1:]))
        if len(flat_board) != BOARD_SIZE * BOARD_SIZE:
            return None

        board = [
            flat_board[i * BOARD_SIZE:(i + 1) * BOARD_SIZE]
            for i in range(BOARD_SIZE)
        ]
        return board
    except Exception as e:
        return None

class StateManager:
    def __init__(self):
        self.current_state = INITIAL_STATE
        self.client_socket = ClientSocket()
        self.gui_manager = None  # Will be set externally to avoid circular dependency


    def join_game(self, game_text):
        try:
            # Extract game ID from the game text (e.g., "Game 1: ...")
            game_id = int(game_text.split()[1].strip(":"))
            packet = bytes([PKT_JOIN]) + game_id.to_bytes(4, 'big')
            self.client_socket.send_packet(packet)
            response = self.client_socket.receive_packet()
            #status, message = unpack_response(response)
            if game_id == 3:  # Playing state
                self.current_state = PLAYING_STATE
                self.gui_manager.show_playing_state()
            elif game_id == 2:  # Waiting state
                self.current_state = WAITING_STATE
                self.gui_manager.show_waiting_state()
            else:
                print("Failed to join the game.")
        except Exception as e:
            print(f"Error during game join: {e}")

    def send_move(self, row, col):
        if self.current_state != PLAYING_STATE:
            return

        try:
            packet = bytes([PKT_MOVE]) + row.to_bytes(4, 'big') + col.to_bytes(4, 'big')
            self.client_socket.send_packet(packet)
            response = self.client_socket.receive_packet()
            if response == 1:  # Invalid move
                self.gui_manager.show_playing_state()  # Stay in playing state to retry
            elif response == 2:  # Waiting for opponent
                self.current_state = WAITING_STATE
            elif response == 3:  # Your turn
                self.current_state = PLAYING_STATE
        except Exception as e:
            print(f"Error sending move: {e}")

    def handle_waiting_state(self):
        try:
            response = self.client_socket.receive_packet_nonblocking()
            if response:

                if response == 3:  # Your turn
                    self.current_state = PLAYING_STATE
                    self.gui_manager.show_playing_state()
                    self.gui_manager.draw_board(self.gui_manager.board)  # Refresh the board
        except Exception as e:
            print(f"Error in waiting state: {e}")

    def handle_playing_state(self):
        try:
            response = self.client_socket.receive_packet_nonblocking()
            if response:
                if response == 5:  # Fin de partie
                    self.current_state = LOBBY_STATE
                    if "You won" in response:
                        self.gui_manager.show_game_result("You won the game!")
                    elif "You lost" in response:
                        self.gui_manager.show_game_result("You lost the game.")
        except Exception as e:
            print(f"Error in playing state: {e}")

    def request_game_list(self):
        try:
            packet = bytes([PKT_LIST_GAME])
            self.client_socket.send_packet(packet)
            response = self.client_socket.receive_packet()

            try:
                decoded_response = response[1:].decode("utf-8")
                game_list = decoded_response.split("\n")
            except UnicodeDecodeError as e:
                return []

            return game_list
        except Exception as e:
            print(f"Error requesting game list: {e}")
            return []
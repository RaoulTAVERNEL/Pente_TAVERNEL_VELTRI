from network import *

def request_game_list(user):
    try:
        game_list_pack = bytes([PKT_LIST_GAME])
        user.client_socket.send_packet(game_list_pack)

        status, message = user.client_socket.receive_packet(False)

        if status == STATUS_LIST_GAMES:
            print(f"[DEBUG] List of games: {message}")

            game_list = []
            for game_data in message.strip().split("\n"):
                try:
                    title, rest = game_data.split(" | ", 1)
                    game_id = int(title.split(":")[0].split()[1].strip())
                    username = title.split(":")[1].strip()

                    score, wins, losses = rest.split(" | ")
                    score = int(score.split(": ")[1].strip())
                    wins = int(wins.split(": ")[1].strip())
                    losses = int(losses.split(": ")[1].strip())

                    game = {
                        'id': game_id,
                        'username': username,
                        'score': score,
                        'wins': wins,
                        'losses': losses
                    }
                    game_list.append(game)
                except (IndexError, ValueError) as e:
                    print(f"[WARNING] Skipping malformed game data: {game_data} - Error: {e}")

            return game_list

        elif status == STATUS_NO_GAME:
            print(f"[DEBUG] No games available: {message}")
            return []

    except Exception as e:
        print(f"[ERROR]: Game list request: {e}")
        return []

def create_game(user):
    try:
        new_game_pack = bytes([PKT_CREATE_GAME])
        user.client_socket.send_packet(new_game_pack)
        status, message = user.client_socket.receive_packet(False)

        if status == STATUS_NEW_GAME_SUCCESS:
            user.current_state = INACTIVE_GAME_STATE
            print(f"[DEBUG] New game created: {message}")
            return status
        elif status == STATUS_NEW_GAME_FAILED:
            user.current_state = LOBBY_STATE
            print(f"[DEBUG] New game failed: {message}")
            return status
        else:
            print(f"[ERROR] Unexpected status: {status}.")
            return STATUS_NEW_GAME_FAILED  # Retour par défaut en cas de problème
    except Exception as e:
        print(f"[ERROR]: Game creation: {e}")
        return STATUS_NEW_GAME_FAILED


def quit_inactive_game(user):
    try:
        quit_pack = bytes([PKT_QUIT])
        user.client_socket.send_packet(quit_pack)
        status, message = user.client_socket.receive_packet(False)

        if status == STATUS_QUIT_GAME:
            user.current_state = LOBBY_STATE
            print(f"[DEBUG] Quitting game successfully: {message}")

        return status
    except Exception as e:
        print(f"[ERROR]: Game quit: {e}")


def get_to_active_game(user):
    try:
        if user.current_state != INACTIVE_GAME_STATE:
            print(f"[ERROR]: Invalid state for checking game: {user.current_state}")
            return None, None

        check_game_pack = bytes([PKT_CHECK_GAME])
        user.client_socket.send_packet(check_game_pack)

        status, message = user.client_socket.receive_packet(nonblocking=True)

        if status == STATUS_CHECK_GAME_NOBODY:
            print(f"[DEBUG] No opponent yet: {message}")
            return STATUS_CHECK_GAME_NOBODY, None
        elif status in [STATUS_BOARD_UPDATE, STATUS_CHECK_GAME_JOINED]:
            print(f"[DEBUG] Synchronizing game state...")
            state_status, board = synchronize_game_state(user)

            # Vérifiez si la synchronisation a réussi
            if state_status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                print("[DEBUG] Synchronization successful. Stopping checks.")
                return state_status, board
        else:
            print(f"[ERROR]: Unexpected status received: {status}")
            return None, None
    except Exception as e:
        print(f"[ERROR]: Getting to active game: {e}")
        return None, None


def synchronize_game_state(user):
    try:
        board = None
        state_status = None

        for _ in range(2):
            status, message = user.client_socket.receive_packet(False)

            if status == STATUS_BOARD_UPDATE:
                board = message
                print(f"[DEBUG] Board synchronized: {board}")
            elif status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                state_status = status
                user.current_state = PLAYING_STATE if status == STATUS_MAKE_MOVE else WAITING_STATE
                print(f"[DEBUG] Player state updated: {message}")

        return state_status, board
    except Exception as e:
        print(f"[ERROR]: Synchronizing game state: {e}")
        return None, None


def join_game(user, game_id):
    try:
        join_pack = bytes([PKT_JOIN]) + game_id.to_bytes(4, 'big')
        user.client_socket.send_packet(join_pack)

        board = None
        state_status = None

        for _ in range(2):
            status, message = user.client_socket.receive_packet(False)

            if status == STATUS_BOARD_UPDATE:
                board = message
            elif status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                state_status = status
                user.current_state = PLAYING_STATE if status == STATUS_MAKE_MOVE else WAITING_STATE
                print(f"[DEBUG] Player state updated: {message}")

        if board is not None and state_status is not None:
            print(f"[DEBUG] Board received: {board}")

            return state_status, board
        else:
            raise Exception("[ERROR]: Incomplete data received from server")

    except (ValueError, IndexError) as e:
        print(f"[ERROR]: Joining game: {e}")

def check_game_state(user):
    try:
        status, message = user.client_socket.receive_packet(nonblocking=True)

        if status is None:
            return STATUS_CHECK_GAME_NOBODY, None

        if status == STATUS_BOARD_UPDATE:
            board = message
            # Recevoir le prochain paquet pour l'état du joueur
            status, message = user.client_socket.receive_packet(False)
            if status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                user.current_state = PLAYING_STATE if status == STATUS_MAKE_MOVE else WAITING_STATE
                return status, board
            else:
                print(f"[WARNING] Unexpected packet after board update: {status}.")
                return STATUS_CHECK_GAME_NOBODY, None
        elif status == STATUS_CHECK_GAME_NOBODY:
            return status, None
        else:
            print(f"[WARNING] Unexpected status: {status}. Defaulting to STATUS_CHECK_GAME_NOBODY.")
            return STATUS_CHECK_GAME_NOBODY, None
    except Exception as e:
        print(f"[ERROR] Check game state: {e}")
        return STATUS_CHECK_GAME_NOBODY, None

def abandon_game(user):
    try:
        abandon_pack = bytes([PKT_ABANDON])
        user.client_socket.send_packet(abandon_pack)
        status, message = user.client_socket.receive_packet(False)

        if status == STATUS_ABANDON_GAME:
            user.current_state = LOBBY_STATE
            print(f"[DEBUG] Game abandoned successfully: {message}")

        return status

    except Exception as e:
        print(f"[ERROR]: Error during game abandon: {e}")

def send_move(user, grid_x, grid_y):
    try:
        # Préparer et envoyer le paquet de mouvement
        move_pack = bytes([PKT_MOVE]) + struct.pack("!BB", grid_x, grid_y)
        user.client_socket.send_packet(move_pack)

        board_update = None
        game_status = None
        additional_message = None

        while True:
            # Recevoir le paquet
            status, message = user.client_socket.receive_packet(False)

            if status == STATUS_BOARD_UPDATE:
                # Met à jour localement les données du plateau
                board_update = message

            elif status in (STATUS_VICTORY, STATUS_LOST, STATUS_WAIT_MOVE, STATUS_MAKE_MOVE):
                # Capture le statut final de la partie
                game_status = status
                additional_message = message
                break

            elif status == STATUS_INVALID_MOVE:
                # Signal d'un coup invalide
                game_status = status
                additional_message = message
                break

        return board_update, game_status, additional_message

    except Exception as e:
        print(f"[ERROR]: Error while sending move: {e}")
        return None, STATUS_FAILED, str(e)

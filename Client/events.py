from game import *
from gui import *

def handle_authentication_events(gui_manager, user):
    running = True
    clock = pygame.time.Clock()

    username_lbl, pw_lbl, username_input, pw_input, login_btn, auth_failed_lbl = gui_manager.show_authentication()

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            gui_manager.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == login_btn:
                username = username_input.get_text()
                password = pw_input.get_text()

                try:
                    status = user.authenticate(username, password)

                    if status == STATUS_AUTH_SUCCESS:
                        running = False
                    elif status == STATUS_AUTH_FAILED:
                        auth_failed_lbl.set_text("Authentication failed. Please try again.")
                        username_input.set_text("")
                        pw_input.set_text("")
                except Exception as e:
                    print(f"[ERROR]: Authentication error: {e}")
                    return False

        gui_manager.manager.update(time_delta)
        gui_manager.screen.blit(gui_manager.background, (0, 0))
        gui_manager.manager.draw_ui(gui_manager.screen)
        pygame.display.update()

    return True

def handle_lobby_events(gui_manager, user):
    running = True
    clock = pygame.time.Clock()

    create_btn, logout_btn, new_game_failed_lbl, confirm_new_game_failed_btn, no_game_label = gui_manager.show_lobby()
    game_buttons = []
    button_to_game_id = {}
    last_update_time = 0
    update_interval = 5.0
    error_displayed = False

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            gui_manager.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == create_btn:
                    try:
                        status = create_game(user)

                        if status == STATUS_NEW_GAME_SUCCESS:
                            running = False
                        elif status == STATUS_NEW_GAME_FAILED:
                            gui_manager.display_new_game_error(
                                create_btn, logout_btn, new_game_failed_lbl, confirm_new_game_failed_btn
                            )
                            error_displayed = True

                            for button in game_buttons:
                                button.kill()
                            if no_game_label:
                                no_game_label.kill()
                    except Exception as e:
                        print(f"[ERROR]: Game creation: {e}")
                        return False

                elif event.ui_element == logout_btn:
                    try:
                        status = user.logout()
                        if status == STATUS_LOGOUT_SUCCESS:
                            running = False
                    except Exception as e:
                        print(f"[ERROR]: Logout error: {e}")
                        return False

                elif event.ui_element == confirm_new_game_failed_btn and error_displayed:
                    (create_btn, logout_btn, new_game_failed_lbl,
                     confirm_new_game_failed_btn, no_game_label) = gui_manager.show_lobby()
                    error_displayed = False

                else:
                    for button, game_id in button_to_game_id.items():
                        if event.ui_element == button:
                            try:
                                status, board = join_game(user, game_id)

                                if status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                                    running = False
                            except Exception as e:
                                print(f"[ERROR]: Failed to join game {game_id}: {e}")

        if not error_displayed:
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time - last_update_time >= update_interval:
                last_update_time = current_time
                try:
                    games = request_game_list(user)

                    if games:
                        if no_game_label:
                            no_game_label.kill()
                        game_buttons, button_to_game_id = gui_manager.show_game_list(games, game_buttons)
                    else:
                        if not no_game_label:
                            no_game_label = pygame_gui.elements.UILabel(
                                relative_rect=pygame.Rect((362, 250), (300, 100)),
                                text="No games available",
                                manager=gui_manager.manager
                            )
                except Exception as e:
                    print(f"[ERROR]: Game list update: {e}")

        gui_manager.manager.update(time_delta)
        gui_manager.screen.blit(gui_manager.background, (0, 0))
        gui_manager.manager.draw_ui(gui_manager.screen)
        pygame.display.update()

    return True

def handle_inactive_game_events(gui_manager, user):
    running = True
    clock = pygame.time.Clock()

    try:
        pending_lbl, lobby_btn, error_lbl = gui_manager.show_inactive_game()

        while running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                gui_manager.manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == lobby_btn:
                    status = quit_inactive_game(user)

                    if status == STATUS_QUIT_GAME:
                        running = False

            status, board = check_game_state(user)

            if status == STATUS_CHECK_GAME_NOBODY:
                pass
            elif status in [STATUS_MAKE_MOVE, STATUS_WAIT_MOVE]:
                running = False

            gui_manager.manager.update(time_delta)
            gui_manager.screen.blit(gui_manager.background, (0, 0))
            gui_manager.manager.draw_ui(gui_manager.screen)
            pygame.display.update()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Exception in handle_inactive_game_events: {e}")

    return True



def handle_playing_state(gui_manager, user):
    clock = pygame.time.Clock()
    running = True
    cell_size = 25
    board_state = user.board_state # Récupère l'état actuel du plateau

    abandon_btn, status_lbl, grid_offset_x, grid_offset_y = gui_manager.show_board(
        board_state, cell_size, status_message="It's your turn!"
    )

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            gui_manager.manager.process_events(event)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == abandon_btn:
                    # Envoyer un paquet d'abandon au serveur
                    abandon_pack = bytes([PKT_ABANDON])
                    user.client_socket.send_packet(abandon_pack)

                    status, message = user.client_socket.receive_packet()
                    if status == STATUS_ABANDON_GAME:
                        print(f"[DEBUG] Abandon confirmed: {message}")
                        gui_manager.show_end_screen(is_winner=False, message="You abandoned the game.")
                        return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                grid_x = (mouse_x - grid_offset_x) // cell_size
                grid_y = (mouse_y - grid_offset_y) // cell_size

                if 0 <= grid_x < 19 and 0 <= grid_y < 19 and board_state[grid_y][grid_x] == 0:
                    move_pack = bytes([PKT_MOVE]) + struct.pack("!BB", grid_y, grid_x)
                    print(f"[DEBUG] Sent move: x={grid_x}, y={grid_y}")
                    user.client_socket.send_packet(move_pack)


        status, message = user.client_socket.receive_packet(nonblocking=True)

        if status == STATUS_BOARD_UPDATE:
            board_state = update_board_state(message)
            user.board_state = board_state
            gui_manager.show_board(board_state, cell_size, status_message="Your turn!")
        elif status == STATUS_WAIT_MOVE:
            user.current_state = WAITING_STATE
            return True
        elif status == STATUS_INVALID_MOVE:
            gui_manager.show_board(board_state, cell_size, status_message="Invalid move. Try again!")
        elif status in [STATUS_VICTORY, STATUS_LOST]:
            is_winner = (status == STATUS_VICTORY)
            return_btn = gui_manager.show_end_screen(is_winner=is_winner, message=message)

            waiting = True
            while waiting:
                time_delta = clock.tick(60) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    gui_manager.manager.process_events(event)
                    if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == return_btn:
                        waiting = False

            gui_manager.manager.clear_and_reset()
            user.current_state = LOBBY_STATE
            return True

        gui_manager.manager.update(time_delta)
        gui_manager.screen.blit(gui_manager.background, (0, 0))
        gui_manager.manager.draw_ui(gui_manager.screen)
        pygame.display.update()




def handle_waiting_state(gui_manager, user):
    clock = pygame.time.Clock()
    running = True
    cell_size = 25
    board_state = user.board_state  # Récupère l'état actuel du plateau

    abandon_btn, status_lbl, grid_offset_x, grid_offset_y = gui_manager.show_board(
        board_state, cell_size, status_message="Waiting for opponent..."
    )

    while running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            gui_manager.manager.process_events(event)

        # Vérifier les messages du serveur
        status, message = user.client_socket.receive_packet(nonblocking=True)

        if status == STATUS_BOARD_UPDATE:
            board_state = update_board_state(message)
            user.board_state = board_state  # Mise à jour de l'état du plateau
            gui_manager.show_board(board_state, cell_size, status_message="Your turn!")
            user.current_state = PLAYING_STATE
            return True
        elif status == STATUS_MAKE_MOVE:
            user.current_state = PLAYING_STATE
            return True
        elif status in [STATUS_VICTORY, STATUS_LOST, STATUS_ABANDON_GAME]:
            is_winner = (status == STATUS_VICTORY)
            if status == STATUS_ABANDON_GAME:
                message = "Your opponent abandoned the game. You win!"
                is_winner = True

            return_btn = gui_manager.show_end_screen(is_winner=is_winner, message=message)

            # Attendre que l'utilisateur clique sur "Back to Lobby"
            waiting = True
            while waiting:
                time_delta = clock.tick(60) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    gui_manager.manager.process_events(event)
                    if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == return_btn:
                        waiting = False

                gui_manager.manager.update(time_delta)
                gui_manager.screen.blit(gui_manager.background, (0, 0))
                gui_manager.manager.draw_ui(gui_manager.screen)
                pygame.display.update()

            user.current_state = LOBBY_STATE
            return False

        gui_manager.manager.update(time_delta)
        gui_manager.screen.blit(gui_manager.background, (0, 0))
        gui_manager.manager.draw_ui(gui_manager.screen)
        pygame.display.update()




def update_board_state(message):
    try:
        print(f"[DEBUG] Raw board message received (length: {len(message)}): {message}")

        # Conversion des valeurs séparées par des virgules en entiers
        board_values = list(map(int, message.strip().split(',')))
        if len(board_values) != 19 * 19:  # Vérifier qu'il y a bien 361 valeurs
            raise ValueError(f"Board data does not contain 361 values (received {len(board_values)}).")

        # Transformation de la liste linéaire en une grille 19x19
        board_state = [board_values[i * 19:(i + 1) * 19] for i in range(19)]
        print(f"[DEBUG] Parsed board state: {board_state}")
        return board_state

    except ValueError as ve:
        print(f"[ERROR] Parsing error: {ve}")
        print(f"[DEBUG] Received message: {message}")
        return [[0] * 19 for _ in range(19)]  # Retourner un plateau vide en cas d'erreur



import pygame
import pygame_gui
from config import *

def get_board_position(mouse_pos):
    """
    Maps mouse position to the corresponding board position.
    """
    x, y = mouse_pos
    col = (x - 50) // 30
    row = (y - 50) // 30

    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None


class GUIManager:
    def __init__(self, state_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.background = pygame.Surface((800, 600))
        self.background.fill(pygame.Color('#FFFFFF'))
        self.manager = pygame_gui.UIManager((800, 600))
        self.state_manager = state_manager
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]  # Initialize game board

    def draw_board(self, board):
        self.background.fill(pygame.Color('#FFFFFF'))
        grid_color = pygame.Color('#000000')

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(50 + col * 30, 50 + row * 30, 30, 30)
                pygame.draw.rect(self.background, grid_color, rect, 1)

                # Draw pieces
                if board[row][col] == 1:
                    pygame.draw.circle(self.background, pygame.Color('#0000FF'), rect.center, 12)
                elif board[row][col] == 2:
                    pygame.draw.circle(self.background, pygame.Color('#FF0000'), rect.center, 12)

        print("Game board drawn.")

    def show_playing_state(self):
        self.manager.clear_and_reset()
        running = True
        clock = pygame.time.Clock()

        while running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = get_board_position(event.pos)
                    if pos:
                        row, col = pos
                        self.state_manager.send_move(row, col)

            self.draw_board(self.board)
            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def show_waiting_state(self):
        self.manager.clear_and_reset()
        running = True
        clock = pygame.time.Clock()

        while running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.state_manager.process_server_response_nonblocking()
            self.draw_board(self.board)  # Ensure the board is refreshed

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def show_lobby(self):
        self.manager.clear_and_reset()
        create_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((150, 450), (200, 50)),
            text="Create New Game",
            manager=self.manager
        )
        logout_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((550, 450), (100, 50)),
            text="Logout",
            manager=self.manager
        )

        running = True
        clock = pygame.time.Clock()
        last_request_time = pygame.time.get_ticks()

        # Ensure game_buttons is a dictionary
        game_buttons = {}

        while running:
            time_delta = clock.tick(60) / 1000.0

            # Update game list every 5 seconds
            if pygame.time.get_ticks() - last_request_time >= 5000:
                games = self.state_manager.request_game_list()
                last_request_time = pygame.time.get_ticks()

                # Clear old buttons
                for button in game_buttons.values():
                    button.kill()
                game_buttons.clear()

                # Dynamically create buttons for each game
                for i, game in enumerate(games):
                    button = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect((50, 50 + i * 50), (700, 40)),
                        text=game,
                        manager=self.manager
                    )
                    game_buttons[game] = button

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                self.manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == create_button:
                        self.state_manager.create_game()
                        if self.state_manager.current_state == INACTIVE_GAME_STATE:
                            self.show_inactive_game()
                            running = False

                    if event.ui_element == logout_button:
                        self.state_manager.logout()
                        if self.state_manager.current_state == INITIAL_STATE:
                            self.show_authentication()
                            running = False

                    # Handle clicks on dynamically created game buttons
                    for game_text, button in game_buttons.items():
                        if event.ui_element == button:
                            self.state_manager.join_game(game_text)
                            running = False
                            if self.state_manager.current_state == PLAYING_STATE:
                                self.show_playing_state()
                            elif self.state_manager.current_state == WAITING_STATE:
                                self.show_waiting_state()

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def show_game_result(self, result):
        self.manager.clear_and_reset()
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((150, 250), (500, 50)),
            text=result,
            manager=self.manager
        )
        back_to_lobby_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((300, 400), (200, 50)),
            text="Back to Lobby",
            manager=self.manager
        )

        running = True
        clock = pygame.time.Clock()

        while running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                self.manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == back_to_lobby_button:
                    self.show_lobby()
                    running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()
import pygame
import pygame_gui
from constants import *

class GUIManager:
    def __init__(self, state_manager):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.background = pygame.Surface((800, 600))
        self.background.fill(pygame.Color('#000000'))
        self.manager = pygame_gui.UIManager((800, 600))
        self.state_manager = state_manager

    def show_inactive_game(self):
        self.manager.clear_and_reset()
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((150, 250), (500, 50)),
            text="New game created. Waiting for opponent...",
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

        games_panel = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((50, 50), (700, 300)),
            html_text="Loading games...",
            manager=self.manager
        )

        join_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((300, 400), (200, 50)),
            text="Join Game",
            manager=self.manager
        )

        running = True
        clock = pygame.time.Clock()
        last_request_time = pygame.time.get_ticks()
        selected_game_id = None

        while running:
            time_delta = clock.tick(60) / 1000.0

            if pygame.time.get_ticks() - last_request_time >= 5000:
                games = self.state_manager.request_game_list()
                games_html = "<br>".join([f"<b>{game}</b>" for game in games])
                games_panel.set_text(games_html)
                last_request_time = pygame.time.get_ticks()

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

                    if event.ui_element == join_button:
                        game_id_input = input("Enter the game ID to join: ")
                        if game_id_input.isdigit():
                            self.state_manager.join_game(int(game_id_input))

                    if event.ui_element == logout_button:
                        self.state_manager.logout()
                        running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def run(self):
        clock = pygame.time.Clock()
        is_running = True

        username_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((300, 200), (200, 30)),
            manager=self.manager
        )
        password_textbox = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((300, 250), (200, 30)),
            manager=self.manager
        )
        login_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((350, 300), (100, 50)),
            text="Login",
            manager=self.manager
        )

        while is_running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False

                self.manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == login_button:
                    username = username_textbox.get_text()
                    password = password_textbox.get_text()
                    self.state_manager.authenticate(username, password)

                    if self.state_manager.current_state == LOBBY_STATE:
                        self.show_lobby()
                        is_running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()
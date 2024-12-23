import pygame
import pygame_gui
from constants import *

class GUIManager:
    def __init__(self, state_manager):
        """
        Initializes the graphical interface, including the screen,
        background, and UI manager.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.background = pygame.Surface((800, 600))
        self.background.fill(pygame.Color('#000000'))
        self.manager = pygame_gui.UIManager((800, 600))
        self.state_manager = state_manager

    def show_lobby(self):
        """
        Displays the lobby screen with options to create a game, log out,
        and dynamically generated buttons for available games.
        """
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

        # Dictionary to store dynamically created buttons for games
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

    def show_waiting_state(self):
        """
        Displays the waiting screen indicating the player is waiting for the opponent's move.
        """
        self.manager.clear_and_reset()
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((150, 250), (500, 50)),
            text="Waiting for opponent's move...",
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

            self.state_manager.handle_waiting_state()

            if self.state_manager.current_state == PLAYING_STATE:
                self.show_playing_state()
                running = False
            elif self.state_manager.current_state == LOBBY_STATE:
                self.show_lobby()
                running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def show_playing_state(self):
        """
        Displays the playing screen where the player can make a move or end the game.
        """
        self.manager.clear_and_reset()
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((150, 250), (500, 50)),
            text="Your turn to play!",
            manager=self.manager
        )
        finish_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((300, 400), (200, 50)),
            text="End Game",
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

                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == finish_button:
                    self.state_manager.handle_playing_state()
                    if self.state_manager.current_state == LOBBY_STATE:
                        self.show_lobby()
                    running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def show_game_result(self, result):
        """
        Displays the game result (win/lose) based on the server's response.
        """
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

    def show_authentication(self):
        """
        Displays the authentication screen where the user can log in
        with their username and password.
        """
        self.manager.clear_and_reset()
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

        running = True
        clock = pygame.time.Clock()

        while running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                self.manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == login_button:
                    username = username_textbox.get_text()
                    password = password_textbox.get_text()
                    self.state_manager.authenticate(username, password)

                    if self.state_manager.current_state == LOBBY_STATE:
                        self.show_lobby()
                        running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

    def run(self):
        """
        Starts the graphical interface by displaying the authentication screen.
        """
        self.show_authentication()

    def show_inactive_game(self):
        """
        Affiche un écran indiquant que la partie est créée et en attente d'un autre joueur.
        Passe automatiquement en état PLAYING_STATE ou WAITING_STATE selon la réponse du serveur.
        """
        self.manager.clear_and_reset()
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((150, 250), (500, 50)),
            text="Partie créée. En attente d'un adversaire...",
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

            # Vérifier les mises à jour du serveur de manière non-bloquante
            self.state_manager.process_server_response_nonblocking()

            if self.state_manager.current_state == PLAYING_STATE:
                self.show_playing_state()
                running = False
            elif self.state_manager.current_state == WAITING_STATE:
                self.show_waiting_state()
                running = False

            self.manager.update(time_delta)
            self.screen.blit(self.background, (0, 0))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

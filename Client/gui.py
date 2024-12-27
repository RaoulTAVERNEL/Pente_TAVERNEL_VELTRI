import pygame
import pygame_gui
from config import *

class GUIManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.background = pygame.Surface(SCREEN_SIZE)
        self.background.fill(pygame.Color('#000000'))
        self.state_manager = INITIAL_STATE
        self.manager = pygame_gui.UIManager(SCREEN_SIZE, "theme.json")

    @staticmethod
    def display_new_game_error(create_btn, logout_btn, new_game_failed_lbl, confirm_new_game_failed_btn):
        create_btn.set_text("")
        logout_btn.set_text("")
        create_btn.set_dimensions((0, 0))
        logout_btn.set_dimensions((0, 0))
        new_game_failed_lbl.set_text("You cannot create a new game right now.")
        confirm_new_game_failed_btn.set_dimensions((200, 50))
        confirm_new_game_failed_btn.set_position((400, 480))
        confirm_new_game_failed_btn.set_text("OK")

    def show_authentication(self):
        pygame.display.set_caption("Authentication")
        self.manager.clear_and_reset()

        username_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 334), (100, 30)),
            text="Username:",
            manager=self.manager,
            object_id="#lbl"
        )

        pw_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 384), (100, 30)),
            text="Password:",
            manager=self.manager,
            object_id="#lbl"
        )

        username_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((472, 334), (200, 30)),
            manager=self.manager,
            object_id="#text_entry"
        )

        pw_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((472, 384), (200, 30)),
            manager=self.manager,
            object_id = "#text_entry"
        )

        login_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((462, 434), (100, 50)),
            text="Login",
            manager=self.manager,
            object_id = "#login_btn"
        )

        auth_failed_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 500), (308, 30)),
            text="",
            manager=self.manager,
            object_id="#error_label"
        )

        return username_lbl, pw_lbl, username_input, pw_input, login_btn, auth_failed_lbl

    def show_lobby(self, show_no_game_label=False):
        pygame.display.set_caption("Lobby")
        self.manager.clear_and_reset()

        create_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((150, 550), (200, 50)),
            text="Create a new game",
            manager=self.manager
        )

        logout_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((750, 550), (100, 50)),
            text="Logout",
            manager=self.manager
        )

        new_game_failed_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 334), (300, 100)),
            text="",
            manager=self.manager,
        )

        confirm_new_game_failed_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((462, 480), (0, 0)),
            text="",
            manager=self.manager
        )

        no_game_label = None
        if show_no_game_label:
            no_game_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((362, 250), (300, 100)),
                text="No games available",
                manager=self.manager
            )

        pygame.display.flip()
        return create_btn, logout_btn, new_game_failed_lbl, confirm_new_game_failed_btn, no_game_label

    def show_game_list(self, games, game_buttons):
        for button in game_buttons:
            button.kill()

        button_to_game_id = {}

        buttons = []
        for i, game in enumerate(games):
            game_info = (f"Game {game['id']}: {game['username']} | "
                         f"Score: {game['score']} | Wins: {game['wins']} | Losses: {game['losses']}")

            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((20, 80 + i * 60), (984, 50)),
                text=game_info,
                manager=self.manager
            )

            button_to_game_id[button] = game['id']
            buttons.append(button)

        return buttons, button_to_game_id

    def show_inactive_game(self):
        pygame.display.set_caption("Game Pending")
        self.manager.clear_and_reset()
        self.background.fill(pygame.Color('#000000'))
        self.screen.blit(self.background, (0, 0))

        pending_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 334), (320, 50)),
            text="Waiting for another player to join the game...",
            manager=self.manager,
            object_id="#pending_label"
        )

        lobby_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((412, 434), (200, 50)),
            text="Quit to Lobby",
            manager=self.manager,
            object_id="#lobby_button"
        )

        error_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((362, 500), (320, 30)),
            text="",
            manager=self.manager,
            object_id="#error_label"
        )

        pygame.display.update()

        return pending_lbl, lobby_btn, error_lbl

    def show_board(self, board_state, cell_size=25, status_message="Waiting..."):
        """
        Affiche le plateau de jeu de Pente avec des cases plus petites et un fond noir.
        :param board_state: Liste 2D représentant l'état du plateau (0 = vide, 1 = joueur 1, 2 = joueur 2).
        :param cell_size: Taille d'une case en pixels.
        :param status_message: Message à afficher au-dessus du plateau.
        """
        pygame.display.set_caption("Pente - Playing")
        self.manager.clear_and_reset()

        # Fond noir
        self.background.fill(pygame.Color('#000000'))

        # Calcul pour centrer le plateau
        grid_width = 19 * cell_size
        grid_height = 19 * cell_size
        grid_offset_x = (1024 - grid_width) // 2
        grid_offset_y = (768 - grid_height) // 2 + 30  # Décalé un peu vers le bas

        # Dessiner le fond en bois clair uniquement sous le plateau
        pygame.draw.rect(self.background, pygame.Color('#D9A066'),
                         pygame.Rect(grid_offset_x, grid_offset_y, grid_width, grid_height))

        # Dessiner la grille
        for x in range(19):
            for y in range(19):
                rect = pygame.Rect(
                    grid_offset_x + x * cell_size,
                    grid_offset_y + y * cell_size,
                    cell_size,
                    cell_size
                )
                pygame.draw.line(self.background, pygame.Color('#000000'), rect.topleft, rect.bottomleft, 1)
                pygame.draw.line(self.background, pygame.Color('#000000'), rect.topleft, rect.topright, 1)

                # Dessiner les pions
                if board_state[y][x] == 1:
                    pygame.draw.circle(self.background, pygame.Color('#000000'), rect.center,
                                       cell_size // 2 - 2)  # Pion noir
                elif board_state[y][x] == 2:
                    pygame.draw.circle(self.background, pygame.Color('#FFFFFF'), rect.center,
                                       cell_size // 2 - 2)  # Pion blanc

        # Afficher un message en haut de l'écran
        status_lbl = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 10), (924, 50)),  # Message au-dessus du plateau
            text=status_message,
            manager=self.manager,
            object_id="#status_label"
        )

        # Bouton pour abandonner
        abandon_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((850, 700), (120, 50)),  # Bouton en bas à droite
            text="Abandon",
            manager=self.manager
        )

        pygame.display.flip()
        return abandon_btn, status_lbl, grid_offset_x, grid_offset_y






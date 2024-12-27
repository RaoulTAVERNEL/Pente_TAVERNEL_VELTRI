from events import *

def states_loop(user, gui_manager):
    while True:
        try:
            if user.current_state == INITIAL_STATE:
                if not handle_authentication_events(gui_manager, user):
                    print("[DEBUG] Exiting from INITIAL_STATE.")
                    return  # Sort du programme

            elif user.current_state == LOBBY_STATE:
                if not handle_lobby_events(gui_manager, user):
                    print("[DEBUG] Exiting from LOBBY_STATE.")
                    return

            elif user.current_state == INACTIVE_GAME_STATE:
                if not handle_inactive_game_events(gui_manager, user):
                    print("[DEBUG] Exiting from INACTIVE_GAME_STATE.")
                    return

            elif user.current_state == PLAYING_STATE:
                print(f"[DEBUG] Current state: {user.current_state}")
                if not handle_playing_state(gui_manager, user):
                    print("[DEBUG] Returning to LOBBY_STATE from PLAYING_STATE.")
                    user.current_state = LOBBY_STATE  # Retour au lobby après le jeu

            elif user.current_state == WAITING_STATE:
                print(f"[DEBUG] Current state: {user.current_state}")
                if not handle_waiting_state(gui_manager, user):
                    print("[DEBUG] Returning to LOBBY_STATE from WAITING_STATE.")
                    user.current_state = LOBBY_STATE  # Retour au lobby après l'attente

            else:
                print(f"[ERROR]: Unknown state: {user.current_state}. Exiting...")
                return  # Sort du programme
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR]: Exception in states_loop: {e}")
            return

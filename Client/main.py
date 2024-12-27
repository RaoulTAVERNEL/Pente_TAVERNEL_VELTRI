from user import *
from states import *

def main():
    client_socket = ClientSocket()
    user = User(client_socket)
    gui_manager = GUIManager()

    try:
        client_socket.connect()
        states_loop(user, gui_manager)
    except Exception as e:
        print(f"[ERROR]: An error occurred: {e}")
    finally:
        client_socket.close()
        pygame.quit()

if __name__ == "__main__":
    main()

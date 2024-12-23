from network import ClientSocket
from states import StateManager
from gui import GUIManager
from constants import SERVER_HOST, SERVER_PORT, BUFFER_SIZE

def main():
    """
    Main entry point of the client application.
    Initializes the network socket, state manager, and GUI manager.
    """
    client_socket = ClientSocket(SERVER_HOST, SERVER_PORT, BUFFER_SIZE)
    state_manager = StateManager(client_socket)
    gui_manager = GUIManager(state_manager)

    try:
        client_socket.connect()
        gui_manager.run()
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()

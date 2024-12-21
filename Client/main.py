from network import ClientSocket
from states import StateManager
from gui import GUIManager
from constants import SERVER_HOST, SERVER_PORT, BUFFER_SIZE

def main():
    client_socket = ClientSocket(SERVER_HOST, SERVER_PORT, BUFFER_SIZE)
    state_manager = StateManager(client_socket)
    gui_manager = GUIManager(state_manager)

    client_socket.connect()
    gui_manager.run()

if __name__ == "__main__":
    main()
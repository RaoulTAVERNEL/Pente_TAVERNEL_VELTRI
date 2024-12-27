# ****************************************
#              CONFIGURATION             *
# ****************************************

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 55555
BUFFER_SIZE = 4096
AUTH_MAX_LENGTH = 16

# ****************************************
#                 STATES                 *
# ****************************************

INITIAL_STATE = 1
LOBBY_STATE = 2
INACTIVE_GAME_STATE = 3
PLAYING_STATE = 4
WAITING_STATE = 5

# ****************************************
#                 PACKETS                *
# ****************************************

PKT_CONNECT = 10
PKT_LIST_GAME = 21
PKT_DISCONNECT = 22
PKT_CREATE_GAME = 23
PKT_JOIN = 24
PKT_QUIT = 30
PKT_CHECK_GAME = 31
PKT_MOVE = 40
PKT_ABANDON = 50

# ****************************************
#                 STATUS                 *
# ****************************************

STATUS_SUCCESS = 0
STATUS_FAILED = 1

STATUS_AUTH_SUCCESS = 10
STATUS_AUTH_FAILED = 11

STATUS_LOGOUT_SUCCESS = 22
STATUS_NEW_GAME_SUCCESS = 23
STATUS_NEW_GAME_FAILED = 25
STATUS_LIST_GAMES = 26
STATUS_NO_GAME = 27

STATUS_QUIT_GAME = 30
STATUS_CHECK_GAME_NOBODY = 31
STATUS_CHECK_GAME_JOINED = 32

STATUS_MAKE_MOVE = 40
STATUS_INVALID_MOVE = 41
STATUS_WAIT_MOVE = 42
STATUS_VICTORY = 43
STATUS_LOST = 44
STATUS_BOARD_UPDATE = 45
STATUS_ABANDON_GAME = 46

STATUS_INTERNAL_ERROR = 100

# ****************************************
#                    GUI                 *
# ****************************************

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
BOARD_SIZE = 19
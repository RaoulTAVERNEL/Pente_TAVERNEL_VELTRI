#ifndef CONFIG_H
#define CONFIG_H
#include <signal.h>

/*********************************************/
/*              CONFIGURATION                */
/*********************************************/

#define PORT 55555
#define MAX_CLIENTS 10
#define BUFFER_SIZE 4096
#define AUTH_MAX_LENGTH 16
#define MAX_GAMES 5
#define BOARD_SIZE 19

/*********************************************/
/*                  STATES                   */
/*********************************************/

#define INITIAL_STATE 1
#define LOBBY_STATE 2
#define INACTIVE_GAME_STATE 3
#define PLAYING_STATE 4
#define WAITING_STATE 5

/*********************************************/
/*                  PACKETS                  */
/*********************************************/

#define PKT_CONNECT 10
#define PKT_LIST_GAME 21
#define PKT_DISCONNECT 22
#define PKT_CREATE_GAME 23
#define PKT_JOIN 24
#define PKT_QUIT 30
#define PKT_CHECK_GAME 31
#define PKT_MOVE 40
#define PKT_ABANDON 50

/*********************************************/
/*                  STATUS                   */
/*********************************************/

#define STATUS_SUCCESS 0
#define STATUS_FAILED 1

#define STATUS_AUTH_SUCCESS 10
#define STATUS_AUTH_FAILED 11

#define STATUS_LOGOUT_SUCCESS 22
#define STATUS_NEW_GAME_SUCCESS 23
#define STATUS_NEW_GAME_FAILED 25
#define STATUS_LIST_GAMES 26
#define STATUS_NO_GAME 27

#define STATUS_QUIT_GAME 30
#define STATUS_CHECK_GAME_NOBODY 31
#define STATUS_CHECK_GAME_JOINED 32

#define STATUS_MAKE_MOVE 40
#define STATUS_INVALID_MOVE 41
#define STATUS_WAIT_MOVE 42
#define STATUS_VICTORY 43
#define STATUS_LOST 44
#define STATUS_BOARD_UPDATE 45
#define STATUS_ABANDON_GAME 46

#define STATUS_INTERNAL_ERROR 100

/*********************************************/
/*              STRUCTURE CLIENT             */
/*********************************************/

typedef struct client {
    int fd; // Client socket descriptor
    int state; // Current state of the client
    char username[AUTH_MAX_LENGTH];
    char password[AUTH_MAX_LENGTH];
    int victories;
    int defeats;
    int games_played;
    int score;
    struct game *current_game; // Pointer to the current game
} client_t;

/*********************************************/
/*               STRUCTURE GAME              */
/*********************************************/

typedef struct game {
    int id;
    client_t *player1; // Pointer to player 1
    client_t *player2; // Pointer to player 2
    int status; // 1: Waiting for 2nd player, 2: Game ongoing
    int board[BOARD_SIZE][BOARD_SIZE];
    int turn; // Designates the player to play
} game_t;

/*********************************************/
/*              VARIABLES GLOBALES           */
/*********************************************/

extern volatile sig_atomic_t server_running;
extern int srand_flag;
extern game_t games[MAX_GAMES];
extern int game_counter;

#endif // CONFIG_H
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <signal.h>
#include <fcntl.h>
#include <stdlib.h>
#include <time.h>

#define PORT 55555
#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024
#define AUTH_MAX_LENGTH 16
#define MAX_GAMES 5
volatile sig_atomic_t server_running = 1; // Server running state variable

/*********************************************/
/*                  STATES                   */
/*********************************************/

#define INITIAL_STATE 1 // Client is disconnected
#define CONNECTED_STATE 2 // Client is authenticated
#define LOBBY_STATE 3 // Client has created a game and is waiting for 2nd player
#define ACTIVE_GAME_STATE 4 // Client is in a running game

/*********************************************/
/*                  PACKETS                  */
/*********************************************/

// PKT starts with the same number as its corresponding state
#define PKT_CONNECT 10
#define PKT_LIST_GAME 21
#define PKT_DISCONNECT 22
#define PKT_CREATE_GAME 23
#define PKT_QUIT 31
#define PKT_ABANDON 40
#define PKT_GAME_OVER 41
#define PKT_JOIN 42



/*********************************************/
/*              STRUCTURE CLIENT             */
/*********************************************/

typedef struct {
    int fd; // Client socket descriptor
    int state; // Current state of the client
    char username[AUTH_MAX_LENGTH];
    char password[AUTH_MAX_LENGTH];
    int victories;
    int defeats;
    int games_played;
    int score;
} client_t;



/*********************************************/
/*               STRUCTURE GAME              */
/*********************************************/

typedef struct {
    int id;
    client_t *player1; // Pointer to player 1
    client_t *player2; // Pointer to player 2
    int status; // 0: Waiting for 2nd player, 1: Game ongoing, 2: Game ended
} game_t;

game_t games[MAX_GAMES]; // List of all games (active and inactive)
int game_counter = 0; // Counter to track game IDs



/*********************************************/
/*            FUNCTION PROTOTYPES            */
/*********************************************/

void handle_signal(int signal); // Signal handler function
void set_non_blocking(int socket); // Set a socket to non-blocking mode
void closeconnection(client_t *client, fd_set *read_fds, int *active_client_count); // Close connection with client
void sendpacket(const client_t *client, unsigned char status, const char *message); // Send packet to client
void print_buffer(const char *buffer, size_t length); // FONCTION DEBUG A SUPPRIMER APRES LES TESTS
void authenticate(client_t *client, const char *buffer); // Authenticate client
void list_games(const client_t *client); // List all games (active and inactive)
void create_game(client_t *client); // Create a new game
void join_game(client_t *client, int game_id); // Join a game
void update_player_stats(client_t *winner, client_t *loser); // Update players stats after game ended
void determine_winner(int game_id); // Manage combat phase between players (randomize right now)
void delete_game(int game_id); // Delete an inactive game the player just made (quitting lobby)
int find_game_id_by_client(const client_t *client); // Get game ID by client
void process_cmd(client_t *client, const char *buffer, fd_set *read_fds, int *active_client_count); // Process commands using a switch structure



/*********************************************/
/*               MAIN FUNCTION               */
/*********************************************/

int main() {
    srand(time(NULL));

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    client_t clients[MAX_CLIENTS] = {0};
    int active_client_count = 0;

    signal(SIGINT, handle_signal);

    if (server_fd == -1) {
        perror("ERROR on socket creation");
        return 1;
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("ERROR on binding");
        close(server_fd);
        return 1;
    }

    if (listen(server_fd, MAX_CLIENTS) == -1) {
        perror("ERROR on listen");
        close(server_fd);
        return 1;
    }

    printf("Server listening on port %d...\n", PORT);
    set_non_blocking(server_fd);

    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(server_fd, &read_fds);

    int max_fd = server_fd;

    while (server_running) {
        fd_set temp_fds = read_fds; // Create a copy of the file descriptor set
        if (select(max_fd + 1, &temp_fds, NULL, NULL, NULL) < 0) {
            perror("ERROR on select");
            continue;
        }

        // Check for new connections
        if (FD_ISSET(server_fd, &temp_fds)) {
            int new_client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
            if (new_client_fd >= 0) {
                printf("New client connected (fd: %d).\n", new_client_fd);
                set_non_blocking(new_client_fd);

                // Find an empty slot for the new client
                int client_assigned = 0;
                for (int i = 0; i < MAX_CLIENTS; i++) {
                    if (clients[i].fd == 0) {
                        clients[i].fd = new_client_fd;
                        clients[i].state = INITIAL_STATE;
                        FD_SET(new_client_fd, &read_fds);
                        if (new_client_fd > max_fd) {
                            max_fd = new_client_fd;
                        }
                        active_client_count++;
                        printf("Active clients: %d\n", active_client_count);
                        client_assigned = 1;
                        break;
                    }
                }

                if (!client_assigned) { // If no slot is available, close the connection
                    printf("Server is full. Rejecting client (fd: %d).\n", new_client_fd);
                    close(new_client_fd);
                }
            } else {
                perror("ERROR on accept");
            }
        }

        // Check for data from clients
        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (clients[i].fd != 0 && FD_ISSET(clients[i].fd, &temp_fds)) {
                char buffer[BUFFER_SIZE] = {0}; // Initialize buffer to 0
                ssize_t bytes_read = read(clients[i].fd, buffer, sizeof(buffer) - 1); // -1 to ensure null-termination

                if (bytes_read > 0) { // Read from client successful
                    buffer[bytes_read] = '\0'; // Null-terminate the buffer for safety
                    printf("Received data from client (fd: %d).\n", clients[i].fd);
                    process_cmd(&clients[i], buffer, &read_fds, &active_client_count);
                } else if (bytes_read == 0) { // Client disconnected
                    printf("Client (fd: %d) disconnected.\n", clients[i].fd);
                    closeconnection(&clients[i], &read_fds, &active_client_count);
                } else {
                    perror("ERROR reading from client");
                    closeconnection(&clients[i], &read_fds, &active_client_count);
                }
            }
        }
    }

    // Clean up and close server
    printf("Shutting down server...\n");
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].fd != 0) {
            close(clients[i].fd);
        }
    }
    close(server_fd);

    return 0;
}



/*********************************************/
/*                 FUNCTIONS                 */
/*********************************************/

/* SIGNAL HANDLER FUNCTION */

void handle_signal(int signal) {
    if (signal == SIGINT) {
        printf("Caught signal %d, server shutting down...\n", signal);
        server_running = 0;
    }
}



/* FUNCTION TO SET A SOCKET TO NON-BLOCKING MODE */

void set_non_blocking(int socket) {
    int flags = fcntl(socket, F_GETFL, 0);
    if (flags == -1) {
        perror("ERROR on fcntl F_GETFL");
        exit(EXIT_FAILURE);
    }
    if (fcntl(socket, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("ERROR on fcntl F_SETFL");
        exit(EXIT_FAILURE);
    }
}



/* FUNCTION TO CLOSE A CLIENT CONNECTION */

void closeconnection(client_t *client, fd_set *read_fds, int *active_client_count) {
    printf("Closing connection with client (fd: %d).\n", client->fd);
    close(client->fd);
    FD_CLR(client->fd, read_fds);

    (*active_client_count)--;
    printf("Active clients after disconnection: %d\n", *active_client_count);

    client->fd = 0;
    client->state = INITIAL_STATE;
}



/* FUNCTION TO SEND A PACKET TO A CLIENT */

void sendpacket(const client_t *client, unsigned char status, const char *message) {
    char packed_response[BUFFER_SIZE]; // Set response packet with buffer size (1024)
    int length = snprintf(packed_response, sizeof(packed_response), "%s\n", message);

    if (length < 0) {
        perror("ERROR formatting packet");
        return;
    }

    unsigned char message_length = strlen(message);
    unsigned char response[BUFFER_SIZE];
    response[0] = status; // First byte reserved for status
    response[1] = message_length; // Second byte for packet length

    memcpy(response + 2, message, message_length); // Offset to +2 to copy the message
    ssize_t bytes_sent = write(client->fd, response, message_length + 2); // Send packet to client

    if (bytes_sent == -1) {
        perror("ERROR sending packet");
    } else {
        printf("Sent packet: Status: %d, Length: %d, Message: %s\n", status, message_length, message);
    }
}



/* PRINT BUFFER (A SUPPRIMER APRES LES DEBUGS) */

void print_buffer(const char *buffer, size_t length) {
    printf("Buffer content: ");
    for (size_t i = 0; i < length; i++) {
        printf("%02x ", (unsigned char)buffer[i]); // Affichage en hexadécimal
    }
    printf("\n");
}



/* FUNCTION TO AUTHENTICATE */

void authenticate(client_t *client, const char *buffer) {
    unsigned char username_length = buffer[0];  // Input username length
    char username[AUTH_MAX_LENGTH + 1] = {0};  // Init buffer for username
    unsigned char password_length_index = 1 + AUTH_MAX_LENGTH; // Index for password length
    unsigned char password_length = buffer[password_length_index];  // Password length
    char password[AUTH_MAX_LENGTH + 1] = {0};  // Init buffer for password

    memcpy(username, buffer + 1, username_length); // Copy input username in username variable to get correct format
    username[username_length] = '\0';  // Add nullbyte at the end of username to respect C format

    memcpy(password, buffer + 1 + AUTH_MAX_LENGTH + 1, password_length);  // Adjust offset for password chain
    password[password_length] = '\0';  // Add nullbyte at the end of password

    //TEMPORARY CODE FOR TESTING
    if (strcmp(password, "ok") == 0 || strcmp(password, "new") == 0) { // Authentication successful
        strcpy(client->username, username);  // Copy username in client structure
        strcpy(client->password, password); // Copy password in client structure
        client->victories = 0;  // Set victories to 0 for new player
        client->defeats = 0; // Set defeats to 0 for new player
        client->games_played = 0; // Set games played to 0 for new player
        client->score = 1000; // Set score to 1000 for new player
        client->state = CONNECTED_STATE;  // Change client state to CONNECTED_STATE
        sendpacket(client, 0, "Connection successful");  // Send successful authentication packet to client
    } else {
        sendpacket(client, 1, "Connection failed");  // Send failed authentication packet to client
    }
}



/* FUNCTION TO LIST GAMES */

void list_games(const client_t *client) {
    if (game_counter == 0) {
        sendpacket(client, 1, "No game available");
    } else {
        char list[BUFFER_SIZE] = "Available games:\n";
        int available_games = 0;

        for (int i = 0; i < game_counter; i++) { // List all game (active and inactive)
            if (games[i].status == 0) { // If game[i] is inactive (meaning another player can join the game)
                char game_info[BUFFER_SIZE];
                snprintf(game_info, sizeof(game_info), "Game %d: %s (waiting)\n", games[i].id, games[i].player1->username);
                strcat(list, game_info);
                available_games++;
            }
        }

        if (available_games == 0) { // If there's no inactive game at the moment
            sendpacket(client, 1, "No game available");
        } else {
            sendpacket(client, 0, list); // Send list games packet to client
        }
    }
}



/* FUNCTION TO CREATE A NEW GAME */

void create_game(client_t *client) {
    if (game_counter < MAX_GAMES) {
        games[game_counter].id = game_counter + 1; // Set ID game
        games[game_counter].player1 = client; // Set the maker of the game to player 1
        games[game_counter].player2 = NULL; // Second player is set to null
        games[game_counter].status = 0; // Waiting 2nd player
        game_counter++;
        client->state = LOBBY_STATE;
        sendpacket(client, 0, "New game created. Waiting for another player to start the game...");
    } else {
        sendpacket(client, 1, "Game creation failed: Lobby full");
    }
}



/* FUNCTION TO JOIN A GAME */

void join_game(client_t *client, int game_id) {
    if (game_id > 0 && game_id <= game_counter && games[game_id - 1].status == 0) {
        client_t *player1 = games[game_id - 1].player1;

        if (games[game_id - 1].player1 == NULL) { // Check if game has a valid player 1 (creator)
            sendpacket(client, 1, "Game join failed: Player 1 is not valid");
            return;
        }

        if (games[game_id - 1].player2 != NULL) { // Check if game has already 2 players
            sendpacket(client, 1, "Game join failed: Game is already full");
            return;
        }

        games[game_id - 1].player2 = client; // Player 2 was null and now is the player who joined the game
        games[game_id - 1].status = 1; // Game is now active

        games[game_id - 1].player1->state = ACTIVE_GAME_STATE;
        games[game_id - 1].player2->state = ACTIVE_GAME_STATE;

        char response[BUFFER_SIZE];
        snprintf(response, sizeof(response), "Joined game %d against %s", game_id, player1->username);
        sendpacket(client, 0, response);

        snprintf(response, sizeof(response), "%s has joined the game!", client->username);
        sendpacket(player1, 3, response);
    }
}



/* FUNCTION TO DELETE A GAME */

void delete_game(int game_id) {
    int index = game_id - 1;

    if (index < 0 || index >= game_counter) {
        printf("Invalid game ID.\n");
        return;
    }

    for (int i = index; i < game_counter - 1; i++) {
        games[i] = games[i + 1];
    }

    game_counter--;

    printf("Game ID %d has been deleted.\n", game_id);
}



/* FUNCTION TO UPDATE PLAYERS STATS */

void update_player_stats(client_t *winner, client_t *loser) {
    winner->victories += 1;
    winner->score += 10;
    loser->defeats += 1;
    loser->score -= 10;
}



/* FUNCTION TO DETERMINE WINNER (will be replaced with actual Pente game rules later) */

void determine_winner(int game_id) {
    char win_message[BUFFER_SIZE];
    char lose_message[BUFFER_SIZE];

    // RANDOMIZE WINNER BLOCK WILL BE DELETED IN THE FOLLOWING PROJECT
    static int initialized = 0;
    if (!initialized) {
        srand(time(NULL));
        initialized = 1;
    }

    int winner = rand() % 2; // 0 or 1

    client_t *player1 = games[game_id - 1].player1;
    client_t *player2 = games[game_id - 1].player2;

    if (winner == 0) { // Player 1 wins
        update_player_stats(player1, player2);

        // Send message to player 1 (winner)
        snprintf(win_message, sizeof(win_message),
                 "CONGRATZ U WON, %s! Your stats - Victories: %d, Defeats: %d, Score: %d.",
                 player1->username, player1->victories, player1->defeats, player1->score);
        sendpacket(player1, 0, win_message);

        // Send message to player 2 (loser)
        snprintf(lose_message, sizeof(lose_message),
                 "OH NO YOU LOST, %s! Your stats - Victories: %d, Defeats: %d, Score: %d.",
                 player2->username, player2->victories, player2->defeats, player2->score);
        sendpacket(player2, 1, lose_message);
    } else { // Player 2 wins
        update_player_stats(player2, player1);

        // Send message to player 2 (winner)
        snprintf(win_message, sizeof(win_message),
                 "CONGRATZ U WON, %s! Your stats - Victories: %d, Defeats: %d, Score: %d.",
                 player2->username, player2->victories, player2->defeats, player2->score);
        sendpacket(player2, 0, win_message);

        // Send message to player 1 (loser)
        snprintf(lose_message, sizeof(lose_message),
                 "OH NO YOU LOST, %s! Your stats - Victories: %d, Defeats: %d, Score: %d.",
                 player1->username, player1->victories, player1->defeats, player1->score);
        sendpacket(player1, 1, lose_message);
    }

    player2->state = CONNECTED_STATE;
    player1->state = CONNECTED_STATE;

    delete_game(game_id);
}



/* FUNCTION TO FIND ID GAME BY CLIENT */

int find_game_id_by_client(const client_t *client) {
    for (int i = 0; i < game_counter; i++) {
        if (games[i].player1 == client || games[i].player2 == client) {
            return games[i].id;  // Return the game ID if the client is in this game
        }
    }
    return -1; // Return -1 if the client is not in any game
}



/* FUNCTION TO PROCESS COMMANDS */

void process_cmd(client_t *client, const char *buffer, fd_set *read_fds, int *active_client_count) {
    switch (client->state) {
        case INITIAL_STATE:
            printf("Client is in INITIAL_STATE. Received buffer: %02x\n", buffer[0]);
            if (buffer[0] == PKT_CONNECT) { // Client sends credentials
                printf("Packet type is PKT_CONNECT. Authenticating...\n");
                authenticate(client, buffer + 1);

            } else {
                printf("Unknown packet type in INITIAL_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }
            break;

        case CONNECTED_STATE:
            printf("Client is in CONNECTED_STATE. Received buffer: %02x\n", buffer[0]);
            if (buffer[0] == PKT_LIST_GAME) { // List all games
                printf("Packet type is PKT_LIST_GAME. Listing games...\n");
                list_games(client);
            } else if (buffer[0] == PKT_CREATE_GAME) { // Client creates a new game
                printf("Packet type is PKT_CREATE_GAME. Creating game...\n");
                create_game(client);
            } else if (buffer[0] == PKT_JOIN) { // Client joins an inactive game
                int game_id;
                // Get ID from buffer
                memcpy(&game_id, buffer + 1, sizeof(int));
                game_id = (int) ntohl(game_id);  // Convert endianness

                if (game_id > 0 && game_id <= game_counter) {
                    printf("Packet type is PKT_JOIN. Joining game with ID: %d\n", game_id);
                    join_game(client, game_id);
                } else {
                    printf("Error: Invalid game ID.\n");
                    sendpacket(client, 1, "Game join failed: Invalid game ID");
                }
            } else {
                printf("Unknown packet type in INITIAL_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }

        break;

        case LOBBY_STATE:
            printf("Client is in LOBBY_STATE. Received buffer: %02x\n", buffer[0]);

            if (buffer[0] == PKT_QUIT) {  // Client quits lobby
                int game_id = find_game_id_by_client(client);
                printf("Packet type is PKT_QUIT. Client is exiting the lobby...\n");
                delete_game(game_id);
                sendpacket(client, 0, "Exited the lobby successfully.");
                client->state = CONNECTED_STATE;
                list_games(client);

            } else {
                printf("Unknown packet type in LOBBY_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }
            break;

        case ACTIVE_GAME_STATE:
            printf("Client is in ACTIVE_GAME_STATE.");

            if(buffer[0] == PKT_GAME_OVER) {
                int game_id = find_game_id_by_client(client);
                if (game_id != -1 && games[game_id - 1].status == 1) {
                    printf("Game is active. Determining the winner...\n");
                    determine_winner(game_id);
                }
            }
            break;

        default:
            printf("Unknown state for client (fd: %d): %d\n", client->fd, client->state);
            closeconnection(client, read_fds, active_client_count);
            break;
    }
}
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
#define USERNAME_MAX_LENGTH 16
#define PASSWORD_MAX_LENGTH 16
#define MAX_GAMES 5

/* STATES */
#define INITIAL_STATE 1
#define CONNECTED_STATE 2
#define LOBBY_STATE 3
#define ACTIVE_GAME_STATE 4

/* PACKETS */
#define PKT_CONNECT 10
#define PKT_LIST_GAME 21
#define PKT_DISCONNECT 22
#define PKT_CREATE_GAME 23
#define PKT_QUIT 31
#define PKT_ABANDON 40
#define PKT_GAME_OVER 41
#define PKT_JOIN 42

volatile sig_atomic_t server_running = 1; // Server running state variable

/* STRUCTURE CLIENT */
typedef struct {
    int fd; // Client socket descriptor
    int state; // Current state of the client
    char username[USERNAME_MAX_LENGTH];
    int victories;
    int defeats;
    int games_played;
    int score;
} client_t;

/* STRUCTURE GAME */
typedef struct {
    int id;
    char player1[USERNAME_MAX_LENGTH];
    char player2[USERNAME_MAX_LENGTH];
    int status; // 0: Waiting for 2nd player, 1: Game ongoing
} game_t;

game_t games[MAX_GAMES]; // List of games
int game_counter = 0; // Counter to track game IDs

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
void closeconnection(client_t *client, fd_set *read_fds) {
    printf("Closing connection with client (fd: %d).\n", client->fd);
    close(client->fd);
    FD_CLR(client->fd, read_fds);
    client->fd = 0;
    client->state = INITIAL_STATE;
}

/* FUNCTION TO SEND A PACKET TO A CLIENT */
void sendpacket(client_t *client, const char *message) {
    unsigned char status = (strcmp(message, "Connection successful") == 0) ? 0 : 1;
    char packed_response[BUFFER_SIZE];
    int length = snprintf(packed_response, sizeof(packed_response), "%s\n", message);

    if (length < 0) {
        perror("ERROR formatting packet");
        return;
    }

    unsigned char message_length = strlen(message);
    char response[BUFFER_SIZE];
    response[0] = status;
    response[1] = message_length;
    memcpy(response + 2, message, message_length);

    ssize_t bytes_sent = write(client->fd, response, message_length + 2);
    if (bytes_sent == -1) {
        perror("ERROR sending packet");
    } else {
        printf("Sent packet: Status: %d, Length: %d, Message: %s\n", status, message_length, message);
    }
}
void print_buffer(const char *buffer, size_t length) {
    printf("Buffer content: ");
    for (size_t i = 0; i < length; i++) {
        printf("%02x ", (unsigned char)buffer[i]); // Affichage en hexadécimal
    }
    printf("\n");
}


void authenticate(client_t *client, char *buffer) {
    print_buffer(buffer, BUFFER_SIZE);

    unsigned char username_length = buffer[0];  // Longueur du nom d'utilisateur
    printf("Username length: %d\n", username_length);  // Affichage de la longueur du nom d'utilisateur

    char username[USERNAME_MAX_LENGTH + 1] = {0};  // Initialiser le tampon pour le nom d'utilisateur

    // Calculer l'index de la longueur du mot de passe
    unsigned char password_length_index = 1 + USERNAME_MAX_LENGTH; // Index pour la longueur du mot de passe
    unsigned char password_length = buffer[password_length_index];  // Longueur du mot de passe
    printf("Password length: %d\n", password_length);  // Affichage de la longueur du mot de passe

    char password[PASSWORD_MAX_LENGTH + 1] = {0};  // Initialiser le tampon pour le mot de passe

    // Copier correctement le nom d'utilisateur
    memcpy(username, buffer + 1, username_length);
    username[username_length] = '\0';  // Ajouter un caractère null à la fin du nom d'utilisateur
    printf("Copied username: '%s'\n", username);  // Affichage du nom d'utilisateur copié

    // Copier correctement le mot de passe
    memcpy(password, buffer + 1 + USERNAME_MAX_LENGTH + 1, password_length);  // Ajuster le décalage
    password[password_length] = '\0';  // Ajouter un caractère null à la fin du mot de passe
    printf("Copied password: '%s'\n", password);  // Affichage du mot de passe copié

    printf("Final username: '%s' with length %d\n", username, username_length);
    printf("Final password: '%s' with length %d\n", password, password_length);

    // Logique d'authentification
    if (strcmp(password, "ok") == 0 || strcmp(password, "new") == 0) {
        strcpy(client->username, username);  // Copier le nom d'utilisateur dans la structure client
        client->victories = 1;  // Valeurs d'exemple
        client->defeats = 2;
        client->games_played = 3;
        client->score = 1000;
        client->state = LOBBY_STATE;  // Changer l'état en LOBBY_STATE
        sendpacket(client, "Connection successful");  // Envoyer un message de succès
        printf("Authentication successful for user: '%s'\n", username);  // Affichage de débogage
    } else {
        sendpacket(client, "Connection failed");  // Envoyer un message d'échec
        printf("Authentication failed for user: '%s'. Invalid password: '%s'\n", username, password);  // Affichage de débogage
    }
}






/* FUNCTION TO LIST GAMES */
void list_games(client_t *client) {
    char list[BUFFER_SIZE] = "Available games:\n";
    for (int i = 0; i < game_counter; i++) {
        if (games[i].status == 0) {
            char game_info[100];
            snprintf(game_info, sizeof(game_info), "Game %d: %s (waiting)\n", games[i].id, games[i].player1);
            strcat(list, game_info);
        }
    }
    sendpacket(client, list);
}

/* FUNCTION TO CREATE A NEW GAME */
void create_game(client_t *client) {
    if (game_counter < MAX_GAMES) {
        games[game_counter].id = game_counter + 1;
        strcpy(games[game_counter].player1, client->username);
        games[game_counter].status = 0; // Waiting for second player
        game_counter++;
        sendpacket(client, "New game created");
    } else {
        sendpacket(client, "Game creation failed: Lobby full");
    }
}

/* FUNCTION TO JOIN A GAME */
void join_game(client_t *client, int game_id) {
    if (game_id > 0 && game_id <= game_counter && games[game_id - 1].status == 0) {
        strcpy(games[game_id - 1].player2, client->username);
        games[game_id - 1].status = 1;
        client->state = ACTIVE_GAME_STATE;

        char response[100];
        snprintf(response, sizeof(response), "Joined game %d against %s", game_id, games[game_id - 1].player1);
        sendpacket(client, response);

        // Simulate game end
        int winner = rand() % 2; // Random winner
        if (winner == 0) {
            sendpacket(client, "You won!");
        } else {
            sendpacket(client, "You lost!");
        }

        games[game_id - 1].status = 2; // Game finished
    } else {
        sendpacket(client, "Game join failed: Invalid game ID");
    }
}

/* FUNCTION TO PROCESS COMMANDS */
void process_cmd(client_t *client, char *buffer) {
    printf("Processing command for client (fd: %d), current state: %d\n", client->fd, client->state);

    switch (client->state) {
        case INITIAL_STATE:
            printf("Client is in INITIAL_STATE. Received buffer: %02x\n", buffer[0]);  // Print the first byte of the buffer
        if (buffer[0] == PKT_CONNECT) {
            printf("Packet type is PKT_CONNECT. Authenticating...\n");
            authenticate(client, buffer + 1);
        } else {
            printf("Unknown packet type in INITIAL_STATE: %02x\n", buffer[0]);
        }
        break;
        case LOBBY_STATE:
            printf("Client is in LOBBY_STATE. Received buffer: %02x\n", buffer[0]);  // Print the first byte of the buffer
        if (buffer[0] == PKT_LIST_GAME) {
            printf("Packet type is PKT_LIST_GAME. Listing games...\n");
            list_games(client);
        } else if (buffer[0] == PKT_CREATE_GAME) {
            printf("Packet type is PKT_CREATE_GAME. Creating game...\n");
            create_game(client);
        } else if (buffer[0] == PKT_JOIN) {
            int game_id = atoi(buffer + 1);
            printf("Packet type is PKT_JOIN. Joining game with ID: %d\n", game_id);
            join_game(client, game_id);
        } else {
            printf("Unknown packet type in LOBBY_STATE: %02x\n", buffer[0]);
        }
        break;
        case ACTIVE_GAME_STATE:
            printf("Client is in ACTIVE_GAME_STATE. Further command handling can be added here.\n");
        // You can add handling for the in-game commands here.
        break;
        default:
            printf("Unknown state for client (fd: %d): %d\n", client->fd, client->state);
        break;
    }
}


/* MAIN FUNCTION */
int main() {
    srand(time(NULL));

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    client_t clients[MAX_CLIENTS] = {0};

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
                for (int i = 0; i < MAX_CLIENTS; i++) {
                    if (clients[i].fd == 0) {
                        clients[i].fd = new_client_fd;
                        clients[i].state = INITIAL_STATE;
                        FD_SET(new_client_fd, &read_fds);
                        if (new_client_fd > max_fd) {
                            max_fd = new_client_fd;
                        }
                        break;
                    }
                }
            } else {
                perror("ERROR on accept");
            }
        }

        // Check for data from clients
        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (clients[i].fd != 0 && FD_ISSET(clients[i].fd, &temp_fds)) {
                char buffer[BUFFER_SIZE];
                ssize_t bytes_read = read(clients[i].fd, buffer, sizeof(buffer));

                if (bytes_read > 0) {
                    printf("Received data from client (fd: %d).\n", clients[i].fd);
                    process_cmd(&clients[i], buffer);
                } else if (bytes_read == 0) {
                    // Client disconnected
                    closeconnection(&clients[i], &read_fds);
                } else {
                    perror("ERROR reading from client");
                    closeconnection(&clients[i], &read_fds);
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


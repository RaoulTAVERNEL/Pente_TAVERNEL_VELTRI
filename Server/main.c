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

#define PORT 55555 // Communication port
#define MAX_CLIENTS 10 // Maximum number of simultaneous clients
#define BUFFER_SIZE 1024 // Buffer size for chunked message handling
#define USERNAME_MAX_LENGTH 32// Maximum length for username

/* STATES */
#define INITIAL_STATE 0
#define CONNECTED_STATE 1

/* PACKETS */
#define PKT_CONNECT 1

volatile sig_atomic_t server_running = 1; // Server running state variable

/* CLIENT STRUCTURE */
typedef struct {
    int fd; // Client socket descriptor
    int state; // Current state of the client
    char recv_buffer[BUFFER_SIZE]; // Buffer to store received data
    char send_buffer[BUFFER_SIZE]; // Buffer to store outgoing data
} client_t;

/* SIGNAL HANDLER FUNCTION */
void handle_signal(int signal) {
    if (signal == SIGINT) {
        printf("Caught signal %d, server shutting down...\n", signal);
        server_running = 0; // Stop the loop
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
    close(client->fd); // Close the socket
    FD_CLR(client->fd, read_fds); // Remove from the read_fds set
    client->fd = 0; // Reset the client's fd to indicate it's no longer in use
    client->state = INITIAL_STATE; // Reset the state
}

/* FUNCTION TO SEND A PACKET TO A CLIENT */
void sendpacket(client_t *client, const char *message) {
    unsigned char status = (strcmp(message, "Connection successful") == 0) ? 0 : 1;
    char response[BUFFER_SIZE];
    int length = snprintf(response, sizeof(response), "%s\n", message); // Remove status from snprintf

    if (length < 0) {
        perror("ERROR formatting packet");
        return;
    }
    // Debugging prints


    // Pack the response with status and message length
    unsigned char message_length = strlen(message);
    char packed_response[BUFFER_SIZE];
    packed_response[0] = status; // Set status byte
    packed_response[1] = message_length; // Set message length
    memcpy(packed_response + 2, message, message_length); // Copy message to the packed response

    ssize_t bytes_sent = write(client->fd, packed_response, message_length + 2); // Send length + status + message
    if (bytes_sent == -1) {
        perror("ERROR sending packet");
    } else {
        printf("Sent packet: Status: %d, Length: %d, Message: %s\n", status, message_length, message);
    }
}





/* FUNCTION TO PROCESS COMMANDS FROM CLIENTS */
void processcmd(int client_fd, client_t *client, char *buffer) {
    unsigned char username_length = buffer[0]; // First byte: username length
    char username[USERNAME_MAX_LENGTH + 1] = {0}; // +1 for null terminator
    unsigned char password_length = buffer[1 + username_length]; // Next byte: password length
    char password[USERNAME_MAX_LENGTH + 1] = {0}; // +1 for null terminator

    // Copy username from buffer
    memcpy(&username_length, buffer, sizeof(username_length));

    memcpy(username, buffer + 1, username_length);
    username[username_length] = '\0'; // Terminer la chaîne

    memcpy(&password_length, buffer + 1 + USERNAME_MAX_LENGTH, sizeof(password_length));
    memcpy(password, buffer + 2 + USERNAME_MAX_LENGTH, password_length);
    password[password_length] = '\0'; // Terminer la chaîne

    printf("Received username: '%s' with length %d\n", username, username_length);
    printf("Received password: '%s' with length %d\n", password, password_length);


    // Check username and password
    if (strcmp(username, "marie") == 0 && strcmp(password, "raoul") == 0) {
        printf("Client authenticated successfully.\n");
        client->state = CONNECTED_STATE; // Transition to connected state
        sendpacket(client, "Connection successful");
    } else {
        printf("Authentication failed.\n");
        sendpacket(client, "Connection failed");
    }
}
/* MAIN SERVER FUNCTION */
int main(int argc, char *argv[]) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0); // Create the server socket
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    client_t clients[MAX_CLIENTS] = {0}; // Array to hold clients

    signal(SIGINT, handle_signal); // Attach SIGINT to the handle_signal function

    if (server_fd == -1) {
        perror("ERROR on socket creation");
        return 1;
    }

    // Set up the server address and port
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bind the socket to the address and port
    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("ERROR on binding");
        close(server_fd);
        return 1;
    }

    // Set the socket to listen mode
    if (listen(server_fd, MAX_CLIENTS) == -1) {
        perror("ERROR on listen");
        close(server_fd);
        return 1;
    }

    printf("Server listening on port %d...\n", PORT);

    // Set the server socket to non-blocking mode
    set_non_blocking(server_fd);

    fd_set read_fds, write_fds, except_fds; // File descriptor sets for select()
    FD_ZERO(&read_fds);
    FD_ZERO(&write_fds);
    FD_ZERO(&except_fds);

    FD_SET(server_fd, &read_fds); // Add the server socket to the read set

    int max_fd = server_fd; // The highest file descriptor (for select)

    char buffer[BUFFER_SIZE]; // Buffer to read client messages

    while (server_running) {
        fd_set temp_read_fds = read_fds;
        fd_set temp_write_fds = write_fds;
        fd_set temp_except_fds = except_fds;

        // Call select() to monitor active sockets
        if (select(max_fd + 1, &temp_read_fds, &temp_write_fds, &temp_except_fds, NULL) < 0) {
            if (server_running == 0) break; // Exit if the server is stopped
            perror("ERROR on select");
            continue;
        }

        // Check for new connections or incoming data
        for (int i = 0; i <= max_fd; ++i) {
            if (FD_ISSET(i, &temp_read_fds)) {
                if (i == server_fd) {
                    // New incoming connection
                    int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
                    if (client_fd == -1) {
                        perror("ERROR on accept");
                    } else {
                        printf("Connection accepted from %s:%d\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
                        set_non_blocking(client_fd); // Set the client socket to non-blocking
                        FD_SET(client_fd, &read_fds); // Add the client to the read set
                        if (client_fd > max_fd) max_fd = client_fd; // Update max_fd if necessary

                        // Initialize the client state
                        for (int j = 0; j < MAX_CLIENTS; ++j) {
                            if (clients[j].fd == 0) {
                                clients[j].fd = client_fd;
                                clients[j].state = INITIAL_STATE; // Start in the initial state
                                break;
                            }
                        }
                    }
                } else {
                    // A client sent a message
                    memset(buffer, 0, BUFFER_SIZE); // Clear the buffer
                    ssize_t bytes_read = read(i, buffer, BUFFER_SIZE - 1); // Read the client's message

                    if (bytes_read <= 0) {
                        // Si le client s'est déconnecté ou s'il y a eu une erreur
                        if (bytes_read == 0) {
                            printf("Client disconnected.\n");
                        } else {
                            perror("ERROR on read");
                        }
                        for (int j = 0; j < MAX_CLIENTS; ++j) {
                            if (clients[j].fd == i) {
                                closeconnection(&clients[j], &read_fds); // Fermer la connexion correctement
                                break;
                            }
                        }
                    } else {
                        // Process the received command
                        for (int j = 0; j < MAX_CLIENTS; ++j) {
                            if (clients[j].fd == i) {
                                printf("Raw buffer: %.*s\n", (int)bytes_read, buffer); // Afficher le contenu brut du buffer

                                processcmd(i, &clients[j], buffer);
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    // Close the server socket
    close(server_fd);
    printf("Server shut down.\n");

    return 0;
}

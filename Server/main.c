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

volatile sig_atomic_t server_running = 1; // Server running state variable

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

int main(void) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0); // Create the server socket
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

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

    fd_set active_fd_set, read_fd_set; // File descriptor sets for select()
    FD_ZERO(&active_fd_set);           // Initialize the active file descriptor set
    FD_SET(server_fd, &active_fd_set); // Add the server socket to the set

    int max_fd = server_fd; // The highest file descriptor (for select)

    char buffer[BUFFER_SIZE]; // Buffer to read client messages

    while (server_running) {
        read_fd_set = active_fd_set; // Copy the active file descriptor set

        // Call select() to monitor active sockets
        if (select(max_fd + 1, &read_fd_set, NULL, NULL, NULL) < 0) {
            if (server_running == 0) break; // Exit if the server is stopped
            perror("ERROR on select");
            continue;
        }

        // Loop through active file descriptors
        for (int i = 0; i <= max_fd; ++i) {
            if (FD_ISSET(i, &read_fd_set)) {
                if (i == server_fd) {
                    // New incoming connection
                    int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
                    if (client_fd == -1) {
                        perror("ERROR on accept");
                    } else {
                        printf("Connection accepted from %s:%d\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
                        set_non_blocking(client_fd); // Set the client socket to non-blocking
                        FD_SET(client_fd, &active_fd_set); // Add the client to the set
                        if (client_fd > max_fd) max_fd = client_fd; // Update max_fd if necessary
                    }
                } else {
                    // A client sent a message
                    int keep_reading = 1;
                    while (keep_reading) {
                        memset(buffer, 0, BUFFER_SIZE); // Clear the buffer
                        ssize_t bytes_read = read(i, buffer, BUFFER_SIZE - 1); // Read the client's message

                        if (bytes_read <= 0) {
                            // If the client disconnected or there was an error
                            if (bytes_read == 0) {
                                printf("Client disconnected.\n");
                            } else {
                                perror("ERROR on read");
                            }
                            close(i); // Close the client's connection
                            FD_CLR(i, &active_fd_set); // Remove the descriptor from the set
                            keep_reading = 0; // Stop reading if the connection is closed
                        } else {
                            // Process the received chunk of the message
                            buffer[bytes_read] = '\0'; // Null-terminate the message chunk
                            printf("Message received: %s\n", buffer); // Display the message chunk
                            ssize_t bytes_written = write(i, buffer, bytes_read); // Reply to the client with the same chunk

                            if (bytes_written < 0) {
                                perror("ERROR on write");
                                close(i);
                                FD_CLR(i, &active_fd_set);
                                keep_reading = 0;
                            }

                            // If we received less than the buffer size, it means no more data to read
                            if (bytes_read < BUFFER_SIZE - 1) {
                                keep_reading = 0; // Stop reading if no more data
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

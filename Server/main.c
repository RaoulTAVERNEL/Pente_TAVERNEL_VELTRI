#include <stdio.h>
#include <unistd.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include "headers/states.h"
#include "headers/network.h"
#include "headers/config.h"

int main() {
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

    printf("[DEBUG] Server listening on port %d...\n", PORT);
    set_non_blocking(server_fd);

    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(server_fd, &read_fds);

    int max_fd = server_fd;

    while (server_running) {
        fd_set temp_fds = read_fds;

        if (select(max_fd + 1, &temp_fds, NULL, NULL, NULL) < 0) {
            perror("ERROR on select");
            continue;
        }

        if (FD_ISSET(server_fd, &temp_fds)) {
            int new_client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);

            if (new_client_fd >= 0) {
                printf("[DEBUG] New client connected (fd: %d).\n", new_client_fd);
                set_non_blocking(new_client_fd);
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
                        printf("[DEBUG] Active clients: %d\n", active_client_count);
                        client_assigned = 1;
                        break;
                    }
                }

                if (!client_assigned) {
                    printf("[DEBUG] Server is full. Rejecting client (fd: %d).\n", new_client_fd);
                    close(new_client_fd);
                }
            } else {
                perror("ERROR on accept");
            }
        }

        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (clients[i].fd != 0 && FD_ISSET(clients[i].fd, &temp_fds)) {
                char buffer[BUFFER_SIZE] = {0};

                ssize_t bytes_read = read(clients[i].fd, buffer, sizeof(buffer) - 1);

                if (bytes_read > 0) {
                    buffer[bytes_read] = '\0';
                    printf("[DEBUG] Received data from client (fd: %d, username: %s, state: %d).\n",
                        clients[i].fd, clients[i].username, clients[i].state);
                    process_cmd(&clients[i], buffer, &read_fds, &active_client_count);
                } else if (bytes_read == 0) {
                    printf("[DEBUG] Client (fd: %d) disconnected.\n", clients[i].fd);
                    closeconnection(&clients[i], &read_fds, &active_client_count);
                } else {
                    perror("ERROR reading from client");
                    closeconnection(&clients[i], &read_fds, &active_client_count);
                }
            }
        }
    }

    printf("[DEBUG] Shutting down server...\n");
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].fd != 0) {
            close(clients[i].fd);
        }
    }
    close(server_fd);

    return 0;
}
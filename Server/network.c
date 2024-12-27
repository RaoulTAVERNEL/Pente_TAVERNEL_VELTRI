#include "headers/network.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>

void handle_signal(int signal) {
    if (signal == SIGINT) {
        printf("[DEBUG] Caught signal %d, server shutting down...\n", signal);
        server_running = 0;
    }
}

void set_non_blocking(int socket) {
    int flags = fcntl(socket, F_GETFL, 0);

    if (flags == -1) {
        perror("[ERROR] on fcntl F_GETFL");
        exit(EXIT_FAILURE);
    }

    if (fcntl(socket, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("[ERROR] on fcntl F_SETFL");
        exit(EXIT_FAILURE);
    }
}

void closeconnection(client_t *client, fd_set *read_fds, int *active_client_count) {
    printf("[DEBUG] Closing connection with client (fd: %d).\n", client->fd);
    close(client->fd);
    FD_CLR(client->fd, read_fds);
    (*active_client_count)--;
    memset(client, 0, sizeof(client_t));
    printf("[DEBUG] Active clients after disconnection: %d\n", *active_client_count);
}

void sendpacket(const client_t *client, unsigned char status, const char *message) {
    char packed_response[BUFFER_SIZE];
    int length = snprintf(packed_response, sizeof(packed_response), "%s", message);

    if (length < 0) {
        perror("[ERROR] on formatting packet");
        return;
    }

    unsigned char message_length = strlen(message);
    unsigned char response[BUFFER_SIZE];

    response[0] = status;
    response[1] = message_length;
    memcpy(response + 2, message, message_length);
    ssize_t bytes_sent = write(client->fd, response, message_length + 2);

    if (bytes_sent == -1) {
        perror("[ERROR] on sending packet");
    } else {
        printf("[DEBUG] Sent packet to client %s (fd: %d): Status: %d, Length: %d, Message: %s\n",
               client->username, client->fd, status, message_length, message);
    }
}
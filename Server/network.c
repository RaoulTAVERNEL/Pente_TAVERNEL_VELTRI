#include "headers/network.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <netinet/in.h>

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
    size_t message_length = strlen(message);

    if (message_length > BUFFER_SIZE - 6) { // Garde une marge pour l'en-tête
        fprintf(stderr, "[ERROR] Message too large to send (max %d bytes)\n", BUFFER_SIZE - 6);
        return;
    }

    unsigned char response[BUFFER_SIZE];

    // Construire l'en-tête
    response[0] = status;
    uint32_t length_network = htonl((uint32_t)message_length); // Convertir la longueur en réseau
    memcpy(response + 1, &length_network, sizeof(uint32_t));   // Copie 4 octets pour la longueur

    // Copier le message
    memcpy(response + 5, message, message_length);

    // Envoyer le paquet
    ssize_t bytes_sent = write(client->fd, response, 5 + message_length);
    if (bytes_sent == -1) {
        perror("[ERROR] on sending packet");
    } else {
        printf("[DEBUG] Sent packet to client %s (fd: %d): Status: %d, Length: %zu, Message: %s\n",
               client->username, client->fd, status, message_length, message);
    }
}

#ifndef NETWORK_H
#define NETWORK_H

#include <sys/select.h>
#include "config.h"

void handle_signal(int signal); // Signal handler function
void set_non_blocking(int socket); // Set a socket to non-blocking mode
void closeconnection(client_t *client, fd_set *read_fds, int *active_client_count); // Close connection with client
void sendpacket(const client_t *client, unsigned char status, const char *message); // Send packet to client

#endif // NETWORK_H

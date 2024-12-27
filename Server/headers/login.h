#ifndef LOGIN_H
#define LOGIN_H

#include "network.h"

void authenticate(client_t *client, const char *buffer); // Authenticate client
void logout(client_t *client); // Disconnect client

#endif // LOGIN_H

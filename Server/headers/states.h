#ifndef STATES_H
#define STATES_H

#include "config.h"
#include "network.h"

void process_cmd(client_t *client, const char *buffer, fd_set *read_fds, int *active_client_count);

#endif // STATES_H

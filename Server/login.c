#include "headers/login.h"
#include <stdio.h>
#include <string.h>

void authenticate(client_t *client, const char *buffer) {
    unsigned char username_length = buffer[0];
    char username[AUTH_MAX_LENGTH + 1] = {0};
    unsigned char password_length_index = 1 + username_length;
    unsigned char password_length = buffer[password_length_index];
    char password[AUTH_MAX_LENGTH + 1] = {0};

    memcpy(username, buffer + 1, username_length);
    username[username_length] = '\0';
    memcpy(password, buffer + password_length_index + 1, password_length);
    password[password_length] = '\0';

    printf("[DEBUG] Username received: %s, Password received: %s\n", username, password);

    if (strcmp(password, "ok") == 0 || strcmp(password, "new") == 0) {
        strcpy(client->username, username);
        strcpy(client->password, password);
        client->victories = 0;
        client->defeats = 0;
        client->games_played = 0;
        client->score = 1000;
        client->state = LOBBY_STATE;
        sendpacket(client, STATUS_AUTH_SUCCESS, "Connection successful");
    } else {
        sendpacket(client, STATUS_AUTH_FAILED, "Connection failed");
    }
}

void logout(client_t *client) {
    if (client == NULL) {
        printf("[ERROR]: Client is NULL.\n");
        return;
    }

    memset(client->username, 0, sizeof(client->username));
    memset(client->password, 0, sizeof(client->password));
    client->victories = 0;
    client->defeats = 0;
    client->games_played = 0;
    client->score = 0;
    client->current_game = NULL;
    client->state = INITIAL_STATE;
    sendpacket(client, STATUS_LOGOUT_SUCCESS, "Disconnection successful");
}

#include "headers/states.h"

#include <stdio.h>
#include <string.h>
#include <netinet/in.h>

#include "headers/game.h"
#include "headers/lobby.h"
#include "headers/login.h"

/*********************************************/
/*                 FUNCTIONS                 */
/*********************************************/

void process_cmd(client_t *client, const char *buffer, fd_set *read_fds, int *active_client_count) {
    switch (client->state) {
        case INITIAL_STATE:
            printf("[DEBUG] Client is in INITIAL_STATE. Received buffer: %02x\n", buffer[0]);

            if (buffer[0] == PKT_CONNECT) {
                printf("[DEBUG] Packet type is PKT_CONNECT. Authenticating...\n");
                authenticate(client, buffer + 1);
            } else {
                printf("[ERROR]: Unknown packet type in INITIAL_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }
            break;

        case LOBBY_STATE:
            printf("[DEBUG] Client is in LOBBY_STATE. Received buffer: %02x\n", buffer[0]);

            if (buffer[0] == PKT_LIST_GAME) {
                printf("[DEBUG] Packet type is PKT_LIST_GAME. Listing games...\n");
                list_games(client);
            } else if (buffer[0] == PKT_CREATE_GAME) {
                printf("[DEBUG] Packet type is PKT_CREATE_GAME. Creating game...\n");
                create_game(client);
            } else if (buffer[0] == PKT_JOIN) {
                int game_id;

                memcpy(&game_id, buffer + 1, sizeof(int));
                game_id = (int) ntohl(game_id);
                printf("[DEBUG] Packet type is PKT_JOIN. Joining game with ID: %d\n", game_id);
                join_game(client, game_id);
            } else if (buffer[0] == PKT_DISCONNECT) {
                printf("[DEBUG] Packet type is PKT_DISCONNECT. Disconnecting client...\n");
                logout(client);
            } else {
                printf("[ERROR]: Unknown packet type in LOBBY_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }

            break;

        case INACTIVE_GAME_STATE:
            printf("[DEBUG] Client is in INACTIVE_GAME_STATE. Received buffer: %02x\n", buffer[0]);

            if (buffer[0] == PKT_CHECK_GAME) {
                game_t *game = client->current_game;
                if (game && game->status == 2) { // Game is ready
                    printf("[DEBUG] Game ready. Sending board and player states...\n");
                    update_board(game);
                    if (game->turn == 1 && game->player1 == client) {
                        sendpacket(client, STATUS_MAKE_MOVE, "Your turn to play.");
                    } else {
                        sendpacket(client, STATUS_WAIT_MOVE, "Waiting for opponent to play.");
                    }
                } else {
                    sendpacket(client, STATUS_CHECK_GAME_NOBODY, "No opponent joined yet.");
                }
            } else if (buffer[0] == PKT_QUIT) {
                printf("[DEBUG] Packet type is PKT_QUIT. Client is exiting the inactive game...\n");
                quit_game(client, client->current_game->id);
            } else {
                printf("[ERROR]: Unknown packet type in INACTIVE_GAME_STATE: %02x\n", buffer[0]);
                closeconnection(client, read_fds, active_client_count);
            }
            break;

        case PLAYING_STATE:
            printf("Client is in PLAYING_STATE.\n");

        if (buffer[0] == PKT_MOVE) {
            printf("[DEBUG] Packet type is PKT_MOVE. Processing move...\n");
            int x = (unsigned char)buffer[1];
            int y = (unsigned char)buffer[2];
            analyze_move(client, x, y);
        } else if (buffer[0] == PKT_ABANDON) {
            printf("[DEBUG] Packet type is PKT_ABANDON. Client is abandoning the game...\n");
            abandon(client, client->current_game->id);
        } else if (buffer[0] == PKT_CHECK_GAME) {
            printf("[DEBUG] Packet type is PKT_CHECK_GAME received in PLAYING_STATE. Ignoring.\n");
        } else {
            printf("[ERROR]: Unknown packet type in PLAYING_STATE: %02x\n", buffer[0]);
        }
        break;

        case WAITING_STATE:
            printf("[DEBUG] Client is in WAITING_STATE.\n");

        if (buffer[0] == PKT_ABANDON) {
            printf("[DEBUG] Packet type is PKT_ABANDON. Client is abandoning the game...\n");
            abandon(client, client->current_game->id);
        } else if (buffer[0] == PKT_CHECK_GAME) {
            printf("[DEBUG] Packet type is PKT_CHECK_GAME received in WAITING_STATE. Ignoring.\n");
        } else {
            printf("[ERROR]: Unknown packet type in WAITING_STATE: %02x\n", buffer[0]);
        }
        break;

        default:
            printf("[ERROR]: Unknown state for client (fd: %d): %d\n", client->fd, client->state);
            closeconnection(client, read_fds, active_client_count);
            break;
    }
}

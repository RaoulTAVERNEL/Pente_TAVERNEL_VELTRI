#ifndef LOBBY_H
#define LOBBY_H

#include "config.h"

void list_games(const client_t *client); // List all active games
void create_game(client_t *client); // Create a new game
void handle_check_game(const client_t *client); // Check if someone joined the inactive game
void join_game(client_t *client, int game_id); // Join a game
void assign_turns(int game_id, client_t *client, client_t *player1); // Determine 1st player in a new game
void update_board(const game_t *game); // Update the chessboard

#endif // LOBBY_H

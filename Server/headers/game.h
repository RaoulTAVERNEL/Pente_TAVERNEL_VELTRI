#ifndef GAME_H
#define GAME_H

#include "config.h"

void analyze_move(client_t *client, int x, int y); // Analyze the move based on Pente rules
int check_winner(int board[BOARD_SIZE][BOARD_SIZE], int x, int y, int player); // Check if a player wins
void update_player_stats(client_t *winner, client_t *loser); // Update players stats after game ended
void delete_game(int game_id); // Delete a game
void quit_game(client_t *client, int game_id); // Quit an inactive game (no penalty)
void abandon(client_t *client, int game_id); // Abandon a game

#endif // GAME_H

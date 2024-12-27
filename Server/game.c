#include "headers/game.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "headers/lobby.h"
#include "headers/network.h"

void analyze_move(client_t *client, int x, int y) {
    game_t *game = client->current_game;

    if (!game) {
        printf("[ERROR]: client not in a game.\n");
        return;
    }

    int player = (game->player1 == client) ? 1 : 2;

    if (game->turn != player) {
        printf("[ERROR]: attempt to make a move while client is not in playing state.\n");
        return;
    }

    if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE || game->board[x][y] != 0) {
        sendpacket(client, STATUS_INVALID_MOVE, "Error: Invalid move.");
        return;
    }

    game->board[x][y] = player; // Met à jour le plateau
    update_board(game); // Envoie la mise à jour à tous les joueurs
    printf("[DEBUG] Player %d placed a piece at (%d, %d).\n", player, x, y);

    if (check_winner(game->board, x, y, player)) {
        printf("[DEBUG] Player %d won the game.\n", player);
        char victory_message[BUFFER_SIZE];
        char defeat_message[BUFFER_SIZE];

        snprintf(victory_message, sizeof(victory_message),
                 "You won! Victories: %d, Defeats: %d, Score: %d, Games played: %d",
                 client->victories + 1, client->defeats, client->score + 3, client->games_played);

        client_t *opponent = (client == game->player1) ? game->player2 : game->player1;
        snprintf(defeat_message, sizeof(defeat_message),
                 "You lost! Victories: %d, Defeats: %d, Score: %d, Games played: %d",
                 opponent->victories, opponent->defeats + 1, opponent->score, opponent->games_played);

        sendpacket(client, STATUS_VICTORY, victory_message);
        sendpacket(opponent, STATUS_LOST, defeat_message);

        game->player1->state = LOBBY_STATE;
        game->player2->state = LOBBY_STATE;
        delete_game(game->id);
        update_player_stats(client, opponent);
    } else {
        game->turn = (player == 1) ? 2 : 1; // Passe le tour à l'autre joueur
        client->state = WAITING_STATE;
        client_t *opponent = (client == game->player1) ? game->player2 : game->player1;
        opponent->state = PLAYING_STATE;

        sendpacket(client, STATUS_WAIT_MOVE, "Waiting for opponent to play.");
        sendpacket(opponent, STATUS_MAKE_MOVE, "Your turn to play.");
    }
}



int check_winner(int board[BOARD_SIZE][BOARD_SIZE], int x, int y, int player) {
    int directions[4][2] = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};

    for (int d = 0; d < 4; d++) {
        int count = 1;

        for (int step = 1; step <= 4; step++) {
            int nx = x + step * directions[d][0];
            int ny = y + step * directions[d][1];

            if (nx >= 0 && nx < BOARD_SIZE && ny >= 0 && ny < BOARD_SIZE && board[nx][ny] == player) {
                count++;

                if (count >= 5) {
                    return 1;
                }
            } else {
                break;
            }
        }

        for (int step = 1; step <= 4; step++) {
            int nx = x - step * directions[d][0];
            int ny = y - step * directions[d][1];

            if (nx >= 0 && nx < BOARD_SIZE && ny >= 0 && ny < BOARD_SIZE && board[nx][ny] == player) {
                count++;

                if (count >= 5) {
                    return 1;
                }
            } else {
                break;
            }
        }
    }

    return 0;
}

void update_player_stats(client_t *winner, client_t *loser) {
    winner->victories += 1;
    winner->score += 10;
    loser->defeats += 1;
    loser->score = (loser->score >= 10) ? (loser->score - 10) : 0;
}

void delete_game(int game_id) {
    int index = game_id - 1;

    if (index < 0 || index >= game_counter) {
        printf("[ERROR]: Invalid game ID %d.\n", game_id);
        return;
    }

    game_t *game = &games[index];

    if (game->player1 != NULL) {
        game->player1->current_game = NULL;
    }

    if (game->player2 != NULL) {
        game->player2->current_game = NULL;
    }

    memset(game, 0, sizeof(game_t));

    for (int i = index; i < game_counter - 1; i++) {
        games[i] = games[i + 1];
    }

    game_counter--;
    printf("[DEBUG] Game ID %d has been successfully deleted.\n", game_id);
}

void quit_game(client_t *client, int game_id) {
    if (client == client->current_game->player1 && client->current_game->status == 1) {
        client->state = LOBBY_STATE;
        delete_game(game_id);
        sendpacket(client, STATUS_QUIT_GAME, "Exited the lobby successfully.");
    } else {
        printf("[ERROR]: Game ID %d is not valid for quitting.\n", game_id);
    }

}

void abandon(client_t *client, int game_id) {
    int index = game_id - 1;

    game_t *game = &games[index];

    if (game->player1 == NULL || game->player2 == NULL) {
        printf("[ERROR]: Game ID %d is not valid for abandonment.\n", game_id);
        return;
    }

    if (client != game->player1 && client != game->player2) {
        printf("[ERROR]: Client is not part of the game ID %d.\n", game_id);
        return;
    }

    client_t *winner = (client == game->player1) ? game->player2 : game->player1;
    client_t *loser = client;
    winner->state = LOBBY_STATE;
    loser->state = LOBBY_STATE;
    delete_game(game_id);
    update_player_stats(winner, loser);
    char message[BUFFER_SIZE];

    snprintf(message, sizeof(message), "You won. Victories: %d, Defeats: %d, Score: %d, Games played: %d",
             winner->victories, winner->defeats, winner->score, winner->games_played);
    sendpacket(winner, STATUS_VICTORY, message);
    snprintf(message, sizeof(message), "You abandoned the game. Victories: %d, Defeats: %d, Score: %d, Games played: %d",
             loser->victories, loser->defeats, loser->score, loser->games_played);
    sendpacket(loser, STATUS_ABANDON_GAME, message);
    printf("[DEBUG] Client %s abandoned the game ID %d. Winner is %s.\n", loser->username, game_id, winner->username);
}
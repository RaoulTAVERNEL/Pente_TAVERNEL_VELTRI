#include "headers/lobby.h"
#include "headers/network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

void list_games(const client_t *client) {
    char list[BUFFER_SIZE] = "";
    int available_games = 0;

    for (int i = 0; i < game_counter; i++) {
        if (games[i].status == 1) {
            char game_info[BUFFER_SIZE];

            snprintf(game_info, sizeof(game_info),
                     "Game %d: %s | Score: %d | Wins: %d | Losses: %d\n",
                     games[i].id, games[i].player1->username,
                     games[i].player1->score, games[i].player1->victories, games[i].player1->defeats);

            if (strlen(list) + strlen(game_info) < BUFFER_SIZE) {
                strcat(list, game_info);
            } else {
                break;
            }
            available_games++;
        }
    }

    if (available_games == 0) {
        sendpacket(client, STATUS_NO_GAME, "No games available.");
    } else {
        sendpacket(client, STATUS_LIST_GAMES, list);
    }
}

void create_game(client_t *client) {
    if (game_counter < MAX_GAMES) {
        // Initialisation des informations de la partie
        games[game_counter].id = game_counter + 1;
        games[game_counter].player1 = client;
        games[game_counter].player2 = NULL;
        games[game_counter].status = 1;

        // Log pour vérifier la taille du board
        size_t board_size = sizeof(games[game_counter].board) / sizeof(games[game_counter].board[0][0]);
        printf("[DEBUG] Board size: %zu cells\n", board_size);

        // Initialisation du board à 0 avec des logs pour vérifier les valeurs
        memset(games[game_counter].board, 0, sizeof(games[game_counter].board));
        printf("[DEBUG] Board initialized with zeros\n");

        // Mise à jour de l'état du client
        client->state = INACTIVE_GAME_STATE;
        client->current_game = &games[game_counter];
        game_counter++;

        sendpacket(client, STATUS_NEW_GAME_SUCCESS, "New game created. Waiting for another player to start the game...");
    } else {
        sendpacket(client, STATUS_NEW_GAME_FAILED, "Game creation failed: Lobby full");
    }
}


void handle_check_game(const client_t *client) {
    game_t *game = client->current_game;

    if (game->status != 2) {
        sendpacket(client, STATUS_CHECK_GAME_NOBODY, "No opponent joined yet.");
    } else {
        sendpacket(client, STATUS_CHECK_GAME_JOINED, "Another player has joined the game.");
    }
}

void join_game(client_t *client, int game_id) {
    if (game_id > 0 && game_id <= game_counter && games[game_id - 1].status == 1) {
        client_t *player1 = games[game_id - 1].player1;

        if (!player1) {
            printf("[ERROR]: Game join failed: Player 1 is not valid.\n");
            return;
        }

        if (games[game_id - 1].player2 != NULL) {
            printf("[ERROR]: Game join failed: Game is already full.\n");
            return;
        }

        games[game_id - 1].player2 = client;
        games[game_id - 1].status = 2;
        client->current_game = &games[game_id - 1];
        client->games_played++;
        player1->games_played++;
        printf("Nombre de partie jouée: %d", client->games_played);

        update_board(&games[game_id - 1]);
        assign_turns(game_id, client, player1);

        printf("[DEBUG] Game %d: Player 1 (%s) vs Player 2 (%s).\n", game_id, player1->username, client->username);
    } else {
        printf("[ERROR]: Game join failed: Invalid game ID.\n");
    }
}


void assign_turns(int game_id, client_t *client, client_t *player1) {
    if (!srand_flag) {
        srand_flag = 1;
        srand(time(NULL));
    }

    game_t *game = &games[game_id - 1];

    if (rand() % 2 == 0) {
        game->turn = 1;
        player1->state = PLAYING_STATE;
        client->state = WAITING_STATE;
        sendpacket(player1, STATUS_MAKE_MOVE, "Your turn to play.");
        sendpacket(client, STATUS_WAIT_MOVE, "Waiting for opponent to play.");
    } else {
        game->turn = 2;
        player1->state = WAITING_STATE;
        client->state = PLAYING_STATE;
        sendpacket(client, STATUS_MAKE_MOVE, "Your turn to play.");
        sendpacket(player1, STATUS_WAIT_MOVE, "Waiting for opponent to play.");
    }
}

void update_board(const game_t *game) {
    char board[BUFFER_SIZE] = {0};

    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            char temp[4]; // Assez pour "0," ou "10,"
            snprintf(temp, sizeof(temp), "%d,", game->board[i][j]);
            if (strlen(board) + strlen(temp) >= BUFFER_SIZE - 1) {
                printf("[ERROR] Board update message too large. Current length: %ld\n", strlen(board));
                return;
            }
            strcat(board, temp);
        }
    }

    // Supprimer la dernière virgule pour respecter le format attendu
    if (strlen(board) > 0) {
        board[strlen(board) - 1] = '\0';
    }

    // Vérification de la longueur totale attendue
    int expected_length = (BOARD_SIZE * BOARD_SIZE * 2) - 1; // 1 chiffre + 1 virgule par case, moins la virgule finale
    if (strlen(board) != expected_length) {
        printf("[ERROR] Board data is incomplete. Length: %ld, Expected: %d\n", strlen(board), expected_length);
        printf("[DEBUG] Partial board data:\n%s\n", board);
        return;
    }

    sendpacket(game->player1, STATUS_BOARD_UPDATE, board);
    sendpacket(game->player2, STATUS_BOARD_UPDATE, board);
}




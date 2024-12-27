#include "headers/config.h"

volatile sig_atomic_t server_running = 1;
int srand_flag = 0;
game_t games[MAX_GAMES] = {0};
int game_counter = 0;

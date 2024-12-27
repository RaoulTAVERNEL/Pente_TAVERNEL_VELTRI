cmake_minimum_required(VERSION 3.25)
project(Server C)

set(CMAKE_C_STANDARD 11)

add_executable(Server main.c
        config.c
        network.c
        login.c
        lobby.c
        game.c
        states.c
        headers/config.h
        headers/network.h
        headers/login.h
        headers/lobby.h
        headers/game.h
        headers/states.h)

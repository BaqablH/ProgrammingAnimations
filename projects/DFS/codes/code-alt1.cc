void explore(int y, int x) {
    // Checks if the square is an exit
    if (is_exit[y][x])
        found_exit = true;

    // Stops if an exit has been found
    if (found_exit)
        return;

    // Marks the square as not explorable
    is_explorable[y][x] = false;
    
    // Explore explorable adjacent squares
    for (int i : {0, 1, 2, 3})
        if (is_explorable[y + dy[i]][x + dx[i])
            explore(y + dy[i], x + dx[i]);
}
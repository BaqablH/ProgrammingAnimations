bool can_explore(int Y, int X) {
    // Checks square's position is valid
    if (Y < 0 or Y >= MATRIX_WIDTH)
        return false;
    if (X < 0 or X >= MATRIX_HEIGHT)
        return false;

    // Explore explorable adjacent squares
    return is_explorable[Y][X];
}


void explore(int y, int x) {
    // Marks the square as not explorable
    is_explorable[y][x] = false;
    
    // Explore explorable adjacent squares
    for (int i : {0, 1, 2, 3})
        if (can_explore(y + dy[i], x + dx[i]))
            explore(y + dy[i], x + dx[i]);
}
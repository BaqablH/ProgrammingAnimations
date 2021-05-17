int dy[] = {0, -1, 0, 1};

int dx[] = {1, 0, -1, 0};


void explore(int y, int x) {
    // Marks the square as not explorable
    is_explorable[y][x] = false;
    
    // Explore explorable adjacent squares
    for (int i : {0, 1, 2, 3})
        if (is_explorable[y + dy[i]][x + dx[i])
            explore(y + dy[i], x + dx[i]);
}
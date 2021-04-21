int dy[] = {0, -1, 0, 1};

int dx[] = {1, 0, -1, 0};


void explore(int y, int x) {
    is_explorable[y][x] = false;
    for (int i = 0; i < 4; ++i)
        if (is_explorable[y + dy[i]][x + dx[i])
            explore(y + dy[i], x + dx[i]);

}
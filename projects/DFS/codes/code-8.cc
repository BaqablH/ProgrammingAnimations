int dy[] = {0, -1, 0, 1};

int dx[] = {1, 0, -1, 0};


bool found_exit = false;


void explore(int y, int x) {
    if (is_exit[y][x])
        found_exit = true;


    is_explorable[y][x] = false;
    for (int i : {0, 1, 2, 3})
        if (is_explorable[y + dy[i]][x + dx[i])
            explore(y + dy[i], x + dx[i]);

}
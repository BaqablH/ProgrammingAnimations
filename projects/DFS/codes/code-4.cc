void explore(int y, int x) {
    is_explorable[y][x] = false;
    if (is_explorable[y][x + 1])
        explore(y, x + 1);
    if (is_explorable[y - 1][x])
        explore(y - 1, x);
    if (is_explorable[y][x - 1])
        explore(y, x - 1);

}
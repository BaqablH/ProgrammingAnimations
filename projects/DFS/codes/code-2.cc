void explore(int y, int x) {
    is_explorable[y][x] = false;
    if (is_explorable[y][x + 1])
        explore(y, x + 1);

}
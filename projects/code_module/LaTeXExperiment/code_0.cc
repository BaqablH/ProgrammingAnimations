void dfs(int y, int x) {
    if (not reachable[y][x] or visited[y][x]) 
        return;
    visited[y][x] = true
    for (int i = 0; i < 4; ++i)
        dfs(y + dy[i], x + dx[i])
}

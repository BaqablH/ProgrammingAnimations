def dfs(y, x):
    if not reachable[y][x] or visited[y][x] 
        return
    visited[y][x] = True
    for i in range(4):
        dfs(y + dy[i], x + dx[i])


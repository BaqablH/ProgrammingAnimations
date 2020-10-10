#!/usr/bin/env python

from manimlib.imports import *
from manimlib.constants import *

SCENE = None

class DFSSquare(Square):
  SIDE_LENGTH = 1.
  POSITION = np.array((-3, 3, 0))

  def __init__(self, i, j, c, **kwargs):
    Square.__init__(self, side_length=self.SIDE_LENGTH, **kwargs)
    self.pos = [i, j]
    self.dfs_arrow = None
    self.dfs_state = "UNDEFINED"
    self.dfs_color = BLACK
    self.set_from_char(c)
    self.shift(self.POSITION)
    self.shift(self.SIDE_LENGTH*np.array((j, -i, 0)))

  def dfs_update(self):
    return self.dfs_set_color().dfs_fill()

  def dfs_set_state_and_update(self, state_str):
    self.dfs_state = state_str
    return self.dfs_update()

  def dfs_set_color(self):
    self.dfs_color = {
      "UNDEFINED" : BLACK,
      "UNACCESIBLE" : BLACK,
      "UNVISITED" : RED,
      "VISITING" : YELLOW,
      "VISITED" : GREEN,
    }[self.dfs_state]
    return self

  def dfs_fill(self):
    self.set_fill(self.dfs_color).set_opacity(1.)
    return self

  def set_from_char(self, char):
    return self.dfs_set_state_and_update("UNACCESIBLE" if char == 'X' else "UNVISITED")

class DFSMatrix(object):
  def __init__(self, **kwargs):
    self.maze = []
    self.matrix = None
    self.height = None
    self.width = None

  def __call__(self, x, y):
    return self.maze[self.width * x + y]

  def get_square(self, x, y):
    return self.maze[self.width * x + y]

  def update_maze(self):
    self.maze = [DFSSquare(i, j, self.matrix[i][j]) for i in range(self.height) for j in range(self.width)]
    x = self.get_squares()
    l = len(x)
    print(l)
    for i in range(l):
      print(i, x[i].pos, x[i].get_center())

  def open_matrix(self, file="matrix.txt"):
    with open(file) as matrix:
      self.matrix = matrix.read().splitlines()
    self.height = len(self.matrix)
    self.width = len(self.matrix[0])
    self.update_maze()
    print(self.width, self.height)
    print(self.matrix)
    return self

  def get_squares(self):
    return [self.get_square(i, j) for i in range(self.height) for j in range(self.width)]
  
  def is_inside(self, y, x):
    return 0 <= x < self.width and 0 <= y < self.height

class Context(DFSMatrix):
  def __init__(self, **kwargs):
    DFSMatrix.__init__(self, **kwargs)

class DFSScene(Scene, Context):

  dfs_title = None

  def start_animation(self):
    for square in self.get_squares():
      self.play(ShowCreation(square), run_time=0.05)

  def end_animation(self):
    for square in self.get_squares():
      self.play(FadeOut(square), run_time=0.05)

  def animate_make_title(self):
    self.dfs_title = TextMobject("DFS").move_to(3.5*UP + 3.5*RIGHT)
    self.play(FadeInFrom(self.dfs_title, 2*DOWN), lag_ratio=0.)

  def update_square_state(self, square, state_str):
    square.dfs_set_state_and_update(state_str)
    self.play(ShowCreation(square), run_time=0.1)

  dy = [-1, 0, 1, 0]
  dx = [0, 1, 0, -1]
  INITIAL_POS = [1, 1]

  def dfs(self, y, x):
    if not self.is_inside(y, x):
      return
    if (self.get_square(y, x).dfs_state != "UNVISITED"):
      return
    self.update_square_state(self.get_square(y, x), "VISITING")
    for i in range(4):
      self.dfs(y + self.dy[i], x + self.dx[i])
    self.update_square_state(self.get_square(y, x), "VISITED")

  def construct(self):
    Context.__init__(self)

    self.animate_make_title()
 
    self.open_matrix()

    self.start_animation()

    self.dfs(*self.INITIAL_POS)

    self.end_animation()

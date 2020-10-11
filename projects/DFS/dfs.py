#!/usr/bin/env python

from manimlib.imports import *
from manimlib.constants import *

SCENE = None

class DFSSquare(Square):
  DFSMATRIX_POSITION = np.array((-6.5, 3.5, 0))

  def __init__(self, i, j, c, side, **kwargs):
    Square.__init__(self, side_length=side, **kwargs)
    self.pos = [i, j]
    self.arrow = None
    self.dfs_state = "UNDEFINED"
    self.dfs_color = BLACK
    self.set_from_char(c)
    self.shift(self.DFSMATRIX_POSITION)
    self.shift(self.side_length*np.array((j, -i, 0)))
    self.add_updater(lambda d: d.set_fill(self.dfs_color))

  def update_square(self):
    self.dfs_color = {
      "UNACCESIBLE" : BLACK,
      "UNACCESIBLE_CHECKING" : DARK_BLUE,
      "UNVISITED" : RED,
      "VISITING" : YELLOW,
      "VISITED" : GREEN,
    }[self.dfs_state]
    self.set_fill(self.dfs_color).set_opacity(1.)
    return self

  def set_state_and_update_square(self, state_str):
    self.dfs_state = state_str
    return self.update_square()

  def set_from_char(self, char):
    return self.set_state_and_update_square("UNACCESIBLE" if char == 'X' else "UNVISITED")

  def create_arrow(self):
    self.arrow = Arrow().shift(self.get_center()).rotate(TAU/4).scale(0.5).set_fill(BLACK)

  def rotate_arrow(self):
    self.arrow.rotate(-TAU/4)

class DFSMatrix(object):
  MAX_MATRIX_SIZE = 8.

  def __init__(self, **kwargs):
    self.maze = []
    self.matrix = None
    self.height = None
    self.width = None
    self.side_length = None
    self.load_matrix()

  def get_square(self, x, y):
    return self.maze[self.width * x + y]

  def update_maze(self):
    self.maze = [DFSSquare(i, j, self.matrix[i][j], self.side_length) for i in range(self.height) for j in range(self.width)]
    x = self.get_squares()
    l = len(x)
    print(l)
    for i in range(l):
      print(i, x[i].pos, x[i].get_center())

  def load_matrix(self, file="matrix.txt"):
    with open(file) as matrix:
      self.matrix = matrix.read().splitlines()
    self.height = len(self.matrix)
    self.width = len(self.matrix[0])
    self.side_length = self.MAX_MATRIX_SIZE/max(self.width, self.height)
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

class Code(TextMobject):
  CODE_POSITION = np.array((-6.5, 3.5, 0))
 
  def __init__(self, **kwargs):
    TextMobject.__init__(self, **kwargs)
    self.shift(self.CODE_POSITION)
    self.code = self.load_code()
"""
  def load_code(self, file="code.txt"):
    with open(file) as code:
      self.code = code.read().splitlines()
    self.height = len(self.matrix)
    self.width = len(self.matrix[0])
    self.side_length = self.MAX_MATRIX_SIZE/max(self.width, self.height)
    self.update_maze()
    print(self.width, self.height)
    print(self.matrix)
    return self
"""

class DFSScene(Scene, Context, Code):

  dfs_title = None

  def start_animation(self):
    self.play(*[FadeInFromDown(square) for square in self.get_squares()], run_time=5.)

  def end_animation(self):
    self.play(*[FadeOut(square) for square in self.get_squares()], run_time=1.)

  def animate_make_title(self):
    self.dfs_title = TextMobject("DFS").move_to(3.5*UP + 3.5*RIGHT)
    self.play(FadeInFrom(self.dfs_title, 2*DOWN), lag_ratio=0.)

  def update_square_state(self, square, state_str):
    square.set_state_and_update_square(state_str)

  def create_arrow(self, square):
    square.create_arrow()
    self.play(ShowCreation(square.arrow), run_time=0.25)

  def rotate_arrow(self, square):
    self.play(Rotate(square.arrow), angle=-TAU/4, run_time=0.25)
    #square.rotate_arrow()

  def remove_arrow(self, square):
    self.remove(square.arrow)
    square.arrow = None

  dy = [-1, 0, 1, 0]
  dx = [0, 1, 0, -1]
  INITIAL_POS = [1, 1]

  def dfs(self, y, x):
    self.wait(0.2)
    if not self.is_inside(y, x): return # Useless for now
    if (self.get_square(y, x).dfs_state != "UNVISITED"):
      keep_state = self.get_square(y, x).dfs_state
      self.get_square(y, x).set_state_and_update_square("UNACCESIBLE_CHECKING")
      self.wait(0.25)
      self.get_square(y, x).set_state_and_update_square(keep_state)
      return
    self.update_square_state(self.get_square(y, x), "VISITING")
    
    self.create_arrow(self.get_square(y, x))
    for i in range(4):
      if i > 0: self.rotate_arrow(self.get_square(y, x))
      self.dfs(y + self.dy[i], x + self.dx[i])
    self.remove_arrow(self.get_square(y, x))
    self.wait(0.2)

    self.update_square_state(self.get_square(y, x), "VISITED")

  def construct(self):
    Context.__init__(self)

    self.animate_make_title()
    self.start_animation()
    self.dfs(*self.INITIAL_POS)
    self.end_animation()

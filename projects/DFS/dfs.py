#!/usr/bin/env python

from manimlib.imports import *

import sys
sys.path.append('../../')

from lib.code_obj import Code

SCENE = None
DFS_COLOR_DICT = {
  "UNACCESIBLE" : GREEN_B,
  "UNACCESIBLE_CHECKING" : DARK_BLUE,
  "UNVISITED" : DARK_GREY,
  "VISITING" : GREY,
  "VISITED" : WHITE,
  "TRUE" : GREEN,
  "FALSE" : RED,
}

class ThreeD:
  BaseDFSSquareClass = Prism
  SceneType = ThreeDScene

class TwoD:
  BaseDFSSquareClass = Square
  SceneType = Scene

MODE = TwoD

class DFSSquare(MODE.BaseDFSSquareClass):
  DFSMATRIX_POSITION = np.array((-6.5, 3.5, 0))

  def __init__(self, i, j, c, side, **kwargs):
    if MODE.BaseDFSSquareClass == Prism:
      MODE.BaseDFSSquareClass.__init__(self, dimensions=self.get_prism_dimensions(side, c), **kwargs)
    else:
      MODE.BaseDFSSquareClass.__init__(self, side_length=side, **kwargs)
    
    self.pos = [i, j]
    self.ctr = 0
    self.arrow = None
    self.ctr_obj = None
    self.dfs_state = "UNDEFINED"
    self.dfs_color = BLACK
    self.set_from_char(c)
    self.shift(self.DFSMATRIX_POSITION)
    self.shift(self.side_length*np.array((j, -i, 0)))
    self.add_updater(lambda d: d.set_fill(self.dfs_color))

  def update_square(self):
    self.dfs_color = DFS_COLOR_DICT[self.dfs_state]
    self.set_fill(self.dfs_color).set_opacity(1.)
    return self

  def set_state_and_update_square(self, state_str):
    self.dfs_state = state_str
    return self.update_square()

  def set_from_char(self, char):
    return self.set_state_and_update_square("UNACCESIBLE" if char == 'X' else "UNVISITED")

  def get_ctr_obj(self):
    return TexMobject("i = {}".format(self.ctr)).\
      shift(self.get_center() + self.side_length*np.array((0.3, -0.375, 0.))).\
        scale(0.25).set_color(WHITE)

  def create_arrow(self):
    self.arrow = Arrow().shift(self.get_center()).rotate(TAU/4).scale(0.5).set_fill(BLACK)
    self.ctr_obj = self.get_ctr_obj()

  def get_prism_dimensions(self, side, char):
    return [side, side, side if char == 'X' else 0]

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
    #print(l)
    # for i in range(l):
    #  print(i, x[i].pos, x[i].get_center())

  def load_matrix(self, file="matrix.txt"):
    with open(file) as matrix:
      self.matrix = matrix.read().splitlines()
    self.height = len(self.matrix)
    self.width = len(self.matrix[0])
    self.side_length = self.MAX_MATRIX_SIZE/max(self.width, self.height)
    self.update_maze()
    # print(self.width, self.height)
    # print(self.matrix)
    return self

  def get_squares(self):
    return [self.get_square(i, j) for i in range(self.height) for j in range(self.width)]
  
  def is_inside(self, y, x):
    return 0 <= x < self.width and 0 <= y < self.height

class Context(DFSMatrix):
  def __init__(self, **kwargs):
    DFSMatrix.__init__(self, **kwargs)

class DFSCode(Code):
  CODE_POSITION = np.array([4.5, 2., 0])
 
  def __init__(self, **kwargs):
    Code.__init__(self, file_name="code.txt", **kwargs)
    self.shift(self.CODE_POSITION).scale(0.5)

class DFSScene(MODE.SceneType, Context):

  dfs_title = None
  code = DFSCode()
  iter_count = 0

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
    self.play(ShowCreation(square.ctr_obj), run_time=0.25)

  def rotate_arrow(self, square):
    self.play(Rotate(square.arrow), angle=-TAU/4, run_time=0.25)
    square.ctr += 1
    new_ctr_obj = square.get_ctr_obj() 
    self.play(Transform(square.ctr_obj, new_ctr_obj))
    square.ctr_obj = new_ctr_obj

  def remove_arrow(self, square):
    self.remove(square.arrow)
    square.arrow = None

  def highlight_lines(self, lines={}):
    self.remove(*self.code.background)
    self.add(*self.code.highlight_lines(lines))
    self.wait(0.25)

  def animate_line_23_true(self, y, x):
    self.highlight_lines({2: RED, 3: RED})
    keep_state = self.get_square(y, x).dfs_state
    self.get_square(y, x).set_state_and_update_square("FALSE")
    self.wait(0.25)
    self.get_square(y, x).set_state_and_update_square(keep_state)
    self.highlight_lines()

  def animate_line_45_false(self, y, x):
    self.highlight_lines({4: GREEN, 5: GREEN})
    keep_state = self.get_square(y, x).dfs_state
    self.get_square(y, x).set_state_and_update_square("TRUE")
    self.wait(0.25)
    self.get_square(y, x).set_state_and_update_square(keep_state)
    self.update_square_state(self.get_square(y, x), "VISITING")
    self.highlight_lines()

  def animate_line_6(self, y, x, i):
    self.highlight_lines({6: GREY})
    if i == 0: self.create_arrow(self.get_square(y, x))
    else: self.rotate_arrow(self.get_square(y, x))
    self.highlight_lines()

  def animate_line_7(self, y, x, i):
    self.highlight_lines({7: GOLD})
    self.dfs(y + self.dy[i], x + self.dx[i])
    self.highlight_lines()

  dy = [-1, 0, 1, 0]
  dx = [0, 1, 0, -1]
  INITIAL_POS = [1, 1]

  def dfs(self, y, x):
    self.iter_count += 1
    print("ITERATION:", self.iter_count)

    self.wait(0.2)
    if not self.is_inside(y, x): return # Useless for now
    if (self.get_square(y, x).dfs_state != "UNVISITED"):
      self.animate_line_23_true(y, x)
      return
    else:
      self.animate_line_45_false(y, x)

    for i in range(4):
      self.animate_line_6(y, x, i)
      self.animate_line_7(y, x, i)

    self.remove_arrow(self.get_square(y, x))
    self.wait(0.2)

    self.update_square_state(self.get_square(y, x), "VISITED")

  def construct(self):
    Context.__init__(self)
    if MODE == ThreeD:
      self.set_camera_orientation(phi=30*consts.DEGREES, theta=-90*consts.DEGREES, distance=20)

    self.animate_make_title()
    self.start_animation()
    self.add(self.code)
    self.dfs(*self.INITIAL_POS)
    self.end_animation()

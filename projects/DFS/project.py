#!/usr/bin/env python

import sys
sys.path.append('../../')

from manimlib.imports import *

from lib.code_obj import Code

CHAR_TO_STATE = {
  'X' : "UNACCESIBLE",
  '.' : "UNVISITED",
  'S' : "START",
  'E' : "EXIT",
}

DFS_COLOR_DICT = {
  "UNACCESIBLE" : "#228b22",
  "UNVISITED" : DARK_GREY,
  "START" : BLUE,
  "EXIT" : YELLOW,
  "HIGHLIGHT_1" : GOLD,
  "HIGHLIGHT_2" : PINK,
  "HIGHLIGHT_3" : RED,
}

class ThreeD:
  BaseDFSSquareClass = Prism
  SceneType = ThreeDScene

class TwoD:
  BaseDFSSquareClass = Square
  SceneType = Scene

MODE = TwoD

directions = [(0, 1), (-1, 0), (0, -1), (1, 0)]
INITIAL_POS = (2, 6)

class DFSSquare(MODE.BaseDFSSquareClass):
  Grid_POSITION = np.array((-6.5, 3.5, 0))

  def __init__(self, y, x, c, side, **kwargs):
    if MODE.BaseDFSSquareClass == Prism:
      MODE.BaseDFSSquareClass.__init__(self, dimensions=self.get_prism_dimensions(side, c), **kwargs)
    else:
      MODE.BaseDFSSquareClass.__init__(self, side_length=side, **kwargs)

    self.pos = [y, x]
    self.ctr = 0
    self.char = c
    self.arrow = None
    self.ctr_obj = None
    self.dfs_state = "UNDEFINED"
    self.dfs_color = BLACK
    self.set_from_char('X' if c == 'X' else '.')
    self.shift(self.Grid_POSITION)
    self.shift(self.side_length*np.array((x, -y, 0)))
    self.add_updater(lambda d: d.set_fill(self.dfs_color))  

  def update_square(self):
    self.dfs_color = DFS_COLOR_DICT[self.dfs_state]
    self.set_fill(self.dfs_color).set_opacity(1.)
    return self

  def set_state_and_update_square(self, state_str):
    self.dfs_state = state_str
    return self.update_square()

  def set_from_char(self, c):
    return self.set_state_and_update_square(CHAR_TO_STATE[c])

  def get_ctr_obj(self):
    return TexMobject("i = {}".format(self.ctr)).\
      shift(self.get_center() + self.side_length*np.array((0.3, -0.375, 0.))).\
        scale(0.25).set_color(WHITE)

  def create_arrow(self):
    self.arrow = Arrow().shift(self.get_center()).rotate(TAU/4).scale(0.5).set_fill(BLACK)
    self.ctr_obj = self.get_ctr_obj()

  def get_prism_dimensions(self, side, char):
    return [side, side, side if char == 'X' else 0]

class Grid(object):
  MAX_MATRIX_SIZE = 7.5

  def __init__(self, **kwargs):
    self.maze = []
    self.matrix = None
    self.matrix_height = None
    self.matrix_width = None
    self.side_length = None
    self.load_matrix()

  def is_inside(self, y, x):
    return 0 <= y < self.matrix_height and 0 <= x < self.matrix_width

  def get_square(self, y, x):
    return self.maze[self.matrix_width * y + x]

  def update_maze(self):
    self.maze = [
        DFSSquare(y, x, self.matrix[y][x], self.side_length) 
            for y in range(self.matrix_height) 
                for x in range(self.matrix_width)]

  def load_matrix(self, file="matrix.txt"):
    with open(file) as matrix:
      self.matrix = matrix.read().splitlines()
    self.matrix_height = len(self.matrix)
    self.matrix_width = len(self.matrix[0])
    self.side_length = self.MAX_MATRIX_SIZE/max(self.matrix_width, self.matrix_height)
    self.update_maze()

  def get_squares(self):
    return [self.get_square(y, x) 
        for y in range(self.matrix_height)
            for x in range(self.matrix_width)]

  def select_square(self, y, x):
    self.get_square(y, x).set_state_and_update_square("HIGHLIGHT_1")

  def show_adjacent_squares(self, y, x):
    for dy, dx in directions:
      self.get_square(y + dy, x + dx).set_state_and_update_square("HIGHLIGHT_2")

  def show_reachable_adjacent_squares(self, y, x):
    for dy, dx in directions:
      sq = self.get_square(y + dy, x + dx)
      if (sq.char != 'X'):
        sq.set_state_and_update_square("HIGHLIGHT_2")

  def reset_adjacency_highlighting(self):
    for sq in self.get_squares():
      if sq.dfs_state == "HIGHLIGHT_2":
        sq.set_state_and_update_square(CHAR_TO_STATE[sq.char])

  def reset_full_highlighting(self):
    for sq in self.get_squares():
      if "HIGHLIGHT" in sq.dfs_state:
        sq.set_state_and_update_square(CHAR_TO_STATE[sq.char])

  def highlight_distance(self, dist, distance_matrix):
    for y in range(len(distance_matrix)):
      for x in range(len(distance_matrix[y])):
        if distance_matrix[y][x] == dist:
          self.get_square(y, x).set_state_and_update_square("HIGHLIGHT_3")

  def mark_squares_with_char(self, c):
    [sq.set_from_char(c) for sq in self.get_squares() if sq.char == c]

  def mark_init_squares(self):
    self.mark_squares_with_char('S')

  def mark_exit_squares(self):
    self.mark_squares_with_char('E')

  def get_distance_matrix(self, y, x):
    distance_matrix = []
    for _ in range(self.matrix_height):
      distance_matrix.append([None] * self.matrix_width)

    distance_matrix[y][x] = 0
    queue = [(y, x, 0)]
    p = 0

    while p != len(queue):
      Y, X, D = queue[p]
      p += 1
      for dx, dy in directions:
        yy, xx = Y + dy, X + dx
        if self.is_inside(yy, xx) and self.get_square(yy, xx).char != 'X' and distance_matrix[yy][xx] is None:
          distance_matrix[yy][xx] = D + 1
          queue.append((yy, xx, D + 1))

    return distance_matrix

class Context(Grid):
  def __init__(self, **kwargs):
    Grid.__init__(self, **kwargs)
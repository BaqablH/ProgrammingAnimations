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
  # The next ones may need review
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

directions = [(0, 1), (-1, 0), (0, -1), (1, 0)]

def add_displacement(y, x, i):
  dy, dx = directions[i]
  return (y + dy, x + dx)

INITIAL_POS = (2, 4)
EXAMPLE_POS = (2, 6)

class DFSSquare(MODE.BaseDFSSquareClass):
  GRID_POSITION = np.array((-6.5, 3.5, 0))

  def __init__(self, y, x, c, side, **kwargs):
    if MODE.BaseDFSSquareClass == Prism:
      MODE.BaseDFSSquareClass.__init__(self, dimensions=self.get_prism_dimensions(side, c), **kwargs)
    else:
      MODE.BaseDFSSquareClass.__init__(self, side_length=side, stroke_width=2, **kwargs)

    self.pos = [y, x]
    self.ctr = None
    self.char = c
    self.arrow = None
    self.ctr_obj = None
    self.dfs_state = "UNDEFINED"
    self.dfs_color = BLACK
    self.set_from_char('X' if c == 'X' else '.')
    self.shift(self.GRID_POSITION)
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

  def new_ctr_obj(self):
    self.ctr = 0 if self.ctr is None else self.ctr + 1
    tex = "i = {}".format(self.ctr)
    return TexMobject(tex, tex_to_color_map={tex : WHITE}, background_stroke_width=0).\
      shift(self.get_center() + self.side_length*np.array((0.3, -0.375, 0.))).\
        scale(0.25).set_fill(WHITE)

  def create_arrow(self):
    self.arrow = Arrow().shift(self.get_center()).scale(0.5).set_fill(BLACK)
    self.ctr_obj = self.new_ctr_obj()

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

class CommonScene(Scene, Context):
  def start_animation(self, **kwargs):
    self.play(*[FadeInFromDown(square) for square in self.get_squares()], **kwargs)

  def end_animation(self, **kwargs):
    self.play(*[FadeOut(square) for square in self.get_squares()], **kwargs)

  def highlight_lines(self, run_time=0., lines={}):
    self.remove(*self.code.background)
    self.add(*self.code.highlight_lines(lines))
    self.wait(run_time)

class NewCanvas(Rectangle):
  def __init__(self, **kwargs):
      super().__init__(width=16, height=10, **kwargs)
      self.set_opacity(1.).set_color(BLACK).set_fill(BLACK)

class MainIdea(CommonScene):
  def animate_maze_construction(self):
    self.start_animation(run_time=3.)
    self.wait(16.)
    self.mark_init_squares()
    self.wait(2.)
    self.mark_exit_squares()
    self.wait(2.)

  def animate_adjacency_example(self):
    self.wait(9.)
    self.select_square(*EXAMPLE_POS)
    self.wait(1.)
    self.show_adjacent_squares(*EXAMPLE_POS)
    self.wait(3.)
    self.reset_adjacency_highlighting()
    self.wait(1.)
    self.show_reachable_adjacent_squares(*EXAMPLE_POS)
    self.wait(2.)
    self.reset_full_highlighting()
    self.wait(2.)

  def animate_distances(self):
    distance_matrix = self.get_distance_matrix(*INITIAL_POS)
    dist_list = []
    for row in distance_matrix:
      dist_list += list(filter(lambda x : x is not None, row))
    max_dist = max(*dist_list)

    self.wait(5.)
    waits = [8., 3., 2., 2.]
    for dist in range(max_dist + 1):
      self.highlight_distance(dist, distance_matrix)
      wait_time = waits[dist] if dist < len(waits) else 1.
      self.wait(wait_time)

  def show_text1(self):
    canv = NewCanvas()
    self.add(canv)
    self.wait(4.5)
    o1 = TextMobject("1. Visits every reachable square")
    o2 = TextMobject("2. Avoids revisiting squares")
    text = VGroup(o1, o2).arrange(DOWN)
    self.add(o1)
    self.wait(4.5)
    self.add(o2)
    self.wait(10.)
    self.remove(canv, o1, o2)

  def show_text2(self):
    canv = NewCanvas()
    self.add(canv)
    self.wait(8.)
    o1 = TextMobject("Exploring a square implies exploring its neighbours").scale(0.8)
    o2 = TexMobject("\Rightarrow").scale(0.8)
    o3 = TextMobject("Exploring the initial square implies exploring all reachable squares").scale(0.8)
    text = VGroup(o1, o2, o3).arrange(DOWN)
    self.add(o1)
    self.wait(3.)
    self.add(o2)
    self.wait(5.)
    self.add(o3)
    self.wait(5.)
    self.remove(canv, o1, o2, o3)

  def connected_component(self):
    self.wait(19.5)

    o1 = TextMobject("Connected component").shift(np.array((3.5, 1., 0.)))
    self.add(o1)
    self.wait(6.5)
    self.remove(o1)

    self.wait(14.)

  def construct(self):
    Context.__init__(self)

    self.wait(5.)
    self.animate_maze_construction()

    self.show_text1()

    self.animate_adjacency_example()

    self.show_text2()

    self.animate_distances()

    self.connected_component()
    
    self.wait(27.)
    #self.reset_full_highlighting()
    self.end_animation(run_time=1.)

class DFSCode(Code):
  def __init__(self, **kwargs):
    Code.__init__(self, style='default', **kwargs)
    self.scale(0.5).align_on_border(UP + RIGHT).shift(np.array([0, -1, 0]))

class ShowCode(CommonScene):
  def get_rectangle(self, i, w, h, displ0, displ_vec, var):
    rect = Rectangle(width=self.side_length*w, height=self.side_length*h)
    rect.set_color(GOLD).set_fill(GOLD).set_opacity(0.5)
    rect.shift(displ0).shift(self.side_length*i*displ_vec)
    obj = TexMobject("{} = {}".format(var, i)).shift(np.array([2, 0, 0]))
    return rect, obj

  def get_row_rectangle(self, i):
    return self.get_rectangle(i, self.matrix_width, 1, np.array((-3.16666, 3.5, 0)), np.array([0, -1, 0]), 'y')

  def get_col_rectangle(self, j):
    return self.get_rectangle(j, 1, self.matrix_height, np.array((-6.5, 0.16666, 0)), np.array([1, 0, 0]), 'x')

  def animate_rectangles(self, id, func, iters):
    rect, obj = func(0)
    self.add(rect, obj)
    self.wait(2.)

    for i in range(1, iters):
      wait_time = 4/3 if i == 1 else 2/3
      new_rect, new_obj = func(i)
      self.play(
        *[Transform(rect, new_rect), Transform(obj, new_obj)],
        skip_animations=True,
        run_time=wait_time
      )
      self.wait(wait_time/2)

    self.remove(rect, obj)
  
  def get_code_file(self, i):
    return "codes/code-{}.cc".format(i)

  def transform_code(self, iter, run_time):
      self.play(
        Transform(self.code, DFSCode(file_name=self.get_code_file(iter))),
        skip_animations=True,
        run_time=run_time
      )

  def animate_codes(self):
    self.code = DFSCode(file_name=self.get_code_file(0))
    self.play(FadeIn(self.code, run_time=2.))

    self.wait(22)
    self.transform_code(1, .5)

    self.wait(63.5)
    self.transform_code(2, .5)

    self.wait(19.5)
    self.transform_code(3, .5)

    self.wait(2.5)
    self.transform_code(4, .5)

    self.wait(2.5)
    self.transform_code(5, .5)

    self.wait(10.5)
    self.transform_code(6, .5)

    self.wait(5.5)
    self.transform_code(7, .5)

    self.wait(83.5)
    self.transform_code(8, .5)

    self.wait(8.)
    self.highlight_lines(4.5, {6 : YELLOW})
    self.highlight_lines(6., {i : YELLOW for i in range(9, 12)})
    self.highlight_lines(0., {})

    self.wait(21.)

  def construct(self):
    Context.__init__(self)

    self.start_animation(run_time=1.)

    self.wait(20.)

    self.animate_rectangles(0, self.get_row_rectangle, self.matrix_height)
    
    self.wait(13.)
    
    self.animate_rectangles(1, self.get_col_rectangle, self.matrix_width)

    self.wait(26.)

    self.animate_codes()

    self.end_animation(run_time=1.)

class TheAnimation(CommonScene):

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
    self.play(
      Transform(square.ctr_obj, square.new_ctr_obj()),
      Rotate(square.arrow, angle=TAU/4),
      run_time=0.5)

  def remove_arrow(self, square):
    self.remove(square.arrow, square.ctr_obj)
    square.arrow = None
    square.ctr_obj = None

  def animate_mark_unexplorable(self, y, x):
    self.highlight_lines(0., {3: YELLOW})
    self.wait(0.2)
    self.update_square_state(self.get_square(y, x), "VISITING")
    self.wait(0.2)

    if (y, x) == (2, 4): self.wait(9.)
    if (y, x) == (1, 4): self.wait(8.5)

    if (y, x) == (1, 5): self.wait(2.5)
    if (y, x) == (1, 6): self.wait(8.)
    
    self.highlight_lines()

  def animate_is_explorable(self, y, x, t):
    self.highlight_lines(0., {7: GREEN, 8: YELLOW})
    self.get_square(y, x).set_state_and_update_square("TRUE")
    self.wait(0.25)

    self.highlight_lines()

  def animate_is_unexplorable(self, y, x, t):
    self.highlight_lines(0., {7: RED})
    keep_state = self.get_square(y, x).dfs_state
    self.get_square(y, x).set_state_and_update_square("FALSE")
    self.wait(0.25)

    if t == (2, 4, 0): self.wait(3.)

    if t == (1, 6, 0): self.wait(4.)
    if t == (1, 6, 1): self.wait(6.)
    if t == (1, 6, 2): self.wait(13.)

    if t == (4, 6, 0): self.wait(3.)
    if t == (4, 6, 1): self.wait(3.)

    if t in [(3, 4, i) for i in range(4)]: self.wait(2.5)

    if t == (4, 4, 3): self.wait(2.)


    self.get_square(y, x).set_state_and_update_square(keep_state)
    self.highlight_lines()

  def update_arrow(self, y, x, i):
      if i == 0:
        self.create_arrow(self.get_square(y, x))
      else:
        self.rotate_arrow(self.get_square(y, x))

  def dfs(self, y, x):
    self.iter_count += 1
    print("ITERATION:", self.iter_count)

    self.wait(0.2)
    if not self.is_inside(y, x): return # Useless for now
    #if (self.get_square(y, x).dfs_state != "UNVISITED"):
    #  self.animate_line_23_true(y, x)
    #  return
    #else:

    if (y, x) == (2, 4): self.wait(1.)
    if (y, x) == (1, 4): self.wait(7.)

    self.animate_mark_unexplorable(y, x)
    
    if (y, x) == (7, 0):
      self.rip = True
      self.wait(15.)
      self.play(Transform(self.code,
        DFSCode(file_name="codes/code-alt1.cc")),
        run_time=1.
      )
      self.wait(57.)
      self.play(Transform(self.code,
        DFSCode(file_name="codes/code-alt2.cc")),
        run_time=1.
      )
      self.wait(11.)
    
    if self.rip:
      return

    if (y, x) == (4, 6): self.wait(6.)
    if (y, x) == (4, 4): self.wait(5.)
    if (y, x) == (5, 2): self.wait(3.)
    if (y, x) == (1, 3): self.wait(6.)

    for i in range(4):
      Y, X = add_displacement(y, x, i)
      t = (y, x, i)
      self.update_arrow(y, x, i)
      if (self.get_square(Y, X).dfs_state in ["UNVISITED", "EXIT"]):
        self.animate_is_explorable(Y, X, t)
        self.dfs(Y, X)
      else:
        self.animate_is_unexplorable(Y, X, t)

      if self.rip:
        return

      if t == (2, 4, 0): self.wait(1.5)

    self.remove_arrow(self.get_square(y, x))
    self.wait(0.2)

    self.update_square_state(self.get_square(y, x), "VISITED")

    if (y, x) == (3, 4): self.wait(25.)
    if (y, x) == (1, 3): self.wait(10.)

  def construct(self):
    Context.__init__(self)

    self.dfs_title = None
    self.code = DFSCode(file_name="codes/code-anim.cc")
    self.iter_count = 0
    self.rip = False

    if MODE == ThreeD:
      self.set_camera_orientation(phi=30*consts.DEGREES, theta=-90*consts.DEGREES, distance=20)

    self.animate_make_title()

    self.mark_init_squares()
    self.mark_exit_squares()
    self.start_animation(run_time=2.)
    self.add(self.code)
    
    self.wait(3.)

    self.dfs(*INITIAL_POS)
    self.end_animation(run_time=1.)

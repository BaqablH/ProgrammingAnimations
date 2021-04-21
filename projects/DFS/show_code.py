import sys
sys.path.append('.')
from project import *

class Context(Grid):
  def __init__(self, **kwargs):
    Grid.__init__(self, **kwargs)

class DFSCode(Code):
  CODE_POSITION = np.array([4., 2., 0])
 
  def __init__(self, **kwargs):
    Code.__init__(self, style='default', **kwargs)
    self.align_on_border(UP + RIGHT)
    self.scale(0.5)
    #self.shift(self.CODE_POSITION).scale(0.5)

class ShowCodeScene(Scene, Context):
  def start_animation(self, run_time=2.):
    self.play(*[FadeInFromDown(square) for square in self.get_squares()], run_time=run_time)

  def end_animation(self, run_time=2.):
    self.play(*[FadeOut(square) for square in self.get_squares()], run_time=run_time)

  def highlight_lines(self, run_time, lines={}):
    self.remove(*self.code.background)
    self.add(*self.code.highlight_lines(lines))
    self.wait(run_time)

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

  def animate_rectangles(self, func, iters):
    rect, obj = func(0)
    self.add(rect, obj)

    for i in range(1, iters):
      new_rect, new_obj = func(i)
      self.play(
        *[Transform(rect, new_rect), Transform(obj, new_obj)],
        skip_animations=True,
        run_time=0.5
      )
      self.wait(0.5)

    self.remove(rect, obj)
    self.wait(0.5)
  
  def get_code_file(self, i):
    return "codes/code-{}.cc".format(i)

  def construct(self):
    Context.__init__(self)

    self.start_animation(0.1)

    # Matrix notation explanation
    self.animate_rectangles(self.get_row_rectangle, self.matrix_height)
    self.animate_rectangles(self.get_col_rectangle, self.matrix_width)

    self.code = DFSCode(file_name=self.get_code_file(0))
    self.add(self.code)

    for i in range(11):
      self.play(
        Transform(self.code, DFSCode(file_name=self.get_code_file(i))),
        skip_animations=True,
        run_time=0.25
      )
      self.wait(1.5)

    self.highlight_lines(2., {12 : YELLOW})
    self.highlight_lines(2., {i : YELLOW for i in range(16, 19)})

    self.wait(3.)

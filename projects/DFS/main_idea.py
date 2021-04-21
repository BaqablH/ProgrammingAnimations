import sys
sys.path.append('.')
from project import *

class MainIdea(Scene, Context):

  def start_animation(self):
    self.play(*[FadeInFromDown(square) for square in self.get_squares()], run_time=1.5)

  def end_animation(self):
    self.play(*[FadeOut(square) for square in self.get_squares()], run_time=1.)

  def construct(self):
    Context.__init__(self)

    ## MAZE CONSTRUCTION
    self.start_animation()
    self.wait(2.)
    self.mark_init_squares()
    self.wait(2.)
    self.mark_exit_squares()
    self.wait(2.)

    ## ADJACENCY EXAMPLE
    self.select_square(*INITIAL_POS)
    self.wait(2.)
    self.show_adjacent_squares(*INITIAL_POS)
    self.wait(2.)
    self.reset_adjacency_highlighting()
    self.wait(2.)
    self.show_reachable_adjacent_squares(*INITIAL_POS)
    self.wait(2.)
    self.reset_full_highlighting()
    self.wait(2.)

    ## DISTANCES
    distance_matrix = self.get_distance_matrix(*INITIAL_POS)
    dist_list = []
    for row in distance_matrix:
      dist_list += list(filter(lambda x : x is not None, row))
    max_dist = max(*dist_list)

    for dist in range(max_dist + 1):
      self.highlight_distance(dist, distance_matrix)
      self.wait(2.)

    self.reset_full_highlighting()

    self.end_animation()
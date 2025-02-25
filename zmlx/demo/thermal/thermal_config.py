# ** desc = '基于Seepage类的温度场计算'

import numpy as np

from zmlx.config import seepage
from zmlx.geometry.point_distance import point_distance
from zmlx.seepage_mesh.cube import create_cube


def create():
    return seepage.create(mesh=create_cube(np.linspace(0, 100, 100),
                                           np.linspace(0, 100, 100),
                                           (-0.5, 0.5)),
                          temperature=lambda *pos: 380 if point_distance(pos, (0, 0, 0)) < 30 else 280,
                          denc=1.0e6,
                          heat_cond=1.0,
                          dt_max=1.0e6,
                          texts={'solve': {'show_cells': {'dim0': 0, 'dim1': 1, 'show_p': False},
                                           'step_max': 500,
                                           }}
                          )


if __name__ == '__main__':
    model = create()
    seepage.solve(model, close_after_done=False)

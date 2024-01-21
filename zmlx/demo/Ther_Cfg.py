# ** desc = '基于Seepage类的温度场计算 （利用TherFlowConfig建模）'

import numpy as np

from zml import SeepageMesh
from zmlx.config import seepage
from zmlx.geometry.point_distance import point_distance
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy


def solve():
    model = seepage.create(mesh=SeepageMesh.create_cube(np.linspace(0, 100, 100),
                                                        np.linspace(0, 100, 100),
                                                        (-0.5, 0.5)),
                           temperature=lambda *pos: 380 if point_distance(pos, (0, 0, 0)) < 30 else 280,
                           denc=1.0e6, heat_cond=1.0, dt_max=1.0e6)

    for step in range(500):
        gui.break_point()
        seepage.iterate(model)
        if step % 50 == 0:
            print(f'step = {step}')
            tricontourf(as_numpy(model).cells.x, as_numpy(model).cells.y,
                        as_numpy(model).cells.get(model.get_cell_key('temperature')),
                        caption='temperature', gui_only=True)


if __name__ == '__main__':
    gui.execute(solve, close_after_done=False)

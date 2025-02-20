# ** desc = '单相流，两端固定压力，计算压力场'

import numpy as np

from zml import get_distance
from zmlx.config import seepage
from zmlx.fluid import h2o
from zmlx.seepage_mesh.cube import create_cube


def create():
    mesh = create_cube(x=np.linspace(0, 100, 100),
                       y=np.linspace(0, 50, 50),
                       z=[0, 1])
    x_min, x_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        return 1.0e10 if abs(x - x_max) < 0.1 or abs(x - x_min) < 0.1 else 0.2

    def get_p(x, y, z):
        if abs(x - x_min) < 0.1:
            return 3e6
        if abs(x - x_max) < 0.1:
            return 1e6
        else:
            return 2e6

    def get_k(x, y, z):
        return 0 if get_distance([x, y], [50, 25]) < 15 else 1e-14

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=[h2o.create(name='h2o', density=1000.0, viscosity=1.0e-3)],
                           porosity=get_fai, pore_modulus=200e6, p=get_p, s=1.0, perm=get_k)

    seepage.set_solve(model,
                      show_cells=dict(
                          dim0=0,
                          dim1=1,
                          show_t=False,
                          show_s=[],
                          cmap='jet'
                      ),
                      time_max=3600 * 24 * 30
                      )
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)

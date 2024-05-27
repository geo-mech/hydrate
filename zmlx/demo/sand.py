# ** desc = '砂浓度计算(正在测试，尚未完成)'

import numpy as np

from zml import Seepage
from zml import get_distance
from zmlx.config import seepage, sand
from zmlx.plt.tricontourf import tricontourf
from zmlx.seepage_mesh.cube import create_cube
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = create_cube(x=np.linspace(0, 100, 100),
                       y=np.linspace(0, 50, 50),
                       z=[0, 1])

    # 所有的流体的定义
    fludefs = [Seepage.FluDef.create(defs=[Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000, name='h2o'),
                                           Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000, name='flu_sand')],
                                     name='flu'),
               Seepage.FluDef(den=1000, vis=1e30, specific_heat=1000, name='sol_sand')
               ]

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

    def get_s(x, y, z):
        return {'h2o': 0.9, 'flu_sand': 0.1}

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=fludefs,
                           porosity=get_fai, pore_modulus=200e6, p=get_p, s=get_s, perm=get_k,
                           has_solid=True)

    seepage.set_solve(model,
                      show_cells={'dim0': 0, 'dim1': 1, 'show_t': False},
                      time_max=3600 * 24 * 365 * 3
                      )

    sand.add_setting(model, sol_sand='sol_sand', flu_sand='flu_sand',
                     v2q=[[0, 1e-6, 5e-6],
                          [-1, 0, 1]],
                     fid=0)
    return model


def show_vel(model: Seepage):
    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    v = model.get_cell_flu_vel(fid=0, last_dt=seepage.get_dt(model)).to_numpy()
    tricontourf(x, y, v, caption='Velocity')


def test_1():
    model = create()
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show_vel(model))


if __name__ == '__main__':
    test_1()

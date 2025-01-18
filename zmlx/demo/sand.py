# ** desc = '砂浓度计算(正在测试，尚未完成)'

import numpy as np

from zml import Seepage, Interp1
from zml import get_distance
from zmlx.config import seepage, sand
from zmlx.plt.tricontourf import tricontourf
from zmlx.seepage_mesh.cube import create_cube
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = create_cube(x=np.linspace(0, 50, 50),
                       y=np.linspace(0, 50, 50),
                       z=[0, 1])

    # 所有的流体的定义
    fludefs = [Seepage.FluDef.create(defs=[Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000, name='h2o'),
                                           Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000, name='flu_sand')],
                                     name='flu'),
               Seepage.FluDef(den=1000, vis=1e30, specific_heat=1000, name='sol_sand')
               ]

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        if abs(x - x_max) < 0.1 or abs(y - y_max) < 0.1:
            return 1e10
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 1e10
        else:
            return 0.2

    def get_p(x, y, z):
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 3e6
        else:
            return 1e6

    def get_k(x, y, z):
        return 1e-14

    def get_s(x, y, z):
        return {'h2o': 0.9, 'sol_sand': 0.1}

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=fludefs,
                           porosity=get_fai, pore_modulus=200e6, p=get_p, s=get_s, perm=get_k,
                           has_solid=True)

    seepage.set_solve(model,
                      show_cells={'dim0': 0, 'dim1': 1, 'show_t': False},
                      time_max=3600 * 24 * 365 * 30
                      )

    # 添加压力梯度到饱和度的映射.
    x0 = [0, 0.003, 0.01]
    y0 = [0, 0.0, 0.1]
    x1 = [0, 0.001, 0.01]
    y1 = [0, 0.0, 0.05]

    model.set_curve(index=0, curve=Interp1(x=x0, y=y0))
    model.set_curve(index=1, curve=Interp1(x=x1, y=y1))

    idx = model.reg_cell_key('i0')
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=0)

    idx = model.reg_cell_key('i1')
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=1)

    sand.add_setting(model, sol_sand='sol_sand', flu_sand='flu_sand',
                     ca_i0='i0', ca_i1='i1')

    return model


def show_stress(model: Seepage):
    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    v = sand.get_stress(model, fluid=[0])
    tricontourf(x, y, v, caption='stress')


def test_1():
    model = create()
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show_stress(model))


if __name__ == '__main__':
    test_1()

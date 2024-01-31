# ** desc = '测试：纵向二维。浮力作用下气体运移成藏过程模拟'


import numpy as np

from zml import SeepageMesh, get_distance
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.h2o import create as create_h2o
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui.GuiBuffer import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(0, 300, 150),
                                   y=(-0.5, 0.5),
                                   z=np.linspace(-500, 0, 250)
                                   )

    def get_initial_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_initial_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def get_initial_s(x, y, z):
        if get_distance((x, y, z), (150, 0, -400)) < 50:
            return {'ch4': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_perm(x, y, z):
        if abs(x - 150) < 20:
            return 1.0e-13
        else:
            return 1.0e-15

    model = seepage.create(mesh, porosity=0.1, pore_modulus=100e6, denc=get_denc, dist=0.1,
                           temperature=get_initial_t, p=get_initial_p, s=get_initial_s,
                           perm=get_perm, heat_cond=2.0,
                           fludefs=[create_ch4(name='ch4'), create_h2o(name='h2o')],
                           dt_max=3600 * 24, gravity=(0, 0, -10))

    return model


def show(model):
    """
    绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if gui.exists():
        title = f'plot when model.time={time2str(seepage.get_time(model))}'
        numpy = as_numpy(model)
        x, z = numpy.cells.x, numpy.cells.z
        p = numpy.cells.get(model.get_cell_key('pre'))
        tricontourf(x, z, p, caption='压力', title=title, xlabel='x / m', ylabel='z / m')
        s = numpy.fluids(0).vol / numpy.cells.fluid_vol
        tricontourf(x, z, s, caption='气饱和度', title=title, xlabel='x / m', ylabel='z / m')


def solve(model):
    """
    执行求解
    """
    iterate = GuiIterator(seepage.iterate, plot=lambda: show(model))
    for step in range(10000):
        iterate(model)
        if step % 10 == 0:
            print(f'step = {step}, dt = {seepage.get_dt(model, as_str=True)}, '
                  f'time = {seepage.get_time(model, as_str=True)}')

    show(model)
    print(iterate.time_info())


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done,
                args=(create(),), disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

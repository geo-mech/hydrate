# ** desc = '测试：纵向二维。重力驱动下的沉降过程'


import numpy as np

from zml import SeepageMesh, Seepage
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.config import settle
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui.GuiBuffer import gui
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(0, 300, 75),
                                   y=(-0.5, 0.5),
                                   z=np.linspace(-500, 0, 125)
                                   )
    model = seepage.create(mesh, porosity=0.1, pore_modulus=100e6, denc=1.0e6, dist=0.1,
                           temperature=280, p=1e6, s={'sand': 0.5, 'h2o': 0.5},
                           perm=1.0e-13, heat_cond=2.0,
                           fludefs=[Seepage.FluDef(name='sand', den=3000.0),
                                    Seepage.FluDef(name='h2o', den=1000.0)],
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
        s = numpy.fluids(0).vol / numpy.cells.fluid_vol
        tricontourf(x, z, s, caption='饱和度', title=title, xlabel='x / m', ylabel='z / m')


def solve(model):
    """
    执行求解
    """
    for step in range(1000000):
        gui.break_point()
        settle.iterate(model, dt=10000, fid0=0, fid1=1, rate=1.0e-6)
        if step % 10 == 0:
            print(f'step = {step}, dt = {seepage.get_dt(model, as_str=True)}, '
                  f'time = {seepage.get_time(model, as_str=True)}')
            show(model)
    show(model)


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done,
                args=(create(),), disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

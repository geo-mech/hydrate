# ** desc = '单相流，两端固定压力，计算压力场'

from zml import *
from zmlx.ui.GuiBuffer import gui
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.fluid import h2o
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.plt.tricontourf import tricontourf
import numpy as np


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(0, 100, 100),
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

    return model


def show(model):
    if gui.exists():
        tricontourf(model.numpy.cells.x, model.numpy.cells.y, model.numpy.cells.pre,
                    caption='pressure', title=f'time = {time2str(seepage.get_time(model))}')


def solve(model):
    solver = ConjugateGradientSolver(tolerance=1.0e-14)
    iterate = GuiIterator(seepage.iterate, lambda: show(model))

    while seepage.get_time(model) < 3600 * 24 * 30:
        iterate(model, solver=solver)
        step = seepage.get_step(model)
        if step % 10 == 0:
            print(f'step = {step}, dt = {time2str(seepage.get_dt(model))}, time = {time2str(seepage.get_time(model))}')

    show(model)


def _test1():
    model = create()
    solve(model)


if __name__ == '__main__':
    gui.execute(_test1, close_after_done=False)

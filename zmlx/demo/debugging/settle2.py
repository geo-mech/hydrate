# ** desc = '测试：流动以及sand的沉降'

import numpy as np

from zml import SeepageMesh, ConjugateGradientSolver, Seepage
from zmlx.alg.time2str import time2str
from zmlx.config import seepage, settle
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui.GuiBuffer import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(0, 100, 100),
                                   y=np.linspace(0, 50, 50),
                                   z=[0, 1])
    x_min, x_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        return 1.0e20 if abs(x - x_max) < 0.1 else 0.2

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=[Seepage.FluDef(name='h2o', den=1000.0, vis=1.0e-3),
                                    Seepage.FluDef(name='sand', den=2000.0, vis=1.0e-2)],
                           porosity=get_fai,
                           pore_modulus=200e6, p=1e6, s=[1, 0], perm=1e-13, gravity=[0, -10, 0])

    pos = [x_min, 25, 0]
    cell = model.get_nearest_cell(pos=pos)
    model.add_injector(fluid_id=0, flu=cell.get_fluid(0).get_copy(), pos=pos, radi=2, value=0.8e-4)
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1).get_copy(), pos=pos, radi=2, value=0.2e-4)

    return model


def show(model):
    if gui.exists():
        numpy = as_numpy(model)
        x = numpy.cells.x
        y = numpy.cells.y
        tricontourf(x, y, numpy.cells.pre,
                    caption='pressure', title=f'time = {time2str(seepage.get_time(model))}')
        tricontourf(x, y, numpy.fluids(1).vol / numpy.cells.fluid_vol,
                    caption='v1', title=f'time = {time2str(seepage.get_time(model))}')


def solve(model):
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    iterate = GuiIterator(seepage.iterate, lambda: show(model))

    while seepage.get_time(model) < 3600 * 24 * 3000:
        iterate(model, solver=solver)
        dt = seepage.get_dt(model)
        settle.iterate(model, dt=dt, fid0=1, fid1=0, rate=5.0e-7)
        step = seepage.get_step(model)
        if step % 10 == 0:
            print(f'step = {step}, dt = {time2str(seepage.get_dt(model))}, time = {time2str(seepage.get_time(model))}')

    show(model)


def _test1():
    model = create()
    solve(model)


if __name__ == '__main__':
    gui.execute(_test1, close_after_done=False)

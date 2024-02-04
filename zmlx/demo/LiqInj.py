# ** desc = '两相流，流体注入驱替'

import numpy as np

from zml import SeepageMesh, Seepage
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator


def create():
    mesh = SeepageMesh.create_cube(np.linspace(0, 100, 101),
                                   np.linspace(0, 100, 101), (-0.5, 0.5))

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x0) < 0.1 or abs(x - x1) < 0.1 or abs(y - y0) < 0.1 or abs(y - y1) < 0.1:
            cell.vol = 1.0e8

    model = seepage.create(mesh, porosity=0.2, pore_modulus=100e6, p=1e6, temperature=280,
                           s=(1, 0), perm=1e-14, disable_update_den=True,
                           disable_update_vis=True, disable_ther=True,
                           disable_heat_exchange=True,
                           fludefs=[Seepage.FluDef(den=50, vis=1.0e-4),
                                    Seepage.FluDef(den=1000, vis=1.0e-3)])

    cell = model.get_nearest_cell((50, 50, 0))
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1), pos=cell.pos, radi=0.1, opers=[(0, 1.0e-5)])

    seepage.set_dt_max(model, 3600 * 24)

    return model


def show(model):
    kwargs = {'gui_only': True, 'title': f'plot when model.time={time2str(seepage.get_time(model))}'}
    xy = [c.pos[0] for c in model.cells], [c.pos[1] for c in model.cells]
    tricontourf(*xy, [c.pre for c in model.cells], caption='压力', **kwargs)
    for i in range(2):
        tricontourf(*xy, [c.get_fluid(i).vol_fraction for c in model.cells], caption=f'饱和度{i}', **kwargs)


def solve(model):
    iterate = GuiIterator(iterate=seepage.iterate, plot=lambda: show(model))

    while seepage.get_time(model) < 365 * 24 * 3600:
        r = iterate(model)
        step = seepage.get_step(model)
        if step % 10 == 0:
            dt, t = time2str(seepage.get_dt(model)), time2str(seepage.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {t}, report={r}')


def execute(gui_mode=True, close_after_done=False):
    gui.execute(lambda: solve(create()), close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

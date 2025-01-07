# ** desc = '基于Seepage类的温度场计算'
"""
x = linspace(0, 1, 100);
T0 = 0;
T1 = 1;
alpha = 1;
figure
for t = linspace(0, 0.1, 10)
    T = T1 + (T0-T1)*erf(x./(2.*(alpha*t)^0.5));
    plot(x, T);
    hold on
end
"""

import numpy as np

from zml import Seepage
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy
from zmlx.plt.plotxy import plotxy


class CellAttrs:
    temperature = 0
    mc = 1


class FaceAttrs:
    g_heat = 0


def create():
    model = Seepage()
    mesh = create_cube(np.linspace(0, 100, 100), (-0.5, 0.5), (-0.5, 0.5))
    x0, x1 = mesh.get_pos_range(0)

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        x = c.pos[0]
        cell.set_attr(CellAttrs.temperature,
                      380 if abs(x-x0)<0.1 else 280)
        cell.set_attr(CellAttrs.mc, 1.0e20 * c.vol if abs(x-x0)<0.1 else 1.0e6 * c.vol)

    for f in mesh.faces:
        face = model.add_face(model.get_cell(f.link[0]), model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.0 / f.length)

    return model


def show(model):
    ada = as_numpy(model)
    plotxy(ada.cells.x, ada.cells.get(CellAttrs.temperature), caption='temperature', gui_only=True)


def solve(model):
    for step in range(500):
        gui.break_point()
        model.iterate_thermal(dt=1.0e6, ca_t=CellAttrs.temperature, ca_mc=CellAttrs.mc,
                              fa_g=FaceAttrs.g_heat)
        if step % 1 == 0:
            show(model)
            print(f'step = {step}')


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done, args=(create(),), disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

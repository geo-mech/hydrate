# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


class CellAttrs:
    temperature = 0
    mc = 1


class FaceAttrs:
    g_heat = 0


def create():
    model = Seepage()
    mesh = create_cube(
        np.linspace(-50, 50, 50),
        np.linspace(-50, 50, 50),
        (-0.5, 0.5))

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        cell.set_attr(CellAttrs.temperature,
                      380 if point_distance(c.pos, (0, 0, 0)) < 30 else 280)
        cell.set_attr(CellAttrs.mc, 1.0e6 * c.vol)

    for f in mesh.faces:
        face = model.add_face(
            model.get_cell(f.link[0]),
            model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.0 / f.length)

    return model


def show(model):
    tricontourf(seepage.get_x(model), seepage.get_y(model),
                seepage.get_ca(model, CellAttrs.temperature), caption='temperature',
                xlabel='x (m)', ylabel='y (m)', clabel='temperature (K)')


def solve(model):
    for step in range(500):
        gui.break_point()
        model.iterate_thermal(
            dt=1.0e6, ca_t=CellAttrs.temperature,
            ca_mc=CellAttrs.mc,
            fa_g=FaceAttrs.g_heat)
        if step % 50 == 0:
            show(model)
            print(f'step = {step}')


if __name__ == '__main__':
    gui.execute(solve, close_after_done=False, args=(create(),))

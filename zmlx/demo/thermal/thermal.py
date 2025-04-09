# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


class CellAttrs:
    temperature = 0
    mc = 1


class FaceAttrs:
    g_heat = 0


def create():
    model = Seepage()
    mesh = create_cube(np.linspace(0, 100, 100), np.linspace(0, 100, 100),
                       (-0.5, 0.5))

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        cell.set_attr(CellAttrs.temperature,
                      380 if point_distance(c.pos, (0, 0, 0)) < 30 else 280)
        cell.set_attr(CellAttrs.mc, 1.0e6 * c.vol)

    for f in mesh.faces:
        face = model.add_face(model.get_cell(f.link[0]),
                              model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.0 / f.length)

    return model


def show(model):
    ada = as_numpy(model)
    tricontourf(ada.cells.x, ada.cells.y,
                ada.cells.get(CellAttrs.temperature), caption='temperature',
                gui_only=True)


def solve(model):
    for step in range(500):
        gui.break_point()
        model.iterate_thermal(dt=1.0e6, ca_t=CellAttrs.temperature,
                              ca_mc=CellAttrs.mc,
                              fa_g=FaceAttrs.g_heat)
        if step % 50 == 0:
            show(model)
            print(f'step = {step}')


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done, args=(create(),),
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

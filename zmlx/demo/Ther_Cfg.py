# ** desc = '基于Seepage类的温度场计算 （利用TherFlowConfig建模）'

from zmlx import *
from zmlx.config import seepage


def solve():
    model = seepage.create(mesh=SeepageMesh.create_cube(np.linspace(0, 100, 100),
                                                        np.linspace(0, 100, 100),
                                                        (-0.5, 0.5)),
                           temperature=lambda *pos: 380 if get_distance(pos, (0, 0, 0)) < 30 else 280,
                           denc=1.0e6, heat_cond=1.0, dt_max=1.0e6)

    for step in range(500):
        gui.break_point()
        seepage.iterate(model)
        if step % 50 == 0:
            print(f'step = {step}')
            tricontourf(model.numpy.cells.x, model.numpy.cells.y,
                        model.numpy.cells.get(model.get_cell_key('temperature')),
                        caption='temperature', gui_only=True)


if __name__ == '__main__':
    gui.execute(solve, close_after_done=False)

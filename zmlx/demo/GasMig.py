# ** desc = '测试：纵向二维。浮力作用下气体运移成藏过程模拟'

from zmlx import *
from zmlx.config import seepage


def create():
    mesh = SeepageMesh.create_cube(np.linspace(0, 300, 150),
                                   np.linspace(0, 500, 250),
                                   (-0.5, 0.5))

    def get_initial_t(x, y, z):
        return 278 + 22.15 - 0.0443 * y

    def get_initial_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * y

    def get_initial_s(x, y, z):
        if get_distance((x, y, z), (150, 100, 0)) < 50:
            return 1, 0
        else:
            return 0, 1

    y0, y1 = mesh.get_pos_range(1)

    def get_denc(x, y, z):
        if abs(y - y0) < 0.1 or abs(y - y1) < 0.1:
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
                           fludefs=[create_ch4(), create_h2o()],
                           dt_max=3600 * 24, gravity=(0, -10, 0))

    return model


def show(model):
    """
    绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if gui.exists():
        x, y = [cell.pos[0] for cell in model.cells], [cell.pos[1] for cell in model.cells]
        title = f'plot when model.time={time2str(seepage.get_time(model))}'
        tricontourf(x, y, [c.get_attr(model.get_cell_key('pre')) for c in model.cells],
                    caption='压力', title=title)
        tricontourf(x, y, [c.get_fluid(0).vol_fraction for c in model.cells],
                    caption='气饱和度', title=title)


def solve(model):
    """
    执行求解
    """
    iterate = GuiIterator(seepage.iterate, plot=lambda: show(model))
    for step in range(10000):
        iterate(model)
        if step % 10 == 0:
            dt = time2str(seepage.get_dt(model))
            time = time2str(seepage.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {time}')

    show(model)
    information('计算结束', iterate.time_info())


def execute(gui_mode=True, close_after_done=False):
    model = create()
    if gui_mode:
        gui.execute(solve, close_after_done=close_after_done,
                    args=(model,))
    else:
        solve(model)


if __name__ == '__main__':
    execute()

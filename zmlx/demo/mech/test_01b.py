# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到向下的面力'

from zmlx import *
from zmlx.fem import xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    # 定义矩形区域的边界
    X_MIN = 0
    X_MAX = 3
    Y_MIN = 0
    Y_MAX = 1

    mesh = layered_triangles(X_MIN, X_MAX, 30, Y_MIN, Y_MAX, 10, as_mesh=True)

    face_n = mesh.face_number

    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    for i in range(mesh.node_number):
        x = mesh.get_node(i).pos[0]
        if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
        if x > 2.99:  # 对于右侧的node，添加一个纵向的压力
            f = model.get_p2f(i * 2 + 1)
            f.c -= 1e3

    model.iterate(dt=1)

    def on_figure(fig):
        dx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        dy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        vx = [mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        vy = [mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    plot(on_figure, gui_mode=True)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

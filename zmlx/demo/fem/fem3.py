# ** desc = '三维有限元模型'

import numpy as np

from zml import Mesh3, ConjugateGradientSolver
from zmlx.fem.create3 import create3
from zmlx.plt.contourf import contourf
from zmlx.ui import gui


def create_mesh():
    return Mesh3.create_cube(x1=-0.5, y1=-50, z1=-50,
                             x2=+0.5, y2=+50, z2=+50,
                             dx=1, dy=5, dz=5)


def create(mesh):
    """
    根据mesh创建模型
    """
    assert isinstance(mesh, Mesh3)
    model = create3(mesh)

    for link in mesh.links:
        assert isinstance(link, Mesh3.Link)
        x0, y0, z0 = link.get_node(0).pos
        x1, y1, z1 = link.get_node(1).pos
        if abs(z0 - z1) > 0.5:
            if (z0 ** 2 + y0 ** 2) ** 0.5 < 10:
                i0 = link.get_node(0).index
                i1 = link.get_node(1).index
                if z0 < z1:
                    p2f = model.get_p2f(i0 * 3 + 2)
                    p2f.c = p2f.c - 0.1
                    p2f = model.get_p2f(i1 * 3 + 2)
                    p2f.c = p2f.c + 0.1
                else:
                    p2f = model.get_p2f(i0 * 3 + 2)
                    p2f.c = p2f.c + 0.1
                    p2f = model.get_p2f(i1 * 3 + 2)
                    p2f.c = p2f.c - 0.1
    return model


def show(model, mesh, caption=None):
    """
    绘图
    """
    assert isinstance(mesh, Mesh3)
    if gui.exists():
        vy = []
        vz = []
        dz = []
        for node_id in range(int(mesh.node_number / 2)):
            vy.append(model.get_pos(node_id * 3 + 1))
            vz.append(model.get_pos(node_id * 3 + 2))
            z0 = mesh.get_node(node_id).pos[2]
            dz.append(model.get_pos(node_id * 3 + 2) - z0)
        contourf(x=np.reshape(vy, [21, 21]),
                 y=np.reshape(vz, [21, 21]),
                 z=np.reshape(dz, [21, 21]), caption=caption)


def solve(model, mesh):
    """
    求解给定的模型
    """
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    model.iterate(dt=1000, solver=solver)
    show(model, mesh, caption='step0')
    model.iterate(dt=1000, solver=solver)
    show(model, mesh, caption='step1')


def execute(gui_mode=True, close_after_done=False):
    """
    主函数
    """
    mesh = create_mesh()
    model = create(mesh=mesh)
    gui.execute(func=solve, args=[model, mesh],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

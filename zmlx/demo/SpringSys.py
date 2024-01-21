# ** desc = '基于弹簧系统计算应力的传播'

import numpy as np

from zml import SpringSys, ConjugateGradientSolver, DynSys
from zmlx.data import mesh_c10000 as data
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui import gui


def create_model(triangles, x, y):
    """
    创建一个模型
    """
    model = SpringSys()
    virtual_nodes = []
    for i in range(len(x)):
        node = model.add_node(pos=(x[i], y[i], 0), vel=(0, 0, 0),
                              mass=1 if np.linalg.norm([x[i], y[i]]) < 0.48 else 1.0e10,
                              force=(0, 0, 0))
        virtual_nodes.append(model.add_virtual_node(node=node))
    for tri in triangles:
        tri_x = (x[tri[0]] + x[tri[1]] + x[tri[2]]) / 3
        tri_y = (y[tri[0]] + y[tri[1]] + y[tri[2]]) / 3
        links = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for link in links:
            x0, y0, x1, y1 = x[link[0]], y[link[0]], x[link[1]], y[link[1]]
            dist = np.linalg.norm(np.array([x0, y0]) - np.array([x1, y1]))
            spr = model.add_spring(virtual_nodes=[virtual_nodes[inode] for inode in link], len0=dist, k=1)
            if np.linalg.norm([tri_x, tri_y]) < 0.2:
                spr.len0 *= 1.01
    return model


def main():
    model = create_model(data.tri, data.x, data.y)
    print(model)

    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    for i in range(500):
        gui.break_point()
        model.modify_pos(2, 0, 0)
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        model.modify_vel(0.99)
        if i % 10 == 0:
            print(i)
            dp = np.array([node.pos for node in model.nodes]) - p0
            tricontourf(x=data.x, y=data.y, z=(dp[:, 0] ** 2 + dp[:, 1] ** 2) ** 0.5, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, keep_cwd=True, close_after_done=False)

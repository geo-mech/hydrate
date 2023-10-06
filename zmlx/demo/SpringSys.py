# ** desc = '基于弹簧系统计算应力的传播'

from zmlx import *
from zmlx.data.mesh_c10000 import x, y, tri
import math


def plot(z):
    def f(fig):
        ax = fig.subplots()
        ax.set_aspect('equal')
        cntr2 = ax.tricontourf(x, y, z, levels=20, cmap="coolwarm")
        fig.colorbar(cntr2, ax=ax)

    zml.plot(f, clear=True, caption='位移场')


def get_norm(x, y):
    return math.sqrt(x * x + y * y)


def create_model(triangles, x, y):
    """
    创建一个模型
    """
    model = zml.SpringSys()
    virtual_nodes = []
    for i in range(len(x)):
        node = model.add_node(pos=(x[i], y[i], 0), vel=(0, 0, 0), mass=1 if get_norm(x[i], y[i]) < 0.48 else 1.0e10,
                              force=(0, 0, 0))
        virtual_nodes.append(model.add_virtual_node(node=node))
    for tri in triangles:
        tri_x = (x[tri[0]] + x[tri[1]] + x[tri[2]]) / 3
        tri_y = (y[tri[0]] + y[tri[1]] + y[tri[2]]) / 3
        links = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for link in links:
            x0, y0, x1, y1 = x[link[0]], y[link[0]], x[link[1]], y[link[1]]
            dist = math.sqrt(math.pow(x0 - x1, 2) + math.pow(y0 - y1, 2))
            spr = model.add_spring(virtual_nodes=[virtual_nodes[inode] for inode in link], len0=dist, k=1)
            if get_norm(tri_x, tri_y) < 0.2:
                spr.len0 *= 1.01
    return model


def get_node_pos(model):
    disp = np.zeros(shape=(model.node_number, 3))
    for i in range(model.node_number):
        disp[i] = model.get_node(i).pos
    return disp


def main():
    model = create_model(tri, x, y)
    print(model)

    p0 = get_node_pos(model)

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    for i in range(500):
        gui.break_point()
        model.modify_pos(2, 0, 0)
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        model.modify_vel(0.99)
        if i % 10 == 0:
            print(i)
            dp = get_node_pos(model) - p0
            plot(np.sqrt(dp[:, 0] * dp[:, 0] + dp[:, 1] * dp[:, 1]))


if __name__ == '__main__':
    gui(main, keep_cwd=True, close_after_done=False)

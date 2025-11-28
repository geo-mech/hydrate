# ** desc = '动态的有限元计算：应力波的传递过程-3'

from zmlx import *
from zmlx.data import mesh_c10000 as data


def create_model(triangles, x, y):
    """
    创建一个模型
    """
    model = SpringSys()
    virtual_nodes = []

    points = [(0, -0.3), (0, -0.1), (0, 0.1), (0, 0.3)]
    for i in range(len(x)):
        v = [0, 0, 0]
        for c in points:
            r = max(get_distance([x[i], y[i]], c), 0.001)
            if r < 0.05:
                v = [(x[i] - c[0]) / r, (y[i] - c[1]) / r, 0]
        node = model.add_node(
            pos=(x[i], y[i], 0),
            vel=v,
            mass=1,
            force=(0, 0, 0))
        virtual_nodes.append(model.add_virtual_node(node=node))
    for tri in triangles:
        links = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for link in links:
            x0, y0, x1, y1 = x[link[0]], y[link[0]], x[link[1]], y[link[1]]
            dist = np.linalg.norm(np.array([x0, y0]) - np.array([x1, y1]))
            model.add_spring(
                virtual_nodes=[virtual_nodes[inode] for inode in link],
                len0=dist, k=1)
    return model


def main():
    model = create_model(data.tri, data.x, data.y)
    print(model)

    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    for i in range(150):
        gui.break_point()
        model.modify_pos(2, 0, 0)
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        # model.modify_vel(0.999999)
        if i % 10 == 0:
            print(i)
            dp = np.array([node.pos for node in model.nodes]) - p0
            tricontourf(
                x=data.x, y=data.y,
                z=(dp[:, 0] ** 2 + dp[:, 1] ** 2) ** 0.5,
                caption='位移场', tight_layout=True
            )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

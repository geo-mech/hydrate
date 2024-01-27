# ** desc = '二维有限元模型(两个三角形有两个顶点固定，另外两个顶点振动过程)'

from zml import Mesh3, ConjugateGradientSolver
from zmlx.ui import gui
from zmlx.plt.tricontourf import tricontourf
from zmlx.fem.create2 import create2


def create_mesh():
    """
    创建mesh
    """
    mesh = Mesh3()

    # 添加node
    nodes = [mesh.add_node(*pos) for pos in [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (1.5, 1, 0)]]

    # 添加link和face
    for triangle in [(0, 1, 2), (1, 2, 3)]:
        n0 = nodes[triangle[0]]
        n1 = nodes[triangle[1]]
        n2 = nodes[triangle[2]]
        mesh.add_face([mesh.add_link([n0, n1]), mesh.add_link([n1, n2]), mesh.add_link([n2, n0])])

    return mesh


def create(mesh):
    """
    根据mesh创建模型
    """
    model = create2(mesh)

    # 增大质量，以确保位置不变
    for idx in [0, 1, 3]:
        model.set_mas(idx, model.get_mas(idx) * 1.0e20)

    # 修改初始位置，打破平衡状态
    idx = 3 * 2  # 第3个node的x
    model.set_pos(idx, model.get_pos(idx) + 0.2)

    return model


def show(model, mesh):
    """
    绘图
    """
    if gui.exists():
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        tricontourf(x=vx, y=vy, z=dx, caption='x位移', clabel='displacement x')


def solve(model, mesh):
    """
    求解给定的模型
    """
    solver = ConjugateGradientSolver(tolerance=1.0e-15)
    for step in range(5000):
        gui.break_point()
        print(f'step = {step}')
        model.iterate(dt=0.1, solver=solver)
        if step % 20 == 0:
            show(model, mesh)


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

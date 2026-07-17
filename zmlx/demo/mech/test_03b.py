# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到面力作用(力的方向向左)。和上一个case的差异：设置较小的时间步长，计算动态的应力波传递的过程'
#
# 【详细说明】
# 本案例是test_03.py的对应版本，模拟完全相同的动态应力波传播问题，
# 但使用zmlx.fem.xy模块的高级API（xy.create_dyn）来实现。
#
# 对比test_03.py（低级API）和test_03b.py（高级API）可以看出：
#   1. 高级API（xy.create_dyn）将材料属性设置和刚度矩阵计算合并为一行代码
#   2. 高级API不需要显式创建ConjugateGradientSolver（使用默认求解器）
#   3. 两种API在求解精度和效率上是等价的

from zmlx import *
from zmlx.fem import xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：使用xy.create_dyn高级API创建模型，进行动态应力波传播模拟。

    与test_03.py的差异：使用高级API简化建模流程，不显式指定求解器，
    其余物理设置和求解参数保持一致（dt=0.0001，200步）。
    """
    # 定义矩形区域的边界 [m]
    X_MIN = 0
    X_MAX = 3
    Y_MIN = 0
    Y_MAX = 1

    # 生成结构化三角形网格
    mesh = layered_triangles(X_MIN, X_MAX, 30, Y_MIN, Y_MAX, 10, as_mesh=True)

    # 获取面的数量，用于创建材料属性列表
    face_n = mesh.face_number

    # 使用xy.create_dyn高级API创建动力学系统
    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    # 施加边界条件和载荷
    for i in range(mesh.node_number):
        x = mesh.get_node(i).pos[0]
        if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变（固定边界）
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
        if x > 2.99:  # 对于右侧的node，添加一个横向（x方向）向左的压力
            f = model.get_p2f(i * 2)
            f.c -= 1e3

    # 保存初始节点坐标（用于后续计算位移变化量）
    vx = [mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
    vy = [mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

    def on_figure(fig):
        """
        绘制位移场云图的回调函数。

        Args:
            fig: matplotlib图形对象
        """
        dx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        dy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    def solve():
        """
        动态求解过程：使用小时间步长推进200步，模拟应力波传播。

        与test_03.py不同，此处不显式指定求解器，使用model.iterate的默认设置。
        """
        for step in range(200):
            print(f'第{step}步')
            model.iterate(dt=0.0001)
            plot(on_figure, caption='位移场')

    gui.execute(solve, close_after_done=False)


if __name__ == '__main__':
    main()

# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到向左(和上一个case相比，仅仅改变力的方向)的面力'
#
# 【详细说明】
# 本案例是test_02.py的对应版本，模拟完全相同的物理问题（左侧固定，右侧受到向左的力），
# 但使用zmlx.fem.xy模块的高级API（xy.create_dyn）来实现，代码更加简洁。
# 与test_01b.py类似，展示了高级API在简化建模流程方面的优势。

from zmlx import *
from zmlx.fem import xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：使用xy.create_dyn高级API创建模型，施加向左的载荷并求解。

    与test_02.py的区别：使用xy.create_dyn替代手动调用compute_face_stiff2和FemAlg.create2。
    载荷施加在x方向自由度上（i*2），模拟水平向左的压缩。
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

    # 使用共轭梯度求解器执行静态求解
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    model.iterate(dt=1, solver=solver)

    def on_figure(fig):
        """
        绘制位移场云图的回调函数。

        Args:
            fig: matplotlib图形对象
        """
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
    main()

# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到向下的面力'
#
# 【详细说明】
# 本案例与test_01.py模拟相同的物理问题（3m × 1m矩形弹性体，左侧固定，右侧受到向下的面力），
# 但采用不同的实现方式：使用zmlx.fem.xy模块的高级API（xy.create_dyn）来创建动力学模型，
# 避免了手动设置单元属性和计算刚度矩阵的步骤，使代码更加简洁。
#
# 展示了zmlx.fem.xy模块的使用方法，该模块封装了常见的二维弹性力学建模流程。

from zmlx import *
from zmlx.fem import xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：创建网格、组装模型、施加边界条件和载荷、求解并可视化。

    通过xy.create_dyn一行代码即可完成单元刚度计算和系统组装，
    与test_01.py中手动调用compute_face_stiff2和FemAlg.create2的方式形成对比。
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
    # 该函数内部自动完成：单元刚度计算、质量矩阵组装、系统初始化
    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    # 施加边界条件和载荷（与test_01.py相同）
    for i in range(mesh.node_number):
        x = mesh.get_node(i).pos[0]
        if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变（固定边界）
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
        if x > 2.99:  # 对于右侧的node，添加一个纵向（y方向）向下的压力
            f = model.get_p2f(i * 2 + 1)
            f.c -= 1e3

    # 执行一个时间步的静态求解（不指定solver时使用默认求解器）
    model.iterate(dt=1)

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
    gui.execute(main, close_after_done=False)

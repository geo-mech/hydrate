# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到面力作用(力的方向向左)。和上一个case的差异：设置较小的时间步长，计算动态的应力波传递的过程'
#
# 【详细说明】
# 本案例与test_02.py模拟相同的物理设置（左侧固定，右侧受到向左的力），
# 但采用动态求解策略：使用很小的固定时间步长（dt=0.0001），推进200步，
# 从而捕捉应力波从右侧向左侧传播的瞬态过程。
#
# 与test_02.py的静态求解不同，动态求解能够展示弹性体中应力波传播的完整过程：
#   - 载荷在右侧边界突然施加时产生压缩波
#   - 压缩波沿x方向向左传播，到达固定边界后发生反射
#   - 通过观察不同时刻的位移场，可以直观理解波的传播和反射现象
#
# 关键建模参数：时间步长dt=0.0001s，共推进200步，总模拟时间0.02s

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：创建网格、组装模型、施加边界条件，并进行动态应力波传播模拟。

    与test_02.py的区别：使用小时间步长（dt=0.0001）进行200步的动态推进，
    而非单步静态求解。每一步都更新可视化，展示应力波的传播过程。
    """
    # 定义矩形区域的边界 [m]
    X_MIN = 0
    X_MAX = 3
    Y_MIN = 0
    Y_MAX = 1

    # 生成结构化三角形网格
    mesh = layered_triangles(X_MIN, X_MAX, 30, Y_MIN, Y_MAX, 10, as_mesh=True)

    # Mesh的face的自定义属性的ID
    fa_ym = 0    # 杨氏模量 [Pa]
    fa_mu = 1    # 泊松比 [无量纲]
    fa_den = 2   # 密度 [kg/m^3]
    fa_h = 3     # 厚度 [m]

    # 为每个三角形单元设置材料属性
    for face in mesh.faces:
        face.set_attr(fa_ym, 1.0e9)  # 杨氏模量: 1 GPa
        face.set_attr(fa_mu, 0.2)    # 泊松比: 0.2
        face.set_attr(fa_den, 1000.0) # 密度: 1000 kg/m^3
        face.set_attr(fa_h, 1.0)     # 厚度: 1 m

    # 计算每个三角形单元的刚度矩阵
    face_stiffs = compute_face_stiff2(
        mesh, fa_E=fa_ym, fa_mu=fa_mu,
        fa_h=fa_h)

    # 组装全局动力学系统
    model = FemAlg.create2(
        mesh=mesh, fa_den=fa_den, fa_h=fa_h,
        face_stiffs=face_stiffs)

    # 施加边界条件和载荷
    for i in range(mesh.node_number):
        x = mesh.get_node(i).pos[0]
        if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变（固定边界）
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
        if x > 2.99:  # 对于右侧的node，添加一个横向（x方向）向左的压力
            f = model.get_p2f(i * 2)
            f.c -= 1e3

    def on_figure(fig):
        """
        绘制位移场云图的回调函数。

        Args:
            fig: matplotlib图形对象
        """
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        dy = [vy[i] - mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    def solve():
        """
        动态求解过程：使用小时间步长推进200步，模拟应力波传播。

        每个时间步dt=0.0001s，使用共轭梯度求解器求解隐式动力学方程。
        每一步都更新位移场可视化，展示波从右侧向左传播的瞬态过程。
        """
        for step in range(200):
            print(f'第{step}步')
            solver = ConjugateGradientSolver(tolerance=1.0e-30)
            model.iterate(dt=0.0001, solver=solver)
            plot(on_figure, gui_mode=True, caption='位移场')

    gui.execute(solve, close_after_done=False)


if __name__ == '__main__':
    main()

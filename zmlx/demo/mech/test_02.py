# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到向左(和上一个case相比，仅仅改变力的方向)的面力'
#
# 【详细说明】
# 本案例与test_01.py模拟相同的网格和边界条件，唯一的区别是力的方向：
# test_01.py中右侧受到向下的力（y方向），本案例中右侧受到向左的力（x方向）。
#
# 通过对比两个案例的位移场，可以直观地理解不同方向载荷对弹性体变形的影响：
#   - 向下载荷主要产生弯曲变形（y方向位移为主）
#   - 向左载荷主要产生压缩变形（x方向位移为主）
#
# 建模技术与test_01.py相同，采用compute_face_stiff2 + FemAlg.create2的低级API。

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：创建网格、组装模型、施加边界条件和载荷、求解并可视化。

    与test_01.py的区别：载荷施加在x方向自由度（索引i*2）上，而非y方向（i*2+1）。
    右侧节点受到向左的集中力（x方向负向），模拟水平压缩。
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
            f = model.get_p2f(i * 2)  # i*2 表示x方向自由度的节点力
            f.c -= 1e3    # 施加向左的集中力（负号表示向左）

    # 创建共轭梯度求解器，执行一个时间步的静态求解
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    model.iterate(dt=1, solver=solver)

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

    plot(on_figure, gui_mode=True)


if __name__ == '__main__':
    main()

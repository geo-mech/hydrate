# ** desc = '对于3m*1m的矩形的区域(在中间添加挖空区，计算挖空之后的位移变化)'
#
# 【详细说明】
# 本案例模拟一个3m × 1m的矩形弹性体，计算中心区域材料弱化（模拟挖空）前后的位移场变化。
# 模型边界条件为：
#   - 左右边界：x方向位移固定（铰支）
#   - 底部边界：y方向位移固定（滑动支座）
#   - 顶部边界：施加均匀向下的压力（分布荷载）
#
# 计算流程分为三个阶段：
#   1. 原始状态：所有单元杨氏模量为1e9 Pa，计算初始位移场
#   2. 挖空状态：将中心区域（1.3<x<1.7, 0.4<y<0.6）的杨氏模量折减为1e7 Pa
#      （降低两个数量级），重新计算位移场
#   3. 位移变化量：计算挖空前后位移场的差值，直观显示挖空区域的影响
#
# 该方法可以用于模拟隧道开挖、洞穴形成等地质工程问题中的变形分析。

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：模拟矩形弹性体中心挖空前后的位移场变化。

    分三个阶段：1) 计算原始位移场；2) 折减中心区域杨氏模量，计算挖空位移场；
    3) 计算并显示位移场的变化量。
    """
    # 定义矩形区域的边界 [m]
    x_min = 0
    x_max = 3
    y_min = 0
    y_max = 1

    # Mesh的face的自定义属性的ID
    fa_ym = 0    # 杨氏模量 [Pa]
    fa_mu = 1    # 泊松比 [无量纲]
    fa_den = 2   # 密度 [kg/m^3]
    fa_h = 3     # 厚度 [m]

    # 生成较密的三角形网格（100×30）
    mesh = layered_triangles(x_min, x_max, 100, y_min, y_max, 30, as_mesh=True)

    # ========================
    # 阶段1：建模并计算原始的位移场
    # ========================

    # 设置所有单元的材料属性
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

    # 施加边界条件
    for i in range(mesh.node_number):
        x, y = mesh.get_node(i).pos[0], mesh.get_node(i).pos[1]
        if x < 0.01 or x > x_max - 0.01:  # 左右的node，固定x方向的位移（铰支）
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            continue
        if y < 0.01:  # 底部，固定y方向的位移（滑动支座）
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
            continue

    # 在顶部所有节点施加向下的压力（模拟重力或上覆载荷）
    for i in range(mesh.node_number):
        f = model.get_p2f(i * 2 + 1)  # y方向自由度
        f.c -= 1e2                      # 向下的集中力

    # 执行静态求解
    solver = ConjugateGradientSolver(tolerance=1.0e-30)
    model.iterate(dt=1, solver=solver)

    def on_figure(fig):
        """
        绘制位移场云图（阶段1和阶段2通用）。

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

    plot(on_figure, caption='位移场1 (原始在重力作用下)')

    # 备份原始位移场，用于后续计算变化量
    vx0 = [model.get_pos(i * 2) for i in range(mesh.node_number)]
    vy0 = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]

    # ========================
    # 阶段2：模拟中心挖空，重新计算位移场
    # ========================

    # 修改中心区域（1.3<x<1.7, 0.4<y<0.6）的材料属性
    # 将杨氏模量从1e9折减到1e7（降低100倍），模拟挖空区域的材料弱化
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y, z = face.pos
        if 1.3 < x < 1.7 and 0.4 < y < 0.6:
            face.set_attr(fa_ym, 1.0e7)  # 杨氏模量折减，模拟挖空区域
        else:
            face.set_attr(fa_ym, 1.0e9)
        face.set_attr(fa_mu, 0.2)
        face.set_attr(fa_den, 1000.0)
        face.set_attr(fa_h, 1.0)

    # 重新计算刚度矩阵（因为杨氏模量发生了变化）
    face_stiffs = compute_face_stiff2(
        mesh, fa_E=fa_ym, fa_mu=fa_mu,
        fa_h=fa_h)

    # 重新组装动力学系统
    model = FemAlg.create2(
        mesh=mesh, fa_den=fa_den, fa_h=fa_h,
        face_stiffs=face_stiffs)

    # 施加与阶段1相同的边界条件
    for i in range(mesh.node_number):
        x, y = mesh.get_node(i).pos[0], mesh.get_node(i).pos[1]
        if x < 0.01 or x > x_max - 0.01:  # 左右的node，固定x方向的位移
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            continue
        if y < 0.01:  # 底部，固定y方向的位移
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
            continue

    # 施加与阶段1相同的顶部载荷
    for i in range(mesh.node_number):
        f = model.get_p2f(i * 2 + 1)
        f.c -= 1e2

    # 执行静态求解
    solver = ConjugateGradientSolver(tolerance=1.0e-30)
    model.iterate(dt=1, solver=solver)

    def on_figure(fig):
        """
        绘制挖空后的位移场云图。

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

    plot(on_figure, caption='位移场2 (中心挖空之后)')

    # ========================
    # 阶段3：计算并显示位移场的变化量
    # ========================

    def on_figure(fig):
        """
        绘制挖空前后的位移变化量云图。

        通过计算挖空后位置与原始位置的差值，突出显示挖空区域的影响。

        Args:
            fig: matplotlib图形对象
        """
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - vx0[i] for i in range(mesh.node_number)]  # x方向位移变化
        dy = [vy[i] - vy0[i] for i in range(mesh.node_number)]  # y方向位移变化

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    plot(on_figure, caption='位移场的变化量')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

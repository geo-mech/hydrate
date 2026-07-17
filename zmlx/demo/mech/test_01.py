# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到向下的面力'
#
# 【详细说明】
# 本案例模拟一个3m × 1m的矩形弹性体，采用三角形网格划分（30×10）。
# 左侧边界固定（所有节点x和y方向位移约束），右侧边界受到向下的面力（1e3 N），
# 计算弹性体在静态载荷下的位移场。展示了有限元静力分析的标准流程：
#   1. 使用layered_triangles生成结构化三角形网格
#   2. 通过compute_face_stiff2计算每个单元的刚度矩阵
#   3. 使用FemAlg.create2组装全局刚度矩阵和质量矩阵
#   4. 通过放大节点质量实现固定位移边界条件
#   5. 通过修改节点力（p2f）施加外力荷载
#   6. 使用ConjugateGradientSolver一次性求解静态平衡

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2

# 定义矩形区域的边界 [m]
X_MIN = 0
X_MAX = 3
Y_MIN = 0
Y_MAX = 1

# 生成结构化三角形网格：x方向30等分，y方向10等分
mesh = layered_triangles(X_MIN, X_MAX, 30, Y_MIN, Y_MAX, 10, as_mesh=True)

# Mesh的face的自定义属性的ID（用于在三角形单元上存储物理参数）
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

# 计算每个三角形单元的刚度矩阵（平面应力问题）
face_stiffs = compute_face_stiff2(
    mesh, fa_E=fa_ym, fa_mu=fa_mu,
    fa_h=fa_h)

# 组装全局动力学系统（质量矩阵 + 刚度矩阵）
model = FemAlg.create2(
    mesh=mesh, fa_den=fa_den, fa_h=fa_h,
    face_stiffs=face_stiffs)

# 施加边界条件和载荷
for i in range(mesh.node_number):
    x = mesh.get_node(i).pos[0]
    if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变（固定边界）
        model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
        model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
    if x > 2.99:  # 对于右侧的node，添加一个纵向（y方向）向下的压力
        f = model.get_p2f(i * 2 + 1)  # i*2+1 表示y方向自由度的节点力
        f.c -= 1e3    # 施加向下的集中力（负号表示向下）

# 创建共轭梯度求解器，执行一个时间步的静态求解
solver = ConjugateGradientSolver(tolerance=1.0e-20)
model.iterate(dt=1, solver=solver)


def on_figure(fig):
    """
    绘制位移场云图的回调函数。

    计算每个节点相对于初始位置的x和y方向位移，
    并以三角形等值线图（tricontourf）的形式并排显示。

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

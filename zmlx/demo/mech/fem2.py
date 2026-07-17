# ** desc = '二维有限元模型(两个三角形有两个顶点固定，另外两个顶点振动过程)'
#
# 【详细说明】
# 本案例演示了如何使用二维有限元方法模拟弹性体的自由振动。
# 模型由两个三角形单元拼成一个四边形区域，共有4个节点：
#   - 节点0、1、3的质量被放大（固定约束）
#   - 节点2（即第3个节点）在x方向施加一个初始位移0.2，随后释放
# 系统在弹性恢复力作用下发生持续振动，验证有限元动力学求解器的正确性。
#
# 涉及的建模技术：
#   1. 使用Mesh3创建三角形网格（节点、连杆、面）
#   2. 通过compute_face_stiff2计算每个三角形单元的刚度矩阵
#   3. 使用FemAlg.create2组装动力学系统（DynSys）
#   4. 通过ConjugateGradientSolver（共轭梯度求解器）进行迭代求解

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2


class FaceKeys:
    """
    存储在每个三角形面（Face）上的自定义属性索引。

    这些索引用于通过set_attr/get_attr在Mesh3的Face对象上存取物理参数。
    """
    ym = 0    # 杨氏模量 (Young's modulus) [Pa]
    mu = 1    # 泊松比 (Poisson's ratio) [无量纲]
    den = 2   # 密度 (Density) [kg/m^3]
    h = 3     # 厚度 (Thickness) [m]


def create_mesh():
    """
    创建一个由两个三角形单元组成的二维网格。

    网格包含4个节点，坐标分别为(0,0)、(1,0)、(0.5,1)、(1.5,1)，
    两个三角形共用中间一条边，构成一个四边形区域。

    Returns:
        Mesh3: 创建好的二维三角形网格对象
    """
    mesh = Mesh3()

    # 添加4个节点，每个节点由三维坐标(x, y, z)定义（z=0表示平面问题）
    nodes = [mesh.add_node(*pos) for pos in
             [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (1.5, 1, 0)]]

    # 添加连杆（Link）和三角形面（Face）
    # 每个三角形由三条边（Link）围成，两个三角形共用节点1-2的边
    for triangle in [(0, 1, 2), (1, 2, 3)]:
        n0 = nodes[triangle[0]]
        n1 = nodes[triangle[1]]
        n2 = nodes[triangle[2]]
        mesh.add_face([mesh.add_link([n0, n1]), mesh.add_link([n1, n2]),
                       mesh.add_link([n2, n0])])

    # 为每个三角形面设置材料属性（杨氏模量、泊松比、密度、厚度）
    for face in mesh.faces:
        face.set_attr(FaceKeys.ym, 1.0)
        face.set_attr(FaceKeys.mu, 0.2)
        face.set_attr(FaceKeys.den, 1.0)
        face.set_attr(FaceKeys.h, 1.0)

    return mesh


def create(mesh):
    """
    根据给定的Mesh3网格创建动力学有限元模型（DynSys）。

    本函数计算每个三角形面的刚度矩阵，组装动力学系统，
    并通过放大某些节点的质量来实现位移边界条件。

    Args:
        mesh: Mesh3对象，包含节点、连杆和面的拓扑及属性

    Returns:
        DynSys: 组装的动力学系统，包含质量矩阵、刚度矩阵和初始位移
    """
    # 基于每个三角形的杨氏模量、泊松比和厚度，计算单元刚度矩阵
    face_stiffs = compute_face_stiff2(mesh, fa_E=FaceKeys.ym, fa_mu=FaceKeys.mu,
                                      fa_h=FaceKeys.h)
    print(face_stiffs)

    # 使用FemAlg.create2组装全局动力学系统
    # 该方法将单元刚度矩阵组装到全局系统，并根据面密度和厚度计算节点质量
    model = FemAlg.create2(mesh=mesh, fa_den=FaceKeys.den, fa_h=FaceKeys.h,
                           face_stiffs=face_stiffs)

    # 将节点0、1、3的质量放大1e20倍，近似实现固定位移边界条件
    # （质量无穷大的节点在外力作用下几乎不发生位移）
    for idx in [0, 1, 3]:
        model.set_mass(idx, model.get_mass(idx) * 1.0e20)

    # 修改第3个节点（索引2）的x方向初始位置，打破平衡状态
    # 这样系统将在弹性恢复力作用下开始振动
    idx = 3 * 2  # 第3个node的x方向自由度（每个节点有x和y两个自由度）
    model.set_pos(idx, model.get_pos(idx) + 0.2)

    return model


def show(model, mesh):
    """
    绘制当前时刻的位移场云图。

    计算每个节点相对于初始位置的x方向位移，并以三角形等值线图显示。

    Args:
        model: DynSys动力学系统对象
        mesh: Mesh3网格对象，用于获取节点初始坐标
    """
    if gui.exists():
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        tricontourf(x=vx, y=vy, z=dx, caption='x位移', clabel='displacement x')


def solve(model, mesh):
    """
    对动力学模型进行时域推进求解。

    使用共轭梯度法隐式求解每个时间步的静力平衡方程，
    采用固定时间步长dt=0.1，共推进5000步。

    Args:
        model: DynSys动力学系统对象
        mesh: Mesh3网格对象（用于绘图）
    """
    # 创建共轭梯度求解器，设置较高的收敛精度
    solver = ConjugateGradientSolver(tolerance=1.0e-15)
    for step in range(5000):
        gui.break_point()         # 检查GUI中断请求
        print(f'step = {step}')
        model.iterate(dt=0.1, solver=solver)  # 推进一个时间步
        if step % 20 == 0:
            show(model, mesh)     # 每隔20步更新一次可视化


def execute(gui_mode=True, close_after_done=False):
    """
    程序主入口：创建网格、组装模型并启动求解。

    Args:
        gui_mode (bool): 是否启用GUI模式（默认True）
        close_after_done (bool): 求解完成后是否自动关闭窗口
    """
    mesh = create_mesh()
    model = create(mesh=mesh)
    gui.execute(func=solve, args=[model, mesh],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

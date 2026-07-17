# ** desc = '三维有限元模型'

# 本案例演示三维有限元（FEM）模型的创建、加载和求解。
# 物理问题：一个三维块体在内部沿垂直方向施加一对力偶（在中心圆柱区域内的
# 垂直链路上加载相反的力），模拟剪切或扭转作用下的弹性变形响应。
# 建模方法：使用Mesh3模块创建三维立方体网格，通过create3函数建立有限元模型，
# 在特定区域内沿垂直方向施加大小相等、方向相反的节点力（形成力偶），
# 使用共轭梯度法（ConjugateGradientSolver）求解静力平衡问题。
# 位移结果通过等值线图展示，反映力偶作用下的变形模式。

from zmlx import *
from zmlx.fem.create3 import create3


def create_mesh():
    """
    创建三维有限元网格。

    生成一个厚度方向很薄（x方向-0.5~0.5）的立方体网格，
    在y和z方向范围均为-50~50，每个方向分别剖分为1、20、20份，
    共形成21x21个节点，用于模拟准二维的平面应变问题。

    返回:
        Mesh3: 三维网格对象
    """
    return Mesh3.create_cube(x1=-0.5, y1=-50, z1=-50,
                             x2=+0.5, y2=+50, z2=+50,
                             dx=1, dy=5, dz=5)


def create(mesh):
    """
    根据网格创建有限元模型，并在中心圆柱区域施加力偶载荷。

    在网格中查找垂直方向（z方向）的链路，若链路位于中心半径10以内的圆柱区域，
    则在该链路两端节点沿z方向施加大小相等、方向相反的节点力（形成力偶）。
    具体地，对z坐标较小的节点施加向下的力（负z方向），
    对z坐标较大的节点施加向上的力（正z方向），模拟扭转载荷。

    参数:
        mesh: 三维网格对象 (Mesh3)

    返回:
        FEModel: 加载完成的有限元模型
    """
    assert isinstance(mesh, Mesh3)
    model = create3(mesh)  # 基于网格创建有限元模型

    # 遍历网格中所有的链路（连接两个相邻节点的边）
    for link in mesh.links:
        assert isinstance(link, Mesh3.Link)
        x0, y0, z0 = link.get_node(0).pos
        x1, y1, z1 = link.get_node(1).pos
        # 仅处理垂直方向（z方向）的链路
        if abs(z0 - z1) > 0.5:
            # 检查链路是否位于中心圆柱区域内（半径10以内）
            if (z0 ** 2 + y0 ** 2) ** 0.5 < 10:
                i0 = link.get_node(0).index
                i1 = link.get_node(1).index
                # 在链路两端施加大小相等、方向相反的z方向力
                if z0 < z1:
                    # 下端节点施加向下的力（-z方向）
                    p2f = model.get_p2f(i0 * 3 + 2)
                    p2f.c = p2f.c - 0.1
                    # 上端节点施加向上的力（+z方向）
                    p2f = model.get_p2f(i1 * 3 + 2)
                    p2f.c = p2f.c + 0.1
                else:
                    # 同上，根据z坐标大小判断方向
                    p2f = model.get_p2f(i0 * 3 + 2)
                    p2f.c = p2f.c + 0.1
                    p2f = model.get_p2f(i1 * 3 + 2)
                    p2f.c = p2f.c - 0.1
    return model


def show(model, mesh, caption=None):
    """
    显示有限元模型的位移结果。

    提取所有节点的z方向位移，并与初始z坐标比较得到位移增量，
    绘制z方向位移的等值线图，直观展示模型的变形特征。

    参数:
        model: 有限元模型对象
        mesh: 三维网格对象 (Mesh3)
        caption: 图形标题（可选）
    """
    assert isinstance(mesh, Mesh3)
    if gui.exists():
        vy = []  # 存储y坐标
        vz = []  # 存储z坐标
        dz = []  # 存储z方向位移增量
        for node_id in range(int(mesh.node_number / 2)):
            vy.append(model.get_pos(node_id * 3 + 1))  # 节点y方向位置
            vz.append(model.get_pos(node_id * 3 + 2))  # 节点z方向位置
            z0 = mesh.get_node(node_id).pos[2]  # 初始z坐标
            dz.append(model.get_pos(node_id * 3 + 2) - z0)  # z方向位移
        # 绘制等值线图，网格尺寸为21x21
        contourf(x=np.reshape(vy, [21, 21]),
                 y=np.reshape(vz, [21, 21]),
                 z=np.reshape(dz, [21, 21]), caption=caption, aspect='equal')


def solve(model, mesh):
    """
    求解有限元模型。

    使用共轭梯度法求解器（容差1.0e-20）进行两个时间步的静力平衡求解，
    每步后显示位移结果。

    参数:
        model: 有限元模型对象
        mesh: 三维网格对象 (Mesh3)
    """
    # 创建高精度的共轭梯度求解器
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    model.iterate(dt=1000, solver=solver)  # 第一个时间步
    show(model, mesh, caption='step0')
    model.iterate(dt=1000, solver=solver)  # 第二个时间步
    show(model, mesh, caption='step1')


def execute(gui_mode=True, close_after_done=False):
    """
    程序入口：执行三维有限元模拟。

    创建网格、构建并加载模型，然后进行求解。

    参数:
        gui_mode: 是否启用GUI显示（默认为True）
        close_after_done: 计算完成后是否自动关闭窗口（默认为False）
    """
    mesh = create_mesh()
    model = create(mesh=mesh)
    gui.execute(func=solve, args=[model, mesh],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()

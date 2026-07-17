# ** desc = '动态的有限元计算：应力波的传递过程-3'
#
# 【详细说明】
# 本案例使用弹簧系统模拟从多个点源发出的径向波及其干涉。
# 在圆盘的y轴上设置4个点源：(0, -0.3), (0, -0.1), (0, 0.1), (0, 0.3)。
# 每个点源附近（半径r<0.05）的节点上施加径向向外的初始速度，
# 模拟多个点源同时激发产生的波场干涉现象。
#
# 与spring/wave_02.py（单点源）的区别：
#   - wave_02.py：单个中心点源，产生对称的柱面波
#   - wave_03.py：4个点源沿y轴排列，产生复杂的干涉图样
#   - 推进步数更少（150步），因为干涉效应在较短时间内即可观察到

from zmlx import *
from zmlx.data import mesh_c10000 as data


def create_model(triangles, x, y):
    """
    创建弹簧系统模型，施加多点源径向初始速度。

    在4个点源位置：
      (0, -0.3), (0, -0.1), (0, 0.1), (0, 0.3)
    各自的附近区域（半径r<0.05）施加径向向外的初始速度，
    模拟多个点源同时激发产生的弹性波干涉。

    Args:
        triangles: 三角形单元列表，每个单元由三个节点索引组成
        x: 所有节点的x坐标列表 [m]
        y: 所有节点的y坐标列表 [m]

    Returns:
        SpringSys: 构建好的弹簧系统模型（带多点源初始速度）
    """
    model = SpringSys()
    virtual_nodes = []

    # 定义4个点源位置（沿y轴排列）
    points = [(0, -0.3), (0, -0.1), (0, 0.1), (0, 0.3)]
    for i in range(len(x)):
        v = [0, 0, 0]
        # 检查当前节点是否在任意一个点源的激发范围内
        for c in points:
            r = max(get_distance([x[i], y[i]], c), 0.001)  # 到点源的距离
            if r < 0.05:
                # 施加径向向外的速度（从点源指向外）
                v = [(x[i] - c[0]) / r, (y[i] - c[1]) / r, 0]
        node = model.add_node(
            pos=(x[i], y[i], 0),
            vel=v,
            mass=1,
            force=(0, 0, 0))
        virtual_nodes.append(model.add_virtual_node(node=node))
    # 在每条三角形边上添加弹簧
    for tri in triangles:
        links = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for link in links:
            x0, y0, x1, y1 = x[link[0]], y[link[0]], x[link[1]], y[link[1]]
            dist = np.linalg.norm(np.array([x0, y0]) - np.array([x1, y1]))
            model.add_spring(
                virtual_nodes=[virtual_nodes[inode] for inode in link],
                len0=dist, k=1)
    return model


def main():
    """
    主函数：创建弹簧系统模型并执行150步多点源波传播模拟。

    4个点源同时激发产生径向波，在传播过程中相互干涉，
    形成复杂的波场图样。无阻尼条件，每10步更新可视化。
    """
    # 创建带多点源初始速度的弹簧系统模型
    model = create_model(data.tri, data.x, data.y)
    print(model)

    # 保存初始节点位置
    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    # 时间推进：150步，步长0.1
    for i in range(150):
        gui.break_point()
        model.modify_pos(2, 0, 0)  # 保持二维平面运动
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        if i % 10 == 0:
            print(i)
            # 计算位移幅值并绘制云图
            dp = np.array([node.pos for node in model.nodes]) - p0
            tricontourf(
                x=data.x, y=data.y,
                z=(dp[:, 0] ** 2 + dp[:, 1] ** 2) ** 0.5,
                caption='位移场', tight_layout=True
            )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

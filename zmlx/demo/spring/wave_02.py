# ** desc = '动态的有限元计算：应力波的传递过程-2'
#
# 【详细说明】
# 本案例使用弹簧系统模拟从圆盘中心向外传播的径向波。
# 初始条件：在圆盘中心（半径r<0.05）的节点上施加径向向外的初始速度，
# 模拟一个从中心点源发出的球面波（在二维圆盘中为柱面波）。
#
# 与spring/wave_01.py的区别：
#   - wave_01.py：速度冲击呈带状分布（x方向），产生平面波
#   - wave_02.py：速度冲击呈径向分布（从中心向外），产生柱面波
#   - 波前形态不同：平面波 vs. 柱面波
#   - 推进步数不同：300步 vs. 200步

from zmlx import *
from zmlx.data import mesh_c10000 as data


def create_model(triangles, x, y):
    """
    创建弹簧系统模型，施加径向向外的初始速度。

    在圆盘中心（半径r<0.05）的节点上施加径向向外的速度，
    即速度方向沿径向指向外，大小归一化为1。

    Args:
        triangles: 三角形单元列表，每个单元由三个节点索引组成
        x: 所有节点的x坐标列表 [m]
        y: 所有节点的y坐标列表 [m]

    Returns:
        SpringSys: 构建好的弹簧系统模型（带径向初始速度）
    """
    model = SpringSys()
    virtual_nodes = []
    # 添加节点并施加径向初始速度
    for i in range(len(x)):
        r = max(get_distance([x[i], y[i]], [0, 0]), 0.001)  # 到原点的距离
        if r < 0.05:
            # 在中心小范围内施加径向向外的速度
            # 速度向量 = (x/r, y/r, 0)，即径向单位向量
            v = [x[i] / r, y[i] / r, 0]
        else:
            v = [0, 0, 0]  # 其他区域初始速度为零
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
    主函数：创建弹簧系统模型并执行200步径向波传播模拟。

    中心点源激发的柱面波在圆盘中传播，无阻尼条件（无速度衰减）。
    每10步更新可视化，观察波从中心向四周均匀扩散的过程。
    """
    # 创建带径向初始速度的弹簧系统模型
    model = create_model(data.tri, data.x, data.y)
    print(model)

    # 保存初始节点位置
    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    # 时间推进：200步，步长0.1
    for i in range(200):
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

# ** desc = '基于弹簧系统计算应力的传播'
#
# 【详细说明】
# 本案例使用弹簧系统（SpringSys）模拟应力波在圆盘形弹性体中的传播。
# 与基于有限元的方法（如wave_01.py）不同，本案例直接使用质点-弹簧模型：
#   1. 每个网格节点对应一个质点
#   2. 三角形网格的每条边对应一根弹簧
#   3. 通过add_spring和add_virtual_node构建弹性网络
#   4. 中心区域（半径<0.2）的弹簧初始长度拉伸1%，模拟残余应力
#   5. 外部区域（半径>0.48）的节点被固定（质量无穷大）
#   6. 每步施加0.99的速度衰减（阻尼）
#
# SpringSys提供了一种直观的弹性体离散化方法，适合理解应力波传播的物理本质。

from zmlx import *
from zmlx.data import mesh_c10000 as data


def create_model(triangles, x, y):
    """
    基于三角形网格创建弹簧系统模型。

    每个网格节点对应一个质点，每条三角形边对应一根弹簧。
    外部边界节点（r>0.48）的质量设为无穷大以实现固定边界。
    中心区域（r<0.2）的弹簧初始长度拉伸1%，模拟局部残余应力。

    Args:
        triangles: 三角形单元列表，每个单元由三个节点索引组成
        x: 所有节点的x坐标列表 [m]
        y: 所有节点的y坐标列表 [m]

    Returns:
        SpringSys: 构建好的弹簧系统模型
    """
    model = SpringSys()
    virtual_nodes = []
    for i in range(len(x)):
        # 添加质点节点：边界附近质量设为无穷大（固定），内部质量设为1
        node = model.add_node(pos=(x[i], y[i], 0), vel=(0, 0, 0),
                              mass=1 if np.linalg.norm(
                                  [x[i], y[i]]) < 0.48 else 1.0e10,
                              force=(0, 0, 0))
        # 每个节点关联一个虚拟节点（用于弹簧系统的计算）
        virtual_nodes.append(model.add_virtual_node(node=node))
    # 遍历每个三角形，在三条边上分别添加弹簧
    for tri in triangles:
        # 计算三角形的中心坐标
        tri_x = (x[tri[0]] + x[tri[1]] + x[tri[2]]) / 3
        tri_y = (y[tri[0]] + y[tri[1]] + y[tri[2]]) / 3
        # 三角形的三条边
        links = ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
        for link in links:
            x0, y0, x1, y1 = x[link[0]], y[link[0]], x[link[1]], y[link[1]]
            dist = np.linalg.norm(np.array([x0, y0]) - np.array([x1, y1]))
            # 添加弹簧，初始长度为节点距离，弹簧刚度k=1
            spr = model.add_spring(
                virtual_nodes=[virtual_nodes[inode] for inode in link],
                len0=dist, k=1)
            # 中心区域（r<0.2）的弹簧初始长度拉伸1%，模拟残余应力
            if np.linalg.norm([tri_x, tri_y]) < 0.2:
                spr.len0 *= 1.01
    return model


def main():
    """
    主函数：创建弹簧系统模型并执行500步动态松弛求解。

    从mesh_c10000数据集加载三角形网格和节点坐标，
    构建弹簧系统后执行时间推进：
      - 每步将z方向自由度置零（保持二维平面运动）
      - 每步速度衰减1%（乘以0.99），模拟材料阻尼
      - 每10步更新可视化，观察应力波的传播过程
    """
    # 从预定义数据创建弹簧系统模型
    model = create_model(data.tri, data.x, data.y)
    print(model)

    # 保存初始节点位置（用于后续计算位移变化量）
    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    # 时间推进：500步，步长0.1，每10步更新可视化
    for i in range(500):
        gui.break_point()
        # 将z方向自由度（索引2）的位置置零，保持二维平面运动
        model.modify_pos(2, 0, 0)
        # 执行一个时间步的求解
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        # 每步速度衰减1%，模拟材料阻尼
        model.modify_vel(0.99)
        if i % 10 == 0:
            print(i)
            # 计算每个节点的位移幅值并绘制云图
            dp = np.array([node.pos for node in model.nodes]) - p0
            tricontourf(x=data.x, y=data.y,
                        z=(dp[:, 0] ** 2 + dp[:, 1] ** 2) ** 0.5,
                        caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

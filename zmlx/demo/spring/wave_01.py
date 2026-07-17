# ** desc = '动态的有限元计算：应力波的传递过程-1'
#
# 【详细说明】
# 本案例使用弹簧系统（SpringSys）模拟应力波传播，初始条件为速度冲击。
# 在圆盘中部（x≈0.16）的带状区域施加相反的初始速度（左侧-1、右侧+1），
# 模拟一个向两侧传播的弹性波。与mech/wave_01.py的物理问题相同，
# 但采用弹簧系统而非有限元方法实现。
#
# 与spring/spring_sys.py的区别：
#   - 无固定边界（所有节点质量为1）
#   - 初始条件为速度冲击，而非初始应力
#   - 不施加速度阻尼（注释掉了modify_vel），模拟无阻尼波传播
#   - 共推进300步

from zmlx import *
from zmlx.data import mesh_c10000 as data


def create_model(triangles, x, y):
    """
    创建弹簧系统模型，施加初始速度冲击。

    在圆盘中部（x≈0.16）的带状区域施加方向相反的初始速度：
      - 带状区域左侧（x<0.16）：速度-1（向左）
      - 带状区域右侧（x>0.16）：速度+1（向右）

    Args:
        triangles: 三角形单元列表，每个单元由三个节点索引组成
        x: 所有节点的x坐标列表 [m]
        y: 所有节点的y坐标列表 [m]

    Returns:
        SpringSys: 构建好的弹簧系统模型（带初始速度）
    """
    model = SpringSys()
    virtual_nodes = []
    # 添加节点并施加初始速度
    for i in range(len(x)):
        xx = 0.16
        # 在带状区域施加相反方向的速度
        if xx - 0.05 < x[i] < xx + 0.05 and -0.3 < y[i] < 0.3:
            v = -1 if x[i] < xx else 1  # 左侧向左、右侧向右
        else:
            v = 0  # 其他区域初始速度为零
        node = model.add_node(
            pos=(x[i], y[i], 0),
            vel=(v, 0, 0),  # 仅x方向有初始速度
            mass=1,          # 所有节点质量均为1（无固定边界）
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
                len0=dist, k=1)  # 刚度k=1，初始长度等于节点距离
    return model


def main():
    """
    主函数：创建弹簧系统模型并执行300步无阻尼波传播模拟。

    使用从mesh_c10000加载的圆盘形网格，施加初始速度冲击后，
    在无阻尼条件下（不施加速度衰减）计算应力波的传播过程。
    每10步更新可视化，展示波从中心向边界传播的过程。
    """
    # 创建带初始速度冲击的弹簧系统模型
    model = create_model(data.tri, data.x, data.y)
    print(model)

    # 保存初始节点位置
    p0 = np.array([node.pos for node in model.nodes])

    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    dynsys = DynSys()

    # 时间推进：300步，步长0.1
    for i in range(300):
        gui.break_point()
        # 将z方向自由度置零，保持二维平面运动
        model.modify_pos(2, 0, 0)
        # 执行一个时间步的求解
        model.iterate(dt=0.1, solver=solver, dynsys=dynsys)
        # 注意：此处不施加速度阻尼（无阻尼波传播）
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

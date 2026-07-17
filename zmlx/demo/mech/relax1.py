# ** desc = '测试一维的松弛问题'
#
# 【详细说明】
# 本案例演示了一维松弛问题的动力学求解过程。
# 模型由11个质点通过弹簧连接构成一维链（每个质点与左右邻居相连），
# 首尾质点被固定（质量设为无穷大），尾部（最后一个质点）初始位移设为1，
# 在松弛过程中，通过逐步释放内部应力使系统达到平衡状态。
#
# 涉及的建模技术：
#   1. 使用DynSys创建一维质点-弹簧动力学系统
#   2. 通过create_lexpr创建刚度矩阵的稀疏表达式
#   3. 使用ConjugateGradientSolver进行隐式时间推进
#   4. 在每个时间步手动将速度置零（阻尼），实现准静态松弛
#   5. 通过修改p2f（节点力）施加额外的内部应力调整

from zmlx import *


def test_1():
    """
    一维松弛问题主测试函数。

    创建11个质点的弹簧链，首尾固定，尾部施加初始位移1，
    通过20个时间步的迭代松弛，观察系统从初始状态到平衡的演化过程。
    在迭代过程中，同时在中间两个单元（索引4-5）施加额外的应力调整，
    模拟非均匀内应力的松弛行为。
    """
    # 创建动力学系统，设置节点数为11
    model = DynSys()
    model.size = 11

    # 初始化所有节点的位置、速度、质量
    for i in range(model.size):
        model.set_pos(i, 0)       # 初始位置均为0
        model.set_vel(i, 0)       # 初始速度均为0
        model.set_mas(i, 1)       # 质量设为1

        # 创建刚度矩阵的稀疏表达式：每个节点与自身连接，刚度为-2
        # 这是中心差分格式的离散化
        model.get_p2f(i).clone(create_lexpr([i, -2]))
        if i > 0:
            model.get_p2f(i).add(i - 1, 1)   # 与左侧邻居连接，刚度1
        if i + 1 < model.size:
            model.get_p2f(i).add(i + 1, 1)   # 与右侧邻居连接，刚度1

    # 首尾的质量设置为无穷大，用以固定
    model.set_mas(0, 1e10)
    model.set_mas(-1, 1e10)
    model.set_pos(-1, 1)  # 将尾部设置一个不同的位移（初始扰动）
    print(model)

    def solve():
        """
        松弛求解过程。

        在20个时间步内，每个步长dt=5，使用共轭梯度求解器进行隐式求解。
        每个时间步后将所有节点速度置零（完全阻尼），实现准静态松弛。
        同时，对中间两个单元施加额外的应力调整（刚度折减5%），
        模拟局部材料弱化效应。
        """
        # 各个单元的额外的内力（初始为零）
        inner_force = [0] * (model.size - 1)

        solver = ConjugateGradientSolver()
        for step in range(20):
            print(f'step = {step}')
            model.iterate(dt=5, solver=solver)
            # 每个时间步后将所有节点速度置零，实现完全阻尼的准静态松弛
            for idx in range(model.size):
                model.set_vel(idx, 0)
            # 绘制当前时刻的位移曲线
            x = list(range(model.size))
            y = [model.get_pos(idx) for idx in range(model.size)]
            plot_xy(x, y)

            # 在中间两个单元（索引4和5）施加额外的应力调整
            # 通过修改节点力（p2f）实现：计算当前单元应力与目标应力的差值
            for idx in range(4, 6):
                # 当前单元应力 = 位移差 × 0.95（刚度折减5%）
                force = (model.get_pos(idx + 1) - model.get_pos(idx)) * 0.95
                d_force = force - inner_force[idx]
                # 将多余的力施加到相邻节点上（作用力与反作用力）
                model.get_p2f(idx).c -= d_force
                model.get_p2f(idx + 1).c += d_force
                inner_force[idx] = force

    gui.execute(func=solve, close_after_done=False)


if __name__ == '__main__':
    test_1()

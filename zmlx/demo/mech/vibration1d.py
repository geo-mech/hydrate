# ** desc = '一维的振动问题。初始时刻，右侧给一个瞬时的位移1，计算这个位移传递的过程'
#
# 【详细说明】
# 本案例模拟一维弹性杆的振动问题，使用100个质点通过弹簧连接组成一维链。
# 初始时刻，尾部（第99个节点）被施加单位位移（pos=1），首尾固定（质量无穷大）。
# 在释放后，位移波沿弹簧链传播，形成复杂的振动模态。
#
# 涉及的建模技术：
#   1. 使用DynSys创建100自由度的一维质点-弹簧系统
#   2. 通过create_lexpr创建中心差分格式的刚度矩阵（[i,-2]表示二阶导数离散化）
#   3. 每个时间步施加0.999的速度衰减系数，模拟材料阻尼
#   4. 使用ConjugateGradientSolver进行隐式时间推进
#   5. 总模拟2000步，步长dt=0.2，观察波的传播和反射

from zmlx import *


def test_1():
    """
    一维振动问题主测试函数。

    创建100个质点的弹簧链，首尾固定，尾部初始位移为1。
    在隐式时间积分过程中施加轻微阻尼（速度每步衰减0.1%），
    模拟弹性波在有限长杆中的传播和衰减过程。
    每20步绘制一次位移曲线，观察波形的演化。
    """
    # 创建动力学系统，设置100个自由度（节点数）
    model = DynSys()
    model.size = 100

    # 初始化所有节点的位置、速度、质量
    for i in range(model.size):
        model.set_pos(i, 0)       # 初始位置均为0
        model.set_vel(i, 0)       # 初始速度均为0
        model.set_mas(i, 1)       # 质量设为1

        # 创建刚度矩阵的稀疏表达式：中心差分格式
        # [i, -2] 表示该节点与自身的连接系数为-2
        model.get_p2f(i).clone(create_lexpr([i, -2]))
        if i > 0:
            model.get_p2f(i).add(i - 1, 1)   # 与左侧邻居的弹性系数为1
        if i + 1 < model.size:
            model.get_p2f(i).add(i + 1, 1)   # 与右侧邻居的弹性系数为1

    # 首尾的质量设置为无穷大，用以固定边界
    model.set_mas(0, 1e10)
    model.set_mas(-1, 1e10)
    model.set_pos(-1, 1)  # 将尾部设置一个不同的位移（初始扰动）

    def solve():
        """
        求解过程：2000步隐式时间推进，每步施加阻尼。

        每步速度衰减0.1%（乘以0.999），模拟材料的内阻尼效应，
        使系统逐渐趋于平衡。每20步更新一次位移曲线可视化。
        """
        solver = ConjugateGradientSolver()
        for step in range(2000):
            model.iterate(dt=0.2, solver=solver)
            # 每步乘以0.999实现速度衰减（相当于施加粘性阻尼）
            for idx in range(model.size):
                model.set_vel(idx, model.get_vel(idx) * 0.999)
            if step % 20 == 0:
                print(f'step = {step}')
                x = list(range(model.size))
                y = [model.get_pos(idx) for idx in range(model.size)]
                plot_xy(x, y)  # 绘制位移曲线

    gui.execute(func=solve, close_after_done=False)


if __name__ == '__main__':
    test_1()

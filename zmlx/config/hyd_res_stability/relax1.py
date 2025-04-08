"""
测试计算1维的松弛问题
"""

from zml import *
from zmlx.plt.plotxy import plotxy
from zmlx.ui import gui


def test_1():
    model = DynSys()

    model.size = 11
    for i in range(model.size):
        model.set_pos(i, 0)
        model.set_vel(i, 0)
        model.set_mas(i, 1)
        model.get_p2f(i).clone(create_lexpr([i, -2]))
        if i > 0:
            model.get_p2f(i).add(i - 1, 1)
        if i + 1 < model.size:
            model.get_p2f(i).add(i + 1, 1)
    # 首尾的质量设置为无穷大，用以固定
    model.set_mas(0, 1e10)
    model.set_mas(-1, 1e10)
    model.set_pos(-1, 1)  # 将尾部设置一个不同的位移
    print(model)

    def solve():
        # 各个单元的额外的内力
        inner_force = [0] * (model.size - 1)

        solver = ConjugateGradientSolver()
        for step in range(20):
            print(f'step = {step}')
            model.iterate(dt=5, solver=solver)
            for idx in range(model.size):
                model.set_vel(idx, 0)
            x = list(range(model.size))
            y = [model.get_pos(idx) for idx in range(model.size)]
            plotxy(x, y)

            for idx in range(4, 6):
                force = (model.get_pos(idx + 1) - model.get_pos(idx)) * 0.95
                d_force = force - inner_force[idx]
                model.get_p2f(idx).c -= d_force
                model.get_p2f(idx + 1).c += d_force
                inner_force[idx] = force

    gui.execute(func=solve, close_after_done=False)


if __name__ == '__main__':
    test_1()

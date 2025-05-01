# ** desc = '一维的振动问题。初始时刻，右侧给一个瞬时的位移1，计算这个位移传递的过程'

from zmlx import *


def test_1():
    model = DynSys()
    model.size = 100
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

    def solve():
        solver = ConjugateGradientSolver()
        for step in range(2000):
            model.iterate(dt=0.2, solver=solver)
            for idx in range(model.size):
                model.set_vel(idx, model.get_vel(idx) * 0.999)  # 减速
            if step % 20 == 0:
                print(f'step = {step}')
                x = list(range(model.size))
                y = [model.get_pos(idx) for idx in range(model.size)]
                plotxy(x, y)

    gui.execute(func=solve, close_after_done=False)


if __name__ == '__main__':
    test_1()

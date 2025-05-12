"""
定义处于测试阶段的方法
"""

import math


def get_velocity_after_slowdown_by_viscosity(v0, a0, time):
    # 确保时间非负
    assert time >= 0.0, "time must be non-negative"

    # 处理极小的初始速度
    if abs(v0) <= 1e-100:
        return 0.0
    # 处理极小的加速度
    if abs(a0) <= 1e-100:
        return v0
    # 处理极短的时间
    if abs(time) <= 1e-100:
        return v0

    # 处理初始速度为负的情况
    if v0 < 0:
        return -get_velocity_after_slowdown_by_viscosity(-v0, a0, time)

    # 确保加速度为非负数
    a0 = abs(a0)

    # 截断过大的初始速度和加速度
    if v0 > 1e100:
        v0 = 1e100
    if a0 > 1e100:
        a0 = 1e100

    # 计算半衰期时间常数
    half_t = 0.6931437 * v0 / a0
    # 计算指数衰减因子
    exponent = time / half_t
    # 返回衰减后的速度
    return v0 * math.pow(0.5, exponent)


def test():
    from random import uniform
    from zml import Alg
    for _ in range(100):
        v0 = uniform(-100, 100)
        a0 = uniform(-100, 100)
        time = uniform(0, 1)
        v1 = get_velocity_after_slowdown_by_viscosity(v0, a0, time)
        v2 = Alg.get_velocity_after_slowdown_by_viscosity(v0, a0, time)
        print(v1, v2)


if __name__ == '__main__':
    test()

"""粘性阻力减速计算（模拟流体在粘性作用下的速度衰减）.

Modified by Claude, 2026-08-12
"""

import math


def get_velocity_after_slowdown_by_viscosity(v0: float, a0: float, time: float):
    """模拟粘性阻力下的速度衰减（指数衰减模型）。

    速度按半衰期指数衰减：``v = v0 * 0.5^(t / half_t)``，
    其中半衰期 ``half_t ≈ 0.693 * v0 / a0``（`a0` 为减速度）。

    Args:
        v0: 初始速度。
        a0: 减速度（取绝对值后使用）。
        time: 衰减时间（必须 >= 0）。

    Returns:
        float: 衰减后的速度。
    """
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
    from zmlx.exts import Alg
    for _ in range(100):
        v0 = uniform(-100, 100)
        a0 = uniform(-100, 100)
        time = uniform(0, 1)
        v1 = get_velocity_after_slowdown_by_viscosity(v0, a0, time)
        v2 = Alg.get_velocity_after_slowdown_by_viscosity(v0, a0, time)
        print(v1, v2)


if __name__ == '__main__':
    test()

from math import sqrt, pow


def get_frac_width(pos, half_length, shear_modulus, poisson_ratio, fluid_net_pressure):
    """
    计算无限大空间内，一个内部充满流体的裂缝的缝宽的理论值。
    参考文献：
    Crouch, S.L.; Starfield, A.M.
    Boundary Element Methods in Solid Mechanics; George Allen & Unwin: London, UK, 1983.
    参数：
    pos:               位置
    half_length:       裂缝的半长
    shear_modulus:     剪切模量
    poisson_ratio:     泊松比
    fluid_net_pressure:裂缝内流体的净压力
    return:            裂缝的开度
    """
    assert shear_modulus > 0
    assert 0 < poisson_ratio < 0.5
    x = 2.0 * (1.0 - poisson_ratio) / shear_modulus
    y = sqrt(max(0.0, 1 - pow(pos / half_length, 2)))
    return x * y * fluid_net_pressure * half_length

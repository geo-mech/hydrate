from math import sqrt, pow

from zmlx.alg.utils import clamp


def get_frac_width(pos, half_length, shear_modulus, poisson_ratio,
                   fluid_net_pressure):
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


def get_frac_cond(fracture_aperture, fracture_length, fracture_height,
                  fluid_viscosity):
    """
    计算裂缝的导流系数 (假设裂缝的横截面积是一个矩形)
    """
    if fracture_aperture <= 0.0:
        return 1.0e-30
    assert fracture_aperture < 1e50
    assert fracture_length > 1e-50
    assert fluid_viscosity > 1e-50
    # Assume the cross-section is a Rectangle. This may be not right 2020-9-15
    fluid_viscosity = clamp(fluid_viscosity, 1.0e-10, 1.0e5)
    return clamp((fracture_aperture ** 3) * fracture_height / (
            fluid_viscosity * fracture_length * 12.0),
                 1.0e-30, 1.0e20)


g_1cm = get_frac_cond(1.0e-3, 1.0, 1.0, 1.0) * 10.0  # 1cm缝宽对应导流系数

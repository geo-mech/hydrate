from zmlx.alg.clamp import clamp


def get_frac_cond(fracture_aperture, fracture_length, fracture_height, fluid_viscosity):
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
    return clamp((fracture_aperture ** 3) * fracture_height / (fluid_viscosity * fracture_length * 12.0),
                 1.0e-30, 1.0e20)


g_1cm = get_frac_cond(1.0e-3, 1.0, 1.0, 1.0) * 10.0  # 1cm缝宽对应导流系数

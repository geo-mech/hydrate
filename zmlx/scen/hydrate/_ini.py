from zmlx.utility.fields import LinearField


def create_t_ini(z_top=0.0, t_top=276.0, grad_t=0.04466):
    """
    创建温度的初始场;
        (在z方向线性)
    """
    assert 0.02 <= grad_t <= 0.06
    return LinearField(v0=t_top, z0=z_top, dz=-grad_t)


def create_p_ini(z_top=0.0, p_top=12e6, grad_p=0.01e6):
    """
    创建压力的初始场;
        (在z方向线性)
    """
    assert 0.001e6 <= grad_p <= 0.1e6
    return LinearField(v0=p_top, z0=z_top, dz=-grad_p)


def create_denc_ini(z_min, z_max, denc=3e6):
    """
    储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）
    """
    return lambda x, y, z: denc if z_min + 0.1 < z < z_max - 0.1 else 1e20


def create_fai_ini(*, z_max, fai=0.2):
    """
    孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
    """
    return lambda x, y, z: 1.0e7 if abs(z - z_max) < 0.1 else fai

from zmlx.fem.elements.planar_stress_cst._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu):
    """计算平面应力常应变三角形单元的应力。

    Args:
        nodes (list): 原始节点坐标 [[x0,y0], [x1,y1], [x2,y2]]
        displacement (np.ndarray): 节点位移向量 (6,) [u0,v0,u1,v1,u2,v2]
        E (float): 杨氏模量
        mu (float): 泊松比

    Returns:
        np.ndarray: 应力向量 [sigma_xx, sigma_yy, tau_xy] (3,)
    """
    assert np is not None, "numpy没有安装"
    strain = calc_strain(nodes, displacement)

    factor = E / (1.0 - mu * mu)
    D = factor * np.array([
        [1.0, mu, 0.0],
        [mu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - mu) / 2.0],
    ])

    return D @ strain

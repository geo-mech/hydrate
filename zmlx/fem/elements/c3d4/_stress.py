from zmlx.fem.elements.c3d4._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu):
    """计算C3D4四面体单元的应力（常应力）。

    Args:
        nodes (list): 节点坐标 [[x0,y0,z0],[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
        displacement (np.ndarray): 节点位移向量 (12,) [u0,v0,w0,u1,v1,w1,u2,v2,w2,u3,v3,w3]
        E (float): 杨氏模量
        mu (float): 泊松比

    Returns:
        np.ndarray: 应力向量 [sigma_xx,sigma_yy,sigma_zz,tau_xy,tau_yz,tau_zx] (6,)
    """
    assert np is not None, "numpy没有安装"
    strain = calc_strain(nodes, displacement)

    c = E / ((1.0 + mu) * (1.0 - 2.0 * mu))
    D = np.array([
        [1.0 - mu, mu, mu, 0.0, 0.0, 0.0],
        [mu, 1.0 - mu, mu, 0.0, 0.0, 0.0],
        [mu, mu, 1.0 - mu, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.5 - mu, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.5 - mu, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.5 - mu],
    ]) * c

    return D @ strain

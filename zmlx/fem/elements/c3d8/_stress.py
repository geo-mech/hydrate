from zmlx.fem.elements.c3d8._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu, xi=0.0, eta=0.0, zeta=0.0):
    """计算C3D8六面体单元在指定自然坐标处的应力。

    Args:
        nodes (list): 8个节点的坐标 [[x0,y0,z0],...,[x7,y7,z7]]
        displacement (np.ndarray): 节点位移向量 (24,)
        E (float): 杨氏模量
        mu (float): 泊松比
        xi (float): 自然坐标 xi，默认0.0
        eta (float): 自然坐标 eta，默认0.0
        zeta (float): 自然坐标 zeta，默认0.0

    Returns:
        np.ndarray: 应力向量 [sigma_xx,sigma_yy,sigma_zz,tau_xy,tau_yz,tau_zx] (6,)
    """
    assert np is not None, "numpy没有安装"
    strain = calc_strain(nodes, displacement, xi, eta, zeta)

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

from zmlx.fem.elements.planar_stress_quad4._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu, xi=0.0, eta=0.0):
    """计算双线性四边形单元在指定自然坐标处的应力（平面应力）。

    Args:
        nodes (list): 节点坐标 [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
        displacement (np.ndarray): 节点位移向量 (8,) [u0,v0,u1,v1,u2,v2,u3,v3]
        E (float): 杨氏模量
        mu (float): 泊松比
        xi (float): 自然坐标 ξ，默认0.0（单元中心）
        eta (float): 自然坐标 η，默认0.0（单元中心）

    Returns:
        np.ndarray: 应力向量 [sigma_xx, sigma_yy, tau_xy] (3,)
    """
    assert np is not None, "numpy没有安装"
    strain = calc_strain(nodes, displacement, xi, eta)

    c = E / (1.0 - mu ** 2)
    D = c * np.array([
        [1.0, mu, 0.0],
        [mu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - mu) / 2.0],
    ])

    return D @ strain

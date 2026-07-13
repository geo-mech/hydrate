try:
    import numpy as np
except ImportError:
    np = None

from zmlx.fem.elements.planar_stress_quad8._stiffness import _shape_derivs


def calc_strain(nodes, displacement, xi=0.0, eta=0.0):
    """计算8节点Serendipity四边形单元在指定自然坐标处的应变。

    Args:
        nodes (list): 节点坐标 [[x0,y0],...,[x7,y7]]
        displacement (np.ndarray): 节点位移向量 (16,)，顺序为 [u0,v0,u1,v1,...,u7,v7]
        xi (float): 自然坐标 ξ，默认0.0（单元中心）
        eta (float): 自然坐标 η，默认0.0（单元中心）

    Returns:
        np.ndarray: 应变向量 [ε_xx, ε_yy, γ_xy] (3,)
    """
    assert np is not None, "numpy没有安装"
    xy = np.array(nodes, dtype=float)
    u = np.asarray(displacement, dtype=float).reshape(-1)

    dN = _shape_derivs(xi, eta)
    J = dN.T @ xy
    invJ = np.linalg.inv(J)
    dNdx = dN @ invJ

    B = np.zeros((3, 16))
    for i in range(8):
        col = i * 2
        B[0, col] = dNdx[i, 0]
        B[1, col + 1] = dNdx[i, 1]
        B[2, col] = dNdx[i, 1]
        B[2, col + 1] = dNdx[i, 0]

    return B @ u

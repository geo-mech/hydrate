try:
    import numpy as np
except ImportError:
    np = None


def calc_strain(nodes, displacement):
    """计算C3D4四面体单元的应变（常应变）。

    Args:
        nodes (list): 节点坐标 [[x0,y0,z0],[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
        displacement (np.ndarray): 节点位移向量 (12,) [u0,v0,w0,u1,v1,w1,u2,v2,w2,u3,v3,w3]

    Returns:
        np.ndarray: 应变向量 [eps_xx,eps_yy,eps_zz,gamma_xy,gamma_yz,gamma_zx] (6,)
    """
    assert np is not None, "numpy没有安装"

    x0, y0, z0 = nodes[0]
    x1, y1, z1 = nodes[1]
    x2, y2, z2 = nodes[2]
    x3, y3, z3 = nodes[3]

    v1 = np.array([x1 - x0, y1 - y0, z1 - z0])
    v2 = np.array([x2 - x0, y2 - y0, z2 - z0])
    v3 = np.array([x3 - x0, y3 - y0, z3 - z0])

    J = np.column_stack((v1, v2, v3))
    J_inv = np.linalg.inv(J)

    natural_derivatives = [
        [-1, -1, -1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ]

    gradients = []
    for i in range(4):
        natural = np.array(natural_derivatives[i])
        grad = J_inv.T @ natural
        gradients.append(grad)

    B = np.zeros((6, 12))
    for i in range(4):
        bi, ci, di = gradients[i]
        col = i * 3
        B[0, col] = bi
        B[1, col + 1] = ci
        B[2, col + 2] = di
        B[3, col] = ci
        B[3, col + 1] = bi
        B[4, col + 1] = di
        B[4, col + 2] = ci
        B[5, col] = di
        B[5, col + 2] = bi

    return B @ np.asarray(displacement).reshape(-1)

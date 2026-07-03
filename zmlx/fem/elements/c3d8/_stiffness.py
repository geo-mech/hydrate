try:
    import numpy as np
except ImportError:
    np = None


def _shape_funcs(xi, eta, zeta):
    """Shape functions for 8-node hexahedral at natural coordinates (xi, eta, zeta)."""
    return np.array([
        (1.0 - xi) * (1.0 - eta) * (1.0 - zeta) / 8.0,
        (1.0 + xi) * (1.0 - eta) * (1.0 - zeta) / 8.0,
        (1.0 + xi) * (1.0 + eta) * (1.0 - zeta) / 8.0,
        (1.0 - xi) * (1.0 + eta) * (1.0 - zeta) / 8.0,
        (1.0 - xi) * (1.0 - eta) * (1.0 + zeta) / 8.0,
        (1.0 + xi) * (1.0 - eta) * (1.0 + zeta) / 8.0,
        (1.0 + xi) * (1.0 + eta) * (1.0 + zeta) / 8.0,
        (1.0 - xi) * (1.0 + eta) * (1.0 + zeta) / 8.0,
    ])


def _shape_derivs(xi, eta, zeta):
    """Derivatives of shape functions w.r.t. natural coordinates (xi, eta, zeta).

    Returns array of shape (8, 3): each row is [dN/dxi, dN/deta, dN/dzeta] for one node.
    """
    dN = np.array([
        [-(1.0 - eta) * (1.0 - zeta), -(1.0 - xi) * (1.0 - zeta), -(1.0 - xi) * (1.0 - eta)],
        [(1.0 - eta) * (1.0 - zeta), -(1.0 + xi) * (1.0 - zeta), -(1.0 + xi) * (1.0 - eta)],
        [(1.0 + eta) * (1.0 - zeta), (1.0 + xi) * (1.0 - zeta), -(1.0 + xi) * (1.0 + eta)],
        [-(1.0 + eta) * (1.0 - zeta), (1.0 - xi) * (1.0 - zeta), -(1.0 - xi) * (1.0 + eta)],
        [-(1.0 - eta) * (1.0 + zeta), -(1.0 - xi) * (1.0 + zeta), (1.0 - xi) * (1.0 - eta)],
        [(1.0 - eta) * (1.0 + zeta), -(1.0 + xi) * (1.0 + zeta), (1.0 + xi) * (1.0 - eta)],
        [(1.0 + eta) * (1.0 + zeta), (1.0 + xi) * (1.0 + zeta), (1.0 + xi) * (1.0 + eta)],
        [-(1.0 + eta) * (1.0 + zeta), (1.0 - xi) * (1.0 + zeta), (1.0 - xi) * (1.0 + eta)],
    ]) / 8.0
    return dN


def _B_matrix(dNdx):
    """Construct B matrix from shape function derivatives in physical coordinates."""
    B = np.zeros((6, 24))
    for i in range(8):
        col = i * 3
        B[0, col] = dNdx[i, 0]
        B[1, col + 1] = dNdx[i, 1]
        B[2, col + 2] = dNdx[i, 2]
        B[3, col] = dNdx[i, 1]
        B[3, col + 1] = dNdx[i, 0]
        B[4, col + 1] = dNdx[i, 2]
        B[4, col + 2] = dNdx[i, 1]
        B[5, col] = dNdx[i, 2]
        B[5, col + 2] = dNdx[i, 0]
    return B


def _D_matrix(E, mu):
    """Elasticity matrix D for isotropic 3D material."""
    c = E / ((1.0 + mu) * (1.0 - 2.0 * mu))
    D = np.array([
        [1.0 - mu, mu, mu, 0.0, 0.0, 0.0],
        [mu, 1.0 - mu, mu, 0.0, 0.0, 0.0],
        [mu, mu, 1.0 - mu, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.5 - mu, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.5 - mu, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.5 - mu],
    ]) * c
    return D


def calc_stiffness(nodes, E, mu):
    """计算C3D8（三维八节点六面体单元）的刚度矩阵。

    Args:
        nodes (list, tuple): 长度为8的列表，每个元素是包含3个float的列表或元组，表示节点的三维坐标。
            节点顺序遵循ABAQUS约定：
            底面(zeta=-1): 0(左后下) 1(右后下) 2(右前下) 3(左前下)
            顶面(zeta=+1): 4(左后上) 5(右后上) 6(右前上) 7(左前上)
        E (float): 弹性模量
        mu (float): 泊松比

    Returns:
        np.ndarray: 24x24的单元刚度矩阵
    """
    coords = np.array(nodes, dtype=float)
    D = _D_matrix(E, mu)

    K = np.zeros((24, 24))

    # 2x2x2 Gaussian quadrature
    gp = 1.0 / np.sqrt(3.0)
    gp_1d = [-gp, gp]
    wt_1d = [1.0, 1.0]

    for i in range(2):
        for j in range(2):
            for k in range(2):
                xi = gp_1d[i]
                eta = gp_1d[j]
                zeta = gp_1d[k]
                w = wt_1d[i] * wt_1d[j] * wt_1d[k]

                dN = _shape_derivs(xi, eta, zeta)
                J = dN.T @ coords
                detJ = np.linalg.det(J)
                dNdx = dN @ np.linalg.inv(J)
                B = _B_matrix(dNdx)

                K += w * abs(detJ) * (B.T @ D @ B)

    return K

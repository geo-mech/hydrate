try:
    import numpy as np
except ImportError:
    np = None

from zmlx.fem.elements.c3d8._stiffness import _shape_derivs, _B_matrix


def calc_strain(nodes, displacement, xi=0.0, eta=0.0, zeta=0.0):
    """计算C3D8六面体单元在指定自然坐标处的应变。

    Args:
        nodes (list): 8个节点的坐标 [[x0,y0,z0],...,[x7,y7,z7]]
        displacement (np.ndarray): 节点位移向量 (24,)
        xi (float): 自然坐标 xi
        eta (float): 自然坐标 eta
        zeta (float): 自然坐标 zeta

    Returns:
        np.ndarray: 应变向量 [eps_xx,eps_yy,eps_zz,gamma_xy,gamma_yz,gamma_zx] (6,)
    """
    assert np is not None, "numpy没有安装"
    coords = np.array(nodes, dtype=float)
    u = np.asarray(displacement, dtype=float).reshape(-1)

    dN = _shape_derivs(xi, eta, zeta)
    J = dN.T @ coords
    dNdx = dN @ np.linalg.inv(J)
    B = _B_matrix(dNdx)

    return B @ u


def calc_strain_at_gauss_points(nodes, displacement):
    """计算C3D8单元在8个高斯积分点处的应变。

    Args:
        nodes (list): 8个节点的坐标
        displacement (np.ndarray): 节点位移向量 (24,)

    Returns:
        list of (np.ndarray, float, float, float): 每个元素为 (strain_6v, xi, eta, zeta)
    """
    assert np is not None, "numpy没有安装"
    gp = 1.0 / np.sqrt(3.0)
    gp_1d = [-gp, gp]

    results = []
    for i in range(2):
        for j in range(2):
            for k in range(2):
                xi = gp_1d[i]
                eta = gp_1d[j]
                zeta = gp_1d[k]
                strain = calc_strain(nodes, displacement, xi, eta, zeta)
                results.append((strain, xi, eta, zeta))
    return results


def calc_strain_extrapolated(nodes, displacement):
    """将高斯点应变外推到8个节点。

    使用三线性外推矩阵将8个高斯积分点的应变外推到8个角节点。

    Args:
        nodes (list): 8个节点的坐标
        displacement (np.ndarray): 节点位移向量 (24,)

    Returns:
        np.ndarray: (8, 6) 每个节点的应变向量
    """
    assert np is not None, "numpy没有安装"

    gp_results = calc_strain_at_gauss_points(nodes, displacement)
    gp_strains = np.array([r[0] for r in gp_results])

    gp = 1.0 / np.sqrt(3.0)
    gp_coords = [
        (-gp, -gp, -gp), (gp, -gp, -gp), (gp, gp, -gp), (-gp, gp, -gp),
        (-gp, -gp, gp), (gp, -gp, gp), (gp, gp, gp), (-gp, gp, gp)
    ]

    node_coords = [
        (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0)
    ]

    def shape_funcs(xi, eta, zeta):
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

    node_strains = np.zeros((8, 6))
    for i_node, (xn, yn, zn) in enumerate(node_coords):
        N = shape_funcs(xn, yn, zn)
        node_strains[i_node] = sum(N[j] * gp_strains[j] for j in range(8))

    return node_strains

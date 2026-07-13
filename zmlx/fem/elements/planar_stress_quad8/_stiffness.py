try:
    import numpy as np
except ImportError:
    np = None


def _shape_derivs(xi, eta):
    """计算8节点Serendipity四边形形函数对自然坐标的导数。

    Args:
        xi (float): 自然坐标 ξ ∈ [-1, 1]
        eta (float): 自然坐标 η ∈ [-1, 1]

    Returns:
        np.ndarray: (8, 2) 数组，每行为 [dN_i/dξ, dN_i/dη]

    节点顺序（逆时针）：
        0(-1,-1), 1(1,-1), 2(1,1), 3(-1,1)  角节点
        4(0,-1), 5(1,0), 6(0,1), 7(-1,0)     边中点
    """
    dN = np.zeros((8, 2))

    # 角节点 (ξ_i = ±1, η_i = ±1)
    corner_nodes = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    for i, (xi_i, eta_i) in enumerate(corner_nodes):
        dN[i, 0] = 0.25 * (1.0 + eta_i * eta) * (2.0 * xi + xi_i * eta_i * eta)
        dN[i, 1] = 0.25 * (1.0 + xi_i * xi) * (xi_i * eta_i * xi + 2.0 * eta)

    # 边中点节点 (ξ = 0 或 η = 0)
    # 节点4: (0, -1)
    dN[4, 0] = -xi * (1.0 - eta)
    dN[4, 1] = -0.5 * (1.0 - xi * xi)

    # 节点5: (1, 0)
    dN[5, 0] = 0.5 * (1.0 - eta * eta)
    dN[5, 1] = -eta * (1.0 + xi)

    # 节点6: (0, 1)
    dN[6, 0] = -xi * (1.0 + eta)
    dN[6, 1] = 0.5 * (1.0 - xi * xi)

    # 节点7: (-1, 0)
    dN[7, 0] = -0.5 * (1.0 - eta * eta)
    dN[7, 1] = -eta * (1.0 - xi)

    return dN


def calc_stiffness(nodes, E: float, mu: float, thickness: float = 1.0):
    """计算平面应力状态下8节点Serendipity四边形单元（Q8）的刚度矩阵。

    使用3×3高斯积分的等参元公式。

    Args:
        nodes (list, tuple): 长度为8的列表，每个元素是包含两个float的列表或元组，表示节点的(x, y)坐标。
            节点顺序（逆时针）：
            0(-1,-1) 1(1,-1) 2(1,1) 3(-1,1) 角节点
            4(0,-1) 5(1,0) 6(0,1) 7(-1,0) 边中点
        E (float): 杨氏模量
        mu (float): 泊松比
        thickness (float, optional): 单元厚度，默认为1.0

    Returns:
        np.ndarray: 16x16的单元刚度矩阵
    """
    assert np is not None, "numpy没有安装"
    assert E > 0, f"杨氏模量必须大于0, but got {E}"
    assert 0 <= mu < 0.5, f"泊松比必须在0到0.5之间, but got {mu}"
    assert thickness > 0, f"单元厚度必须大于0, but got {thickness}"

    xy = np.array(nodes, dtype=float)
    assert xy.shape == (8, 2), f"节点坐标必须是8x2数组，但得到 {xy.shape}"

    # 平面应力弹性矩阵 D (3x3)
    c = E / (1.0 - mu ** 2)
    D = c * np.array([
        [1.0, mu, 0.0],
        [mu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - mu) / 2.0],
    ])

    # 3×3 高斯积分点和权重
    gp = np.sqrt(3.0 / 5.0)  # ≈ 0.7745966692414834
    gps_1d = [-gp, 0.0, gp]
    wts_1d = [5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0]

    K = np.zeros((16, 16))

    for i_xi in range(3):
        for i_eta in range(3):
            xi = gps_1d[i_xi]
            eta = gps_1d[i_eta]
            w = wts_1d[i_xi] * wts_1d[i_eta]

            dN = _shape_derivs(xi, eta)  # (8, 2)

            J = dN.T @ xy
            detJ = np.linalg.det(J)
            invJ = np.linalg.inv(J)

            dNdx = dN @ invJ  # (8, 2)

            B = np.zeros((3, 16))
            for i in range(8):
                col = i * 2
                B[0, col] = dNdx[i, 0]
                B[1, col + 1] = dNdx[i, 1]
                B[2, col] = dNdx[i, 1]
                B[2, col + 1] = dNdx[i, 0]

            K += w * abs(detJ) * thickness * (B.T @ D @ B)

    return K


def test_1():
    """单位正方形单元的基本测试"""
    nodes = [[0, 0], [1, 0], [1, 1], [0, 1],
             [0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5]]
    E = 1.0
    mu = 0.2
    thickness = 1.0
    Ke = calc_stiffness(nodes, E, mu, thickness)
    print(f"Shape: {Ke.shape}")
    print(f"Symmetric: {np.allclose(Ke, Ke.T)}")
    eigvals = np.linalg.eigvalsh(Ke)
    near_zero = np.sum(np.abs(eigvals) < 1e-6)
    positive = np.sum(eigvals > 1e-6)
    print(f"Near-zero eigenvalues: {near_zero} (expect 3)")
    print(f"Positive eigenvalues: {positive} (expect 13)")
    print(Ke)


if __name__ == '__main__':
    test_1()

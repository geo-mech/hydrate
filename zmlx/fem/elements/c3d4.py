import numpy as np


def stiffness(nodes, E, mu):
    """计算C3D4（三维四面体单元）四面体单元的刚度矩阵。

    Args:
        nodes (list, tuple): 长度为4的列表，每个元素是包含3个float的列表或元组，表示节点的三维坐标
        E (float): 弹性模量
        mu (float): 泊松比

    Returns:
        np.ndarray: 12x12的单元刚度矩阵
    """
    # 解包节点坐标
    x0, y0, z0 = nodes[0]
    x1, y1, z1 = nodes[1]
    x2, y2, z2 = nodes[2]
    x3, y3, z3 = nodes[3]

    # 计算四个向量
    v1 = np.array([x1 - x0, y1 - y0, z1 - z0])
    v2 = np.array([x2 - x0, y2 - y0, z2 - z0])
    v3 = np.array([x3 - x0, y3 - y0, z3 - z0])

    # 构造雅可比矩阵并计算行列式
    J = np.column_stack((v1, v2, v3))
    detJ = np.linalg.det(J)
    V = abs(detJ) / 6.0

    # 计算雅可比矩阵的逆
    J_inv = np.linalg.inv(J)

    # 自然导数
    natural_derivatives = [
        [-1, -1, -1],  # 节点0
        [1, 0, 0],  # 节点1
        [0, 1, 0],  # 节点2
        [0, 0, 1]  # 节点3
    ]

    # 计算每个节点的实际梯度
    gradients = []
    for i in range(4):
        natural = np.array(natural_derivatives[i])
        grad = J_inv.T @ natural  # 实际坐标中的梯度
        gradients.append(grad)

    # 构造B矩阵
    B = np.zeros((6, 12))
    for i in range(4):
        bi, ci, di = gradients[i]
        start_col = i * 3
        # ε_x, ε_y, ε_z
        B[0, start_col] = bi
        B[1, start_col + 1] = ci
        B[2, start_col + 2] = di
        # γ_xy
        B[3, start_col] = ci
        B[3, start_col + 1] = bi
        # γ_yz
        B[4, start_col + 1] = di
        B[4, start_col + 2] = ci
        # γ_xz
        B[5, start_col] = di
        B[5, start_col + 2] = bi

    # 构造D矩阵
    c = E / ((1 + mu) * (1 - 2 * mu))
    D = np.array([
        [1 - mu, mu, mu, 0, 0, 0],
        [mu, 1 - mu, mu, 0, 0, 0],
        [mu, mu, 1 - mu, 0, 0, 0],
        [0, 0, 0, 0.5 * (1 - 2 * mu), 0, 0],
        [0, 0, 0, 0, 0.5 * (1 - 2 * mu), 0],
        [0, 0, 0, 0, 0, 0.5 * (1 - 2 * mu)]
    ]) * c

    # 计算刚度矩阵
    k = V * (B.T @ D @ B)

    return k

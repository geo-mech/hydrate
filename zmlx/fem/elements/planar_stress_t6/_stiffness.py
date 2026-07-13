try:
    import numpy as np
except ImportError:
    np = None


def calc_stiffness(nodes, E: float, mu: float, thickness: float = 1.0):
    """计算平面应力状态下6节点三角形单元（T6）的刚度矩阵。

    使用面积坐标与4点Hammer数值积分。6节点二次三角形单元内应变为线性分布，
    精度远高于常应变三角形单元（CST）。

    Args:
        nodes (list, tuple): 长度为6的列表，每个元素是包含两个float的列表或元组，表示节点的坐标。
            节点顺序（逆时针）：0,1,2为角节点，3为边0-1中点，4为边1-2中点，5为边2-0中点
        E (float): 杨氏模量
        mu (float): 泊松比
        thickness (float, optional): 单元厚度，默认为1.0

    Returns:
        np.ndarray: 12x12的单元刚度矩阵
    """
    assert np is not None, "numpy没有安装"
    assert E > 0, f"杨氏模量必须大于0, but got {E}"
    assert 0 <= mu < 0.5, f"泊松比必须在0到0.5之间, but got {mu}"
    assert thickness > 0, f"单元厚度必须大于0, but got {thickness}"

    # 解包节点坐标（仅使用角节点计算面积和几何参数）
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]
    x2, y2 = nodes[2]

    # 计算三角形面积
    area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    assert area > 0, "三角形面积必须大于0"

    # 计算几何参数b_i和c_i（与CST相同）
    b = [y1 - y2, y2 - y0, y0 - y1]
    c = [x2 - x1, x0 - x2, x1 - x0]

    # 平面应力弹性矩阵 D (3x3)
    factor = E / (1.0 - mu ** 2)
    D = factor * np.array([
        [1.0, mu, 0.0],
        [mu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - mu) / 2.0],
    ])

    # 4点Hammer积分（三角形域上的Gauss积分）
    # 权重归一化：sum(w) = 1.0
    hammer_pts = [
        (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0, -27.0 / 48.0),
        (3.0 / 5.0, 1.0 / 5.0, 1.0 / 5.0, 25.0 / 48.0),
        (1.0 / 5.0, 3.0 / 5.0, 1.0 / 5.0, 25.0 / 48.0),
        (1.0 / 5.0, 1.0 / 5.0, 3.0 / 5.0, 25.0 / 48.0),
    ]

    K = np.zeros((12, 12))

    for L1, L2, L3, w in hammer_pts:
        # 6个节点的形函数对面积坐标的导数 dNdL (6, 3)
        dNdL = np.array([
            [4.0 * L1 - 1.0, 0.0, 0.0],            # 角节点0: N0 = (2L1-1)*L1
            [0.0, 4.0 * L2 - 1.0, 0.0],            # 角节点1: N1 = (2L2-1)*L2
            [0.0, 0.0, 4.0 * L3 - 1.0],            # 角节点2: N2 = (2L3-1)*L3
            [4.0 * L2, 4.0 * L1, 0.0],              # 边中点3 (0-1): N3 = 4*L1*L2
            [0.0, 4.0 * L3, 4.0 * L2],              # 边中点4 (1-2): N4 = 4*L2*L3
            [4.0 * L3, 0.0, 4.0 * L1],              # 边中点5 (2-0): N5 = 4*L3*L1
        ])

        # 链式法则: dN/dx = dN/dL * [b0,b1,b2]^T / (2A)
        inv_2A = 1.0 / (2.0 * area)
        dNdx = (dNdL[:, 0] * b[0] + dNdL[:, 1] * b[1] + dNdL[:, 2] * b[2]) * inv_2A
        dNdy = (dNdL[:, 0] * c[0] + dNdL[:, 1] * c[1] + dNdL[:, 2] * c[2]) * inv_2A

        # 组装应变-位移矩阵 B (3x12)
        B = np.zeros((3, 12))
        for i in range(6):
            col = i * 2
            B[0, col] = dNdx[i]       # ε_xx: ∂u/∂x
            B[1, col + 1] = dNdy[i]   # ε_yy: ∂v/∂y
            B[2, col] = dNdy[i]       # γ_xy: ∂u/∂y
            B[2, col + 1] = dNdx[i]   # γ_xy: ∂v/∂x

        # 累加: K += w * thickness * area * B.T @ D @ B
        K += w * thickness * area * (B.T @ D @ B)

    return K


def test_1():
    """标准直角三角形的基本测试"""
    nodes = [[0, 0], [1, 0], [0, 1], [0.5, 0], [0.5, 0.5], [0, 0.5]]
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
    print(f"Positive eigenvalues: {positive} (expect 9)")
    print(Ke)


if __name__ == '__main__':
    test_1()

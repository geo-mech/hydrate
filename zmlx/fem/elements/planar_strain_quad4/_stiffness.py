try:
    import numpy as np
except ImportError:
    np = None


def calc_stiffness(nodes, E: float, mu: float, thickness: float = 1.0):
    """计算平面应变状态下双线性四边形单元（4节点）的刚度矩阵。

    使用2×2高斯积分的等参元公式。

    Args:
        nodes (list, tuple): 长度为4的列表，每个元素是包含两个float的列表或元组，表示节点的(x, y)坐标。
            节点顺序（逆时针）：0(左下) 1(右下) 2(右上) 3(左上)
        E (float): 杨氏模量
        mu (float): 泊松比
        thickness (float, optional): 单元厚度，默认为1.0

    Returns:
        np.ndarray: 8x8的单元刚度矩阵
    """
    assert np is not None, "numpy没有安装"
    assert E > 0, f"杨氏模量必须大于0, but got {E}"
    assert 0 <= mu < 0.5, f"泊松比必须在0到0.5之间, but got {mu}"
    assert thickness > 0, f"单元厚度必须大于0, but got {thickness}"

    xy = np.array(nodes, dtype=float)
    assert xy.shape == (4, 2), f"节点坐标必须是4x2数组，但得到 {xy.shape}"

    # 平面应变弹性矩阵 D (3x3)
    c = E / ((1.0 + mu) * (1.0 - 2.0 * mu))
    D = c * np.array([
        [1.0 - mu, mu, 0.0],
        [mu, 1.0 - mu, 0.0],
        [0.0, 0.0, (1.0 - 2.0 * mu) / 2.0],
    ])

    # 2×2 高斯积分点和权重
    gp = 1.0 / np.sqrt(3.0)
    gps = [(-gp, -gp), (gp, -gp), (gp, gp), (-gp, gp)]
    wts = [1.0, 1.0, 1.0, 1.0]

    K = np.zeros((8, 8))

    for (xi, eta), w in zip(gps, wts):
        # 形函数对自然坐标的导数 dN/dxi, dN/deta，每行对应一个节点
        dN = np.array([
            [-(1.0 - eta) / 4.0, -(1.0 - xi) / 4.0],
            [(1.0 - eta) / 4.0, -(1.0 + xi) / 4.0],
            [(1.0 + eta) / 4.0, (1.0 + xi) / 4.0],
            [-(1.0 + eta) / 4.0, (1.0 - xi) / 4.0],
        ])

        # 雅可比矩阵 J = dN^T @ xy (2x2)
        J = dN.T @ xy
        detJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)

        # 形函数对物理坐标的导数
        dNdx = dN @ invJ  # (4, 2)

        # 应变-位移矩阵 B (3x8)
        B = np.zeros((3, 8))
        for i in range(4):
            col = i * 2
            B[0, col] = dNdx[i, 0]      # du/dx
            B[1, col + 1] = dNdx[i, 1]  # dv/dy
            B[2, col] = dNdx[i, 1]      # du/dy
            B[2, col + 1] = dNdx[i, 0]  # dv/dx

        K += w * abs(detJ) * thickness * (B.T @ D @ B)

    return K


def test_1():
    """单位正方形单元的基本测试"""
    nodes = [[0, 0], [1, 0], [1, 1], [0, 1]]
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
    print(f"Positive eigenvalues: {positive} (expect 5)")
    print(Ke)


if __name__ == '__main__':
    test_1()

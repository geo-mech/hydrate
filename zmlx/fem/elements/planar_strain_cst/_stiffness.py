try:
    import numpy as np
except ImportError:
    np = None


def calc_stiffness(nodes, E: float, mu: float, thickness: float = 1.0):
    """计算平面应变状态下常应变三角形单元的刚度矩阵(适用于无限厚的二维问题)

    Args:
        nodes (list, tuple): 长度为3的列表，每个元素是包含两个float的列表或元组，表示节点的坐标。
        E (float): 杨氏模量
        mu (float): 泊松比
        thickness (float, optional): 单元厚度，默认为1.0

    Returns:
        np.ndarray: 6x6的单元刚度矩阵
    """
    assert np is not None, "numpy没有安装"
    assert E > 0, f"杨氏模量必须大于0, but got {E}"
    assert 0 <= mu < 0.5, f"泊松比必须在0到0.5之间, but got {mu}"
    assert thickness > 0, f"单元厚度必须大于0, but got {thickness}"

    # 解包节点坐标
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]
    x2, y2 = nodes[2]

    # 计算三角形面积
    area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    assert area > 0, "三角形面积必须大于0"

    # 计算几何参数b_i和c_i
    b0 = y1 - y2
    b1 = y2 - y0
    b2 = y0 - y1
    c0 = x2 - x1
    c1 = x0 - x2
    c2 = x1 - x0

    # 构造应变-位移矩阵B（3x6）
    B = np.array([
        [b0, 0, b1, 0, b2, 0],
        [0, c0, 0, c1, 0, c2],
        [c0, b0, c1, b1, c2, b2]
    ]) / (2 * area)

    # 平面应变的弹性矩阵D（3x3）
    factor = E / ((1 + mu) * (1 - 2 * mu))
    D = factor * np.array([
        [1 - mu, mu, 0],
        [mu, 1 - mu, 0],
        [0, 0, (1 - 2 * mu) / 2]
    ])

    # 计算单元刚度矩阵（6x6）
    Ke = (thickness * area) * B.T @ D @ B

    return Ke


def test_1():
    nodes = [[0, 0], [1, 0], [0, 1]]
    E = 1.0
    mu = 0.2
    thickness = 1.0
    Ke = calc_stiffness(nodes, E, mu, thickness)
    print(Ke)
    """
[[ 0.76388889  0.34722222 -0.55555556 -0.20833333 -0.20833333 -0.13888889]
 [ 0.34722222  0.76388889 -0.13888889 -0.20833333 -0.20833333 -0.55555556]
 [-0.55555556 -0.13888889  0.55555556  0.          0.          0.13888889]
 [-0.20833333 -0.20833333  0.          0.20833333  0.20833333  0.        ]
 [-0.20833333 -0.20833333  0.          0.20833333  0.20833333  0.        ]
 [-0.13888889 -0.55555556  0.13888889  0.          0.          0.55555556]]
    """


if __name__ == '__main__':
    test_1()

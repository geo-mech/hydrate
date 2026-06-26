try:
    import numpy as np
except ImportError:
    np = None


def calc_stiffness(nodes, E, area=1.0):
    """
    计算纯拉压一维杆单元 Truss Element的刚度矩阵。

    Args:
        nodes (list, tuple): 长度为2的列表，每个元素是包含两个float的列表或元组，表示节点的坐标。
        E (float): 弹性模量
        area (float): 单元的横截面积(默认1.0)

    Returns:
        np.ndarray: 单元刚度矩阵
    """
    assert np is not None, "numpy is not installed"

    # 解包节点坐标
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]

    # 计算杆单元长度和方向余弦
    dx = x1 - x0
    dy = y1 - y0
    L = np.sqrt(dx * dx + dy * dy)
    c = dx / L
    s = dy / L

    # 杆单元刚度矩阵(4x4)
    # 自由度顺序: [u0, v0, u1, v1]
    k = E * area / L
    Ke = k * np.array([
        [c * c, c * s, -c * c, -c * s],
        [c * s, s * s, -c * s, -s * s],
        [-c * c, -c * s, c * c, c * s],
        [-c * s, -s * s, c * s, s * s]
    ])

    return Ke


def test_1():
    nodes = [[0, 0], [1, 0]]
    E = 1.0
    area = 1.0
    Ke = calc_stiffness(nodes, E, area)
    print(Ke)


if __name__ == '__main__':
    test_1()

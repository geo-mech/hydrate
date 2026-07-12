try:
    import numpy as np
except ImportError:
    np = None


def calc_strain(nodes, displacement):
    """计算常应变三角形单元的应变。

    Args:
        nodes (list): 原始节点坐标，格式为 [[x0,y0], [x1,y1], [x2,y2]]
        displacement (np.ndarray): 节点位移向量，形状为(6,)，顺序为 [u0, v0, u1, v1, u2, v2]

    Returns:
        np.ndarray: 应变向量 [ε_xx, ε_yy, γ_xy] (形状为(3,))
    """
    assert np is not None, "numpy没有安装"
    # 解包节点坐标
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]
    x2, y2 = nodes[2]

    # 计算三角形面积
    area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))

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

    # 计算应变: ε = B @ displacement
    strain = B @ np.asarray(displacement).reshape(-1)
    return strain

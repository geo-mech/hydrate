from zmlx.base.zml import np  # 当numpy没有安装的时候，np为None


def stiffness(nodes, E, mu, thickness=1.0):
    """计算平面应力状态下常应变三角形单元的刚度矩阵(适用于无限薄的二维问题)

    Args:
        nodes (list, tuple): 长度为3的列表，每个元素是包含两个float的列表或元组，表示节点的坐标。
        E (float): 弹性模量
        mu (float): 泊松比
        thickness (float): 单元厚度(默认1.0)

    Returns:
        np.ndarray: 6x6的单元刚度矩阵
    """

    # 解包节点坐标
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]
    x2, y2 = nodes[2]

    # 计算三角形面积[1,2](@ref)
    area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))

    # 计算几何参数b_i和c_i[1,2](@ref)
    b0 = y1 - y2
    b1 = y2 - y0
    b2 = y0 - y1

    c0 = x2 - x1
    c1 = x0 - x2
    c2 = x1 - x0

    # 构造应变-位移矩阵B(3x6)[1,3](@ref)
    B = np.array([
        [b0, 0, b1, 0, b2, 0],
        [0, c0, 0, c1, 0, c2],
        [c0, b0, c1, b1, c2, b2]
    ]) / (2 * area)

    # 平面应力的弹性矩阵D(3x3)[2,7](@ref)
    D = (E / (1 - mu ** 2)) * np.array([
        [1, mu, 0],
        [mu, 1, 0],
        [0, 0, (1 - mu) / 2]
    ])

    # 计算单元刚度矩阵(6x6)[1,2](@ref)
    Ke = (thickness * area) * B.T @ D @ B

    return Ke

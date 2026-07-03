try:
    import numpy as np
except ImportError:
    np = None


def calc_strain(nodes, displacement):
    """计算杆单元的轴向工程应变。

    Args:
        nodes (list): 节点坐标 [[x0,y0], [x1,y1]]
        displacement (np.ndarray): 节点位移向量 (4,) [u0,v0,u1,v1]

    Returns:
        float: 轴向工程应变 (L_new - L0) / L0
    """
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]

    dx = x1 - x0
    dy = y1 - y0
    L0 = np.sqrt(dx * dx + dy * dy)

    u = np.asarray(displacement).reshape(-1)
    u0, v0, u1, v1 = u[0], u[1], u[2], u[3]

    x0_new = x0 + u0
    y0_new = y0 + v0
    x1_new = x1 + u1
    y1_new = y1 + v1

    L_new = np.sqrt((x1_new - x0_new) ** 2 + (y1_new - y0_new) ** 2)

    return (L_new - L0) / L0

try:
    import numpy as np
except ImportError:
    np = None


def calc_strain(nodes, displacement, L1=1.0 / 3.0, L2=1.0 / 3.0, L3=1.0 / 3.0):
    """计算6节点三角形单元在指定面积坐标处的应变。

    Args:
        nodes (list): 节点坐标 [[x0,y0],...,[x5,y5]]，角节点0,1,2在前，边中点3,4,5在后
        displacement (np.ndarray): 节点位移向量 (12,)，顺序为 [u0,v0,u1,v1,...,u5,v5]
        L1 (float): 面积坐标 L1，默认1/3（单元形心）
        L2 (float): 面积坐标 L2，默认1/3
        L3 (float): 面积坐标 L3，默认1/3

    Returns:
        np.ndarray: 应变向量 [ε_xx, ε_yy, γ_xy] (形状为(3,))
    """
    assert np is not None, "numpy没有安装"
    assert abs(L1 + L2 + L3 - 1.0) < 1e-10, f"面积坐标之和必须为1, but got L1+L2+L3={L1+L2+L3}"

    # 解包角节点坐标
    x0, y0 = nodes[0]
    x1, y1 = nodes[1]
    x2, y2 = nodes[2]

    # 计算三角形面积
    area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))

    # 计算几何参数b_i和c_i
    b = [y1 - y2, y2 - y0, y0 - y1]
    c = [x2 - x1, x0 - x2, x1 - x0]

    # 6个节点的形函数对面积坐标的导数 dNdL (6, 3)
    dNdL = np.array([
        [4.0 * L1 - 1.0, 0.0, 0.0],            # 角节点0
        [0.0, 4.0 * L2 - 1.0, 0.0],            # 角节点1
        [0.0, 0.0, 4.0 * L3 - 1.0],            # 角节点2
        [4.0 * L2, 4.0 * L1, 0.0],              # 边中点3 (0-1)
        [0.0, 4.0 * L3, 4.0 * L2],              # 边中点4 (1-2)
        [4.0 * L3, 0.0, 4.0 * L1],              # 边中点5 (2-0)
    ])

    # 链式法则求物理导数
    inv_2A = 1.0 / (2.0 * area)
    dNdx = (dNdL[:, 0] * b[0] + dNdL[:, 1] * b[1] + dNdL[:, 2] * b[2]) * inv_2A
    dNdy = (dNdL[:, 0] * c[0] + dNdL[:, 1] * c[1] + dNdL[:, 2] * c[2]) * inv_2A

    # 组装B矩阵 (3x12)
    B = np.zeros((3, 12))
    for i in range(6):
        col = i * 2
        B[0, col] = dNdx[i]
        B[1, col + 1] = dNdy[i]
        B[2, col] = dNdy[i]
        B[2, col + 1] = dNdx[i]

    # 计算应变: ε = B @ displacement
    strain = B @ np.asarray(displacement).reshape(-1)
    return strain

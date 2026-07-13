from zmlx.fem.elements.planar_stress_t6._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu, L1=1.0 / 3.0, L2=1.0 / 3.0, L3=1.0 / 3.0):
    """计算6节点三角形单元在指定面积坐标处的应力（平面应力）。

    Args:
        nodes (list): 节点坐标 [[x0,y0],...,[x5,y5]]
        displacement (np.ndarray): 节点位移向量 (12,) [u0,v0,...,u5,v5]
        E (float): 杨氏模量
        mu (float): 泊松比
        L1 (float): 面积坐标 L1，默认1/3（单元形心）
        L2 (float): 面积坐标 L2，默认1/3
        L3 (float): 面积坐标 L3，默认1/3

    Returns:
        np.ndarray: 应力向量 [σ_xx, σ_yy, τ_xy] (形状为(3,))
    """
    assert np is not None, "numpy没有安装"

    # 1. 计算应变
    strain = calc_strain(nodes, displacement, L1, L2, L3)

    # 2. 构造平面应力弹性矩阵D
    factor = E / (1.0 - mu ** 2)
    D = factor * np.array([
        [1.0, mu, 0.0],
        [mu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - mu) / 2.0],
    ])

    # 3. 计算应力: σ = D @ ε
    stress = D @ strain
    return stress

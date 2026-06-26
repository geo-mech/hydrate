from zmlx.fem.elements.planar_strain_cst._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E, mu):
    """计算常应变三角形单元的应力 (DeepSeek 生成，尚未测试)

    Args:
        nodes (list): 原始节点坐标，格式为 [[x0,y0], [x1,y1], [x2,y2]]
        displacement (np.ndarray): 节点位移向量，形状为(6,)，顺序为 [u0, v0, u1, v1, u2, v2]
        E (float): 杨氏模量
        mu (float): 泊松比

    Returns:
        np.ndarray: 应力向量 [σ_xx, σ_yy, τ_xy] (形状为(3,))
    """
    assert np is not None, "numpy没有安装"
    # 1. 计算应变
    strain = calc_strain(nodes, displacement)  # 复用之前的应变函数

    # 2. 构造弹性矩阵D
    factor = E / ((1 + mu) * (1 - 2 * mu))
    D = factor * np.array([
        [1 - mu, mu, 0],
        [mu, 1 - mu, 0],
        [0, 0, (1 - 2 * mu) / 2]
    ])

    # 3. 计算应力: σ = D @ ε
    stress = D @ strain
    return stress

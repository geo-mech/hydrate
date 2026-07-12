from zmlx.fem.elements.truss2._strain import calc_strain

try:
    import numpy as np
except ImportError:
    np = None


def calc_stress(nodes, displacement, E):
    """计算杆单元的轴向应力。

    Args:
        nodes (list): 节点坐标 [[x0,y0], [x1,y1]]
        displacement (np.ndarray): 节点位移向量 (4,) [u0,v0,u1,v1]
        E (float): 杨氏模量

    Returns:
        float: 轴向应力 sigma = E * epsilon
    """
    assert np is not None, "numpy没有安装"
    strain = calc_strain(nodes, displacement)
    return E * strain

"""
给定空间的散点，计算各个散点位置的压力梯度.
todo:
    宇轩补全.
"""


def calculate_gradient2(x, y, p):
    """
    计算压力梯度 (给定坐标位置的)

    参数:
    x (list): 一维数组，表示x坐标   (1维的numpy数组)
    y (list): 一维数组，表示y坐标
    p (list): 一维数组，表示对应坐标点的压力

    返回:
    tuple: 包含两个一维数组，表示x和y方向上的压力梯度
    """
    # 初始化压力梯度数组
    grad_x = [0] * len(x)
    grad_y = [0] * len(y)

    # 计算x方向上的压力梯度
    for i in range(1, len(x)):
        dx = x[i] - x[i-1]
        dp = p[i] - p[i-1]
        grad_x[i] = dp / dx

    # 计算y方向上的压力梯度
    for i in range(1, len(y)):
        dy = y[i] - y[i-1]
        dp = p[i] - p[i-1]
        grad_y[i] = dp / dy

    return grad_x, grad_y


def calculate_gradient3(x, y, z, p):
    pass


import math

try:
    import numpy as np
except ImportError:
    np = None


def get_angle(x, y):
    """
    返回点（x,y）对应的弧度（与x轴正方向的夹角，范围[-π, π]）
    Args:
        x: 点的x坐标
        y: 点的y坐标

    Returns:
        点（x,y）对应的弧度（与x轴正方向的夹角，范围[-π, π]）
    """
    return math.atan2(y, x)


def get_norm(p):
    """
    计算向量的模长
    Args:
        p: 向量

    Returns:
        向量的模长

    """
    return np.linalg.norm(p)


def get_distance(p1, p2):
    """
    Returns the distance between two points in n-dimensional space.
    Args:
        p1: 第一个点的坐标
        p2: 第二个点的坐标

    Returns:
        两个点之间的距离
    """
    return np.linalg.norm(
        np.asarray(p1, dtype=np.float64) - np.asarray(p2, dtype=np.float64))


point_distance = get_distance


def get_center(*points):
    """
    计算多个点的中心
    Args:
        *points: 多个点的坐标

    Returns:
        多个点的中心坐标

    Raises:
        ValueError: 如果没有提供点
    """
    if not points:
        raise ValueError("至少需要提供一个点")

    # 检查维度一致性
    dims = [len(p) for p in points]
    if len(set(dims)) > 1:
        import warnings
        warnings.warn("点的维度不一致，将使用最小维度进行计算")

    n_dim = min(dims)
    truncated_points = [p[:n_dim] for p in points]
    center = np.mean(truncated_points, axis=0)
    return center


def test_1():
    """
    测试get_angle函数
    """
    from zml import Array2
    import random
    for i in range(100):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        a1 = get_angle(x, y)
        a2 = Array2(x, y).get_angle()
        print(x, y, a1, a2)


def test_2():
    """
    测试get_center函数
    """
    a = get_center([0, 0, -1], [1, 1, 1])
    print(a)


if __name__ == '__main__':
    test_2()

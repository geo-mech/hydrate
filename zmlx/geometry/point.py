import math

from zmlx.exts import get_distance, get_distance as point_distance

_keep = [point_distance]


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
    return get_distance(p, [0] * len(p))


# if __name__ == '__main__':
#     print(get_norm([3, 4]))


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
    if len(points) == 0:
        return []
    n_dim = min(len(p) for p in points)
    if n_dim == 0:
        return []
    res = [0] * n_dim
    for p in points:
        for i in range(n_dim):
            res[i] += p[i]
    return [x / len(points) for x in res]


def test_1():
    """
    测试get_angle函数
    """
    from zmlx.exts import Array2
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
    a = get_center([0, 0], [1, 1, 1])
    print(a)

# if __name__ == '__main__':
#     test_1()
#     test_2()

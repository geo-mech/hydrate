import math


def get_angle(x, y):
    """
    返回点（x,y）对应的弧度（与x轴正方向的夹角，范围[-π, π]）
    """
    return math.atan2(y, x)


def test():
    from zml import Array2
    import random
    for i in range(100):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        a1 = get_angle(x, y)
        a2 = Array2(x, y).get_angle()
        print(x, y, a1, a2)


if __name__ == '__main__':
    test()

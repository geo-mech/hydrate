import math


def point_distance(p1, p2):
    """
    Returns the distance between two points
    """
    dist = 0
    for i in range(min(len(p1), len(p2))):
        dist += math.pow(p1[i] - p2[i], 2)
    return math.sqrt(dist)


def test():
    """
    测试
    """
    p1 = (0, 0, 0)
    p2 = (1, 0, 0)
    print(point_distance(p1, p2))


if __name__ == '__main__':
    test()



# -*- coding: utf-8 -*-


from math import sqrt, pow


def get_point_distance(p1, p2):
    """
    Returns the distance between two points
    """
    assert len(p1) == len(p2), f'dimension not equal. p1 = {p1} and p2 = {p2}'
    dist = 0
    for i in range(len(p1)):
        dist += pow(p1[i] - p2[i], 2)
    return sqrt(dist)


if __name__ == '__main__':
    p1 = (0, 0, 0)
    p2 = (1, 0, 0)
    print(get_point_distance(p1, p2))


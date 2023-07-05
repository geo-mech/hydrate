from zmlx.geometry.point_distance import point_distance as get_point_distance
from zmlx.geometry.triangle_area import triangle_area


def seg_point_distance(seg, point):
    """
    返回线段<由两个点定义>和一个点之间的距离
    """
    assert len(seg) == 2, 'The segment should be defined by two points'

    a = get_point_distance(seg[0], point)
    b = get_point_distance(seg[1], point)
    c = get_point_distance(seg[0], seg[1])

    if c <= 0:
        return a

    s = triangle_area(a, b, c)
    assert s >= 0

    h = s * 2.0 / c
    if h > a:
        h = a
    if h > b:
        h = b

    if a * a - h * h >= c * c:
        return b
    if b * b - h * h >= c * c:
        return a
    else:
        return h


if __name__ == '__main__':
    p1 = (0, 0, 0)
    p2 = (1, 0, 0)
    p3 = (2, 0, 0)
    print(seg_point_distance((p1, p2), p3))


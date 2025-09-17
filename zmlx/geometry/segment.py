from zmlx.geometry.point import get_angle, point_distance


def get_seg_angle(x0, y0, x1, y1):
    return get_angle(x1 - x0, y1 - y0)


def get_center(p1, p2):
    return [(p1[i] + p2[i]) * 0.5 for i in range(min(len(p1), len(p2)))]


def seg_intersection(ax, ay, bx, by, cx, cy, dx, dy):
    """
    返回线段ab和线段cd的交点；如果没有交点，则返回None

    算法来自网络，已忘记具体来源，原本为C语言代码；

    by zzb. 2022-11-28
    """
    if ax == bx and ay == by or cx == dx and cy == dy:
        # Fail if either line segment is zero-length.
        return

    if ax == cx and ay == cy or bx == cx and by == cy or ax == dx and ay == dy or bx == dx and by == dy:
        # Fail if the segments share an end-point.
        return

    # (1) Translate the system so that point A is on the origin.
    bx -= ax
    by -= ay
    cx -= ax
    cy -= ay
    dx -= ax
    dy -= ay

    # Discover the length of segment A-B.
    dst_ab = (bx * bx + by * by) ** 0.5

    #  (2) Rotate the system so that point B is on the positive X axis.
    cos_ = bx / dst_ab
    sin_ = by / dst_ab

    def rotate_(x, y):
        new_x = x * cos_ + y * sin_
        y = y * cos_ - x * sin_
        x = new_x
        return x, y

    cx, cy = rotate_(cx, cy)
    dx, dy = rotate_(dx, dy)

    # Fail if segment C-D doesn't cross line A-B.
    if cy < 0. and dy < 0. or cy >= 0. and dy >= 0.:
        return

    # (3) Discover the position of the intersection point along line A-B.
    pos_ab = dx + (cx - dx) * dy / (dy - cy)

    # Fail if segment C-D crosses line A-B outside of segment A-B.
    if pos_ab < 0.0 or pos_ab > dst_ab:
        return

    #  (4) Apply the discovered position to line A-B in the
    #  original coordinate system.
    return ax + pos_ab * cos_, ay + pos_ab * sin_

def _triangle_area(a, b, c):
    """
    get the area of a triangle by the length of its edge.
        see: http://baike.baidu.com/view/1279.htm
    """
    p = (a + b + c) / 2
    p = p * (p - a) * (p - b) * (p - c)
    return p ** 0.5 if p > 0 else 0

def seg_point_distance(seg, point):
    """
    返回线段<由两个点定义>和一个点之间的距离
    """
    assert len(seg) == 2, 'The segment should be defined by two points'

    a = point_distance(seg[0], point)
    b = point_distance(seg[1], point)
    c = point_distance(seg[0], seg[1])

    if c <= 0.0:
        return a

    s = _triangle_area(a, b, c)
    assert s >= 0

    h = s * 2 / c
    if h > a:
        h = a
    if h > b:
        h = b

    if a ** 2 - h ** 2 >= c ** 2:
        return b
    if b ** 2 - h ** 2 >= c ** 2:
        return a
    else:
        return h


def test():
    """
    测试
    """
    ax, ay, bx, by = 0, 0, 1, 1
    cx, cy, dx, dy = 0, 1, 1, 0
    print(seg_intersection(ax, ay, bx, by, cx, cy, dx, dy))

    ax, ay, bx, by = 0, 0, 1, 0
    cx, cy, dx, dy = 0, 0, 0, 1
    print(seg_intersection(ax, ay, bx, by, cx, cy, dx, dy))


if __name__ == '__main__':
    test()

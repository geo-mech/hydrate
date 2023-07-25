from math import sqrt


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
    dst_ab = sqrt(bx * bx + by * by)

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

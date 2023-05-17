

from zml import *


def disc3_intersect_cube(disc3, lr, rr):
    """
    返回一个三维的圆盘，是否经过一个六面体网格<圆盘整体位于六面体内部则不算>
    """
    assert len(lr) == 3 and len(rr) == 3
    assert isinstance(disc3, Disc3)

    x0, y0, z0 = lr
    x1, y1, z1 = rr

    for x in (x0, x1):
        for y in (y0, y1):
            if disc3.get_intersection(p1=(x, y, z0), p2=(x, y, z1)) is not None:
                return True

    for y in (y0, y1):
        for z in (z0, z1):
            if disc3.get_intersection(p1=(x0, y, z), p2=(x1, y, z)) is not None:
                return True

    for z in (z0, z1):
        for x in (x0, x1):
            if disc3.get_intersection(p1=(x, y0, z), p2=(x, y1, z)) is not None:
                return True

    return False


if __name__ == '__main__':
    disc = Disc3(radi=1.0)
    print(disc3_intersect_cube(disc, lr=(0, 0, -0.1), rr=(0.1, 0.1, 0.1)))
    print(disc3_intersect_cube(disc, lr=(2, 2, -0.1), rr=(2.1, 2.1, 0.1)))

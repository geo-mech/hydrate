from zmlx.geometry.base import point_distance as get_distance
from zmlx.geometry.base import seg_intersection


def get_area(v3):
    """
    返回一个裂缝的面积
    """
    assert len(v3) == 6
    x0, y0, z0, x1, y1, z1 = v3
    return get_distance((x0, y0), (x1, y1)) * abs(z0 - z1)


def intersected(a, b):
    """
    返回两个给定的竖直裂缝a和b是否相交
    """
    if a is None or b is None:
        return False
    assert len(a) == 6 and len(b) == 6
    az0, az1 = a[2], a[5]
    bz0, bz1 = b[2], b[5]
    if max(bz0, bz1) <= min(az0, az1):
        return False
    if min(bz0, bz1) >= max(az0, az1):
        return False
    xy = seg_intersection(*a[0: 2], *a[3: 5], *b[0: 2], *b[3: 5])
    return xy is not None

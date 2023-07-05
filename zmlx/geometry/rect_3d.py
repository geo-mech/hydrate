"""
定义三维矩形以及相关的基本操作. 利用9个浮点数（<矩形中心坐标>以及<相邻两条边的中心坐标>）组成的list或者tuple来表示一个三维矩形.

除此之外，有一种特例，就是拟三维的矩形(v3)，这种矩形竖直，利用两个相对的顶点坐标，共6个浮点数表示.

张召彬 2023-6-21
"""

from zmlx.geometry.point_distance import point_distance as get_distance
from zmlx.geometry.rect_v3 import get_area as v3_area, intersected as v3_intersected

__all__ = ['from_v3', 'to_v3', 'get_rc3', 'set_rc3', 'get_v3', 'set_v3', 'get_cent', 'get_area', 'v3_area',
           'get_vertexes', 'v3_intersected']


def from_v3(v3):
    """
    将竖直的裂缝（用6个数字表示）修改为用9个数字（矩形中心坐标和两个相邻边的中心坐标）表示的三维矩形的形式
    """
    if v3 is None:
        return
    else:
        x0, y0, z0, x1, y1, z1 = v3
        p0 = __cen([x0, y0, z0], [x1, y1, z1])
        p1 = [(x0 + x1) / 2, (y0 + y1) / 2, z1]
        p2 = [x0, y0, (z0 + z1) / 2]
        return p0 + p1 + p2


def to_v3(rc3):
    """
    将三维裂缝(9个数字表示)修改为利用6个数字表示的拟三维矩形的形式(注意必须确保原始的数据确实是拟三维的，否则会由不可预知的错误)
    """
    if rc3 is None:
        return
    else:
        x0, y0, z0, x1, y1, z1, x2, y2, z2 = rc3
        p1 = __cen([x1, y1, z1], [x2, y2, z2])
        p2 = __sym(p1, [x0, y0, z0])
        p3 = __sym([x0, y0, z0], p2)
        return p2 + p3


def get_rc3(cell, keys):
    """
    读取属性，返回rc3格式的三维矩形.
    """
    rc3 = []
    for i in (keys.x0, keys.y0, keys.z0,
              keys.x1, keys.y1, keys.z1,
              keys.x2, keys.y2, keys.z2):
        v = cell.get_attr(i)
        if v is None:
            return
        else:
            rc3.append(v)
    return rc3


def set_rc3(cell, rc3, keys):
    """
    设置cell的rc3属性.
    """
    if cell is None:
        return

    if rc3 is None:
        rc3 = [1.0e200, ] * 9

    assert len(rc3) >= 9
    cell.set_attr(keys.x0, rc3[0])
    cell.set_attr(keys.y0, rc3[1])
    cell.set_attr(keys.z0, rc3[2])

    cell.set_attr(keys.x1, rc3[3])
    cell.set_attr(keys.y1, rc3[4])
    cell.set_attr(keys.z1, rc3[5])

    cell.set_attr(keys.x2, rc3[6])
    cell.set_attr(keys.y2, rc3[7])
    cell.set_attr(keys.z2, rc3[8])


def get_v3(cell, keys):
    """
    返回用6个浮点数表示的竖直三维的裂缝
    """
    rc3 = get_rc3(cell, keys)
    if rc3 is None:
        return
    else:
        return to_v3(get_rc3(cell, keys))


def set_v3(cell, v3, keys):
    """
    设置用6个浮点数表示的竖直三维的裂缝
    """
    if v3 is not None:
        set_rc3(cell, from_v3(v3), keys)


def get_cent(rc3):
    """
    返回三维矩形的中心点坐标
    """
    if rc3 is not None:
        return rc3[0: 3]


def get_area(rc3):
    """
    返回三维矩形的面积
    """
    if rc3 is not None:
        assert len(rc3) >= 9
        a = get_distance(rc3[0: 3], rc3[3: 6])
        b = get_distance(rc3[0: 3], rc3[6: 9])
        return a * b * 4.0


def __cen(x, y):
    """
    返回点x和y的中心点
    """
    if x is not None and y is not None:
        return [(x[i] + y[i]) / 2 for i in range(3)]


def __sym(c, x):
    """
    返回x关于中心点x的对称点
    """
    if c is not None and x is not None:
        return [c[i] * 2 - x[i] for i in range(3)]


def get_vertexes(rc3):
    """
    返回三维矩形4个顶点的坐标
    """
    if rc3 is None:
        return

    p0 = rc3[0: 3]

    p1 = rc3[3: 6]
    p2 = rc3[6: 9]
    p3 = __sym(p0, p1)
    p4 = __sym(p0, p2)

    p5 = __cen(p1, p2)
    p6 = __cen(p2, p3)
    p7 = __cen(p3, p4)
    p8 = __cen(p4, p1)

    p1 = __sym(p5, p0)
    p2 = __sym(p6, p0)
    p3 = __sym(p7, p0)
    p4 = __sym(p8, p0)

    return p1, p2, p3, p4

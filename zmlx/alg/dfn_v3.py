"""
用以管理竖直三维的离散裂缝网络
"""

from zml import *
from zmlx.alg.linspace import linspace
from zmlx.alg.clamp import clamp
from zmlx.alg.loadtxt import loadtxt
from zmlx.alg.opath import opath
from zmlx.alg.seg_intersection import seg_intersection
import random


def create(box=None, p21=None, angles=None, lengths=None, heights=None, l_min=None):
    """
    创建一个拟三维的DFN: 裂缝面都垂直于x-y平面.
    :param box: 坐标的范围，格式为: x_min, y_min, z_min, x_max, y_max, z_max
    :param p21: 在二维平面上裂缝的密度
    :param angles: 裂缝的角度
    :param lengths: 裂缝的长度
    :param heights: 裂缝的高度
    :param l_min: 裂缝允许的最近的距离
    :return: 三维裂缝数据，格式: x0, y0, z0, x1, y1, z1
    创建时间:
        2023-5-3
    """
    if box is None:
        box = [-50, -150, -25, 50, 150, 25]
    if p21 is None:
        p21 = 1
    if angles is None:
        angles = [0.0, 1.57]
    if lengths is None:
        lengths = linspace(10, 50, 100)
    if heights is None:
        heights = linspace(5, 25, 100)
    if l_min is None:
        l_min = 0.1

    assert len(box) == 6
    x_min, y_min, z_min, x_max, y_max, z_max = box

    dfn2 = Dfn2()
    dfn2.range = (x_min, y_min, x_max, y_max)
    dfn2.add_frac(angles=angles, lengths=lengths,
                  p21=p21, l_min=l_min)

    fractures = []

    for f2 in dfn2.get_fractures():
        x0, y0, x1, y1 = f2
        z = random.uniform(z_min, z_max)
        assert len(heights) >= 1
        h = heights[round(random.uniform(0, len(heights) - 1))]
        z0 = z - h / 2
        z1 = z + h / 2
        z0 = clamp(z0, z_min, z_max)
        z1 = clamp(z1, z_min, z_max)
        fractures.append([x0, y0, z0, x1, y1, z1])

    return fractures


def save_c14(path, fractures):
    """
    将裂缝打印到一个14列的文件中，供matlab绘图用
    """
    with open(make_parent(path), 'w') as file:
        for f3 in fractures:
            x0, y0, z0, x1, y1, z1 = f3
            file.write(f'{x0}  {x0}  {x1}  {x1}  {y0}  {y0}  {y1}  {y1}   {z0}  {z1}  {z0}  {z1}  {0.0}  {0.0} \n')


def save(path, fractures):
    """
    将拟三维的裂缝保存到文件
    """
    with open(make_parent(path), 'w') as file:
        for f3 in fractures:
            for x in f3:
                file.write(f'{x}\t')
            file.write('\n')


def load(path):
    """
    读取拟三维的裂缝
    """
    return loadtxt(path)


def parse(f3):
    """
    解析 create 函数存储的，或者是返回的裂缝数据; 其中f3应该包含6个元素，或者至少包含12个元素.
    返回裂缝所在的坐标系，以及裂缝的宽度和高度.
    """
    if isinstance(f3, str):
        f3 = [float(w) for w in f3.split()]

    if len(f3) < 6:
        return

    if len(f3) == 6:
        x0, y0, z0, x1, y1, z1 = f3
    else:
        assert len(f3) >= 12
        x0 = f3[0]
        y0 = f3[4]
        z0 = f3[8]
        x1 = f3[2]
        y1 = f3[6]
        z1 = f3[9]

    o = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    x = x1 - x0, y1 - y0, 0
    y = 0, 0, 1
    c = Coord3(origin=o, xdir=x, ydir=y)
    w = get_distance((x0, y0), (x1, y1))
    h = abs(z0 - z1)

    return c, w, h


def intersected(a, b):
    """
    返回两个给定的竖直裂缝a和b是否相交
    """
    assert len(a) == 6 and len(b) == 6
    az0, az1 = a[2], a[5]
    bz0, bz1 = b[2], b[5]
    if max(bz0, bz1) <= min(az0, az1):
        return False
    if min(bz0, bz1) >= max(az0, az1):
        return False
    xy = seg_intersection(*a[0: 2], *a[3: 5], *b[0: 2], *b[3: 5])
    return xy is not None


def get_area(f3):
    """
    返回一个裂缝的面积
    """
    assert len(f3) == 6
    x0, y0, z0, x1, y1, z1 = f3
    return get_distance((x0, y0), (x1, y1)) * abs(z0 - z1)


def set_cell(cell, f3, ca_s=None,
             ca_x0=None, ca_x1=None, ca_x2=None, ca_x3=None,
             ca_y0=None, ca_y1=None, ca_y2=None, ca_y3=None,
             ca_z0=None, ca_z1=None, ca_z2=None, ca_z3=None,
             ):
    assert len(f3) == 6
    x0, y0, z0, x1, y1, z1 = f3
    cell.pos = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    if ca_s is not None:
        cell.set_attr(ca_s, get_area(f3))

    # 下面的一些属性，主要用于Matlab三维绘图的输出.
    if ca_x0 is not None:
        cell.set_attr(ca_x0, x0)
    if ca_x1 is not None:
        cell.set_attr(ca_x1, x0)
    if ca_x2 is not None:
        cell.set_attr(ca_x2, x1)
    if ca_x3 is not None:
        cell.set_attr(ca_x3, x1)

    if ca_y0 is not None:
        cell.set_attr(ca_y0, y0)
    if ca_y1 is not None:
        cell.set_attr(ca_y1, y0)
    if ca_y2 is not None:
        cell.set_attr(ca_y2, y1)
    if ca_y3 is not None:
        cell.set_attr(ca_y3, y1)

    if ca_z0 is not None:
        cell.set_attr(ca_z0, z0)
    if ca_z1 is not None:
        cell.set_attr(ca_z1, z1)
    if ca_z2 is not None:
        cell.set_attr(ca_z2, z0)
    if ca_z3 is not None:
        cell.set_attr(ca_z3, z1)


def add_fractures(seepage, fractures, **kwargs):
    """
    将给定的竖直三维的裂缝添加到渗流模型. 其中ca_s定义Cell对应的裂缝的面积. ca_x0到ca_z3共12个参数，用以定义一个三维的矩形，用于后期的绘图.
    """
    assert isinstance(seepage, Seepage)
    if len(fractures) == 0:
        return

    average_s = 0
    for f3 in fractures:
        average_s += get_area(f3)
    average_s /= len(fractures)

    temp = []
    for f3 in fractures:
        if get_area(f3) > average_s * 0.025:  # 抛弃那些特别小的裂缝
            temp.append(f3)

    fractures = temp
    if len(fractures) == 0:
        return

    cell_n = seepage.cell_number  # 初始的Cell数量

    for f3 in fractures:
        set_cell(seepage.add_cell(), f3, **kwargs)

    for i0 in range(len(fractures)):
        f0 = fractures[i0]
        for i1 in range(i0 + 1, len(fractures)):
            f1 = fractures[i1]
            if intersected(f0, f1):
                seepage.add_face(seepage.get_cell(cell_n + i0), seepage.get_cell(cell_n + i1))


def test1():
    """
    测试 create
    """
    fractures = create()
    print(f'dfn created. n = {len(fractures)}')
    save_c14(opath('dfn3.txt'), fractures)


def test2():
    """
    测试 parse
    """
    c, w, h = parse('0.6188042427042346  0.6188042427042346  0.1912180358076829  0.1912180358076829  '
                    '0.8593401898251294  0.8593401898251294  0.85934018982513    0.85934018982513 '
                    '0                   0.1916603353240886  0                   0.1916603353240886 '
                    ' 0.0  0.0 ')

    print(c)
    print(w)
    print(h)

    gc = Coord3()
    print(gc.view(coord=c, o=Array3(x=-w / 2, y=-h / 2, z=0)))
    print(gc.view(coord=c, o=Array3(x=-w / 2, y=h / 2, z=0)))
    print(gc.view(coord=c, o=Array3(x=w / 2, y=-h / 2, z=0)))
    print(gc.view(coord=c, o=Array3(x=w / 2, y=h / 2, z=0)))


def test3():
    a = [0, 0, 0, 1, 1, 1]
    b = [0, 1, 0, 1, 0, -1]
    print(intersected(a, b))


def test4():
    seepage = Seepage()
    fractures = create()
    print(f'count of fractures = {len(fractures)}')
    add_fractures(seepage, fractures, ca_s=0,
                  ca_x0=1, ca_x1=2, ca_x2=3, ca_x3=4,
                  ca_y0=5, ca_y1=6, ca_y2=7, ca_y3=8,
                  ca_z0=9, ca_z1=10, ca_z2=11, ca_z3=12, )
    seepage.save(opath('seepage.xml'))
    print(seepage)


if __name__ == '__main__':
    test4()

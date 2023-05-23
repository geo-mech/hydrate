from zmlx import *
from zmlx.alpha.hf2.Attrs import *
from zmlx.alg.loadtxt import loadtxt
from zmlx.alpha.hf2.save_c14 import save_c14
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

#
# def save_c14(path, fractures):
#     """
#     将裂缝打印到一个14列的文件中，供matlab绘图用
#     """
#     with open(make_parent(path), 'w') as file:
#         for f3 in fractures:
#             x0, y0, z0, x1, y1, z1 = f3
#             file.write(f'{x0}  {x0}  {x1}  {x1}  {y0}  {y0}  {y1}  {y1}   {z0}  {z1}  {z0}  {z1}  {0.0}  {0.0} \n')


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


def get_area(f3):
    """
    返回一个裂缝的面积
    """
    assert len(f3) == 6
    x0, y0, z0, x1, y1, z1 = f3
    return get_distance((x0, y0), (x1, y1)) * abs(z0 - z1)


def add_fractures(model, fractures):
    """
    将给定的竖直三维的裂缝添加到渗流模型. 每一个裂缝，建立一个和它对应的Cell;
        Cell具有如下属性:
            位置 pos
            面积 s
            三维矩形 rect3
            -- 其它所有的Cell属性均未设置.

        Face所有属性均没有设置
            仅添加Face，没有进行任何初始化.
    """
    assert isinstance(model, Seepage)
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

    cell_n0 = model.cell_number  # 初始的Cell数量
    ca = CellAttrs(model)

    for f3 in fractures:
        cell = model.add_cell()
        assert len(f3) == 6
        x0, y0, z0, x1, y1, z1 = f3
        cell.pos = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        ca.set_fs(cell, get_area(f3))
        ca.set_rect3(cell, x0, y0, z0, x1, y1, z1)

    for i0 in range(cell_n0, model.cell_number):
        c0 = model.get_cell(i0)
        for i1 in range(i0 + 1, model.cell_number):
            c1 = model.get_cell(i1)
            if ca.intersected(c0, c1):
                model.add_face(c0, c1)

    # 建立和之前已经存在的Cell之间的联系
    for i0 in range(0, cell_n0):
        c0 = model.get_cell(i0)
        for i1 in range(cell_n0, model.cell_number):
            c1 = model.get_cell(i1)
            if ca.intersected(c0, c1):
                model.add_face(c0, c1)


def add_fracture(model, f3, dx, dy):
    """
    在模型中添加一个竖直的裂缝，将这个竖直的裂缝剖分未多个单元，并且建立和之前的Cell的联系
        dx 为裂缝长度方向上的网格大小
        dy 为裂缝高度方向上的网格大小

    对于新添加的Cell和Face
        Cell具有如下属性:
            位置 pos
            面积 s
            三维矩形 rect3
            -- 其它所有的Cell属性均未设置.

        Face所有属性均没有设置
            仅添加Face，没有进行任何初始化.
    """
    assert isinstance(model, Seepage)

    c1, w, h = parse(f3)
    assert isinstance(c1, Coord3)
    assert w > 0 and h > 0
    c2 = Coord3()

    jx = max(2, round(w / dx))
    jy = max(2, round(h / dy))

    boxes = []
    mesh = SeepageMesh.create_cube(x=linspace(-w / 2, w / 2, jx),
                                   y=linspace(-h / 2, h / 2, jy),
                                   z=(-1, 1), boxes=boxes)
    assert len(boxes) == mesh.cell_number

    cell_n0 = model.cell_number  # 初始的Cell数量
    ca = CellAttrs(model)
    area = get_area(f3) / mesh.cell_number

    for idx in range(mesh.cell_number):
        cell = model.add_cell()
        assert isinstance(cell, Seepage.Cell)
        ca.set_fs(cell, area)

        p1 = Array3.from_list(mesh.get_cell(idx).pos)
        p2 = c2.view(c1, p1)
        cell.pos = p2

        x0, y0, z0, x1, y1, z1 = boxes[idx]
        lr = c2.view(c1, Array3.from_list([x0, y0, 0]))
        rr = c2.view(c1, Array3.from_list([x1, y1, 0]))
        ca.set_rect3(cell, *lr.to_list(), *rr.to_list())

    for face in mesh.faces:
        assert isinstance(face, SeepageMesh.Face)
        i0 = face.cell_i0 + cell_n0
        i1 = face.cell_i1 + cell_n0
        model.add_face(model.get_cell(i0), model.get_cell(i1))

    # 建立和之前已经存在的Cell之间的联系
    for i0 in range(0, cell_n0):
        c0 = model.get_cell(i0)
        for i1 in range(cell_n0, model.cell_number):
            c1 = model.get_cell(i1)
            if ca.intersected(c0, c1):
                model.add_face(c0, c1)


def test_1():
    model = Seepage()
    fractures = create(p21=0.1)
    print(f'count of fractures = {len(fractures)}')
    add_fractures(model, fractures)
    print(model)
    add_fractures(model, fractures)
    print(model)


def test_2():
    model = Seepage()
    add_fracture(model, [-20, -40, -10, 20, 40, 10], 1, 1)
    add_fracture(model, [20, -40, -10, -20, 40, 10], 1, 1)
    print(model)
    save_c14(opath('test.c14'), model)


if __name__ == '__main__':
    test_2()

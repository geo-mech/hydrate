# ** desc = '压降漏斗的形成演化（两个漏斗之间的相互影响）'

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p):
    """
    设置一个Cell的属性
    Args:
        c: 要设置属性的Cell对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


def add_cell(model: Seepage, x, y, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    c = model.add_cell()
    set_cell(c, x, y, v, p)


def add_face(model: Seepage, i0, i1, area, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        i0: 第一个单元的索引
        i1: 第二个单元的索引
        area: 流动的横截面积，m2
        perm: 渗透率，单位：m2
    """
    dist = get_distance(model.get_cell(i0).pos, model.get_cell(i1).pos)
    face = model.add_face(i0, i1)
    face.cond = area * perm / dist


def pressure_items(model: Seepage, jx, jy):
    """
    显示模型中所有Cell的压力分布
    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向
    """
    x = np.reshape(as_numpy(model).cells.x, (jx, jy))
    y = np.reshape(as_numpy(model).cells.y, (jx, jy))
    p = np.reshape(as_numpy(model).cells.pre / 1e6, (jx, jy))
    return [item('surf', x, y, p * 20 - 15, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
            item('contourf', x, y, p)
            ]


def test():
    """
    运行测试：创建模型、运行、绘制结果
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 添加一列Cell。其中第一个和最后一个Cell的体积设置为无穷大 (1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    for ix in range(jx):
        for iy in range(jy):
            if ix == 0 or ix == jx - 1 or iy == 0 or iy == jy - 1:
                add_cell(model, x=ix, y=iy, v=1e6, p=2.0e6)  # 在四个边上，将体积设置为无穷大，确保压力固定
            else:
                add_cell(model, x=ix, y=iy, v=1, p=2.0e6)

    # 设置压力固定（将Cell的体积设置为无穷大）
    cent = model.get_nearest_cell(pos=[jx * 0.3, jy * 0.3, 0])
    set_cell(cent, x=None, y=None, v=1e6, p=1e6)

    cent = model.get_nearest_cell(pos=[jx * 0.7, jy * 0.7, 0])
    set_cell(cent, x=None, y=None, v=1e6, p=1e6)

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for ix in range(jx):
        for iy in range(jy):
            idx = iy + ix * jy
            if ix < jx - 1:
                add_face(model, idx, idx + jy, area=1, perm=1.0e-15)
            if iy < jy - 1:
                add_face(model, idx, idx + 1, area=1, perm=1.0e-15)

    # 迭代并且绘图显示
    step_max = 50
    for step in range(step_max):
        print(f'step = {step}/{step_max}')
        model.iterate(dt=1.0e6)
        items = pressure_items(model, jx, jy)
        plot(add_axes3, add_items, *items,
             xlabel="x/m", ylabel="y/m", title=f'Pressure Distribution, step = {step}',
             aspect='equal', tight_layout=True,
             caption='压力场')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)

# ** desc = '压降漏斗的形成演化（两个漏斗之间的相互影响）'
#
# 【物理问题描述】
# 本模型模拟两个生产井同时开采时，压降漏斗之间的相互影响。在40x40的二维区域中，
# 四周边界固定压力2MPa，内部有两个低压点（压力1MPa），分别位于(0.3,0.3)和(0.7,0.7)
# 附近。随着开采进行，两个压降漏斗逐渐扩展并相互叠加，形成复杂的压力场分布。
#
# 【建模技术要点】
# 1. 与pressure.py类似，但有两个低压中心（模拟两井同时生产）
# 2. 通过体积极大（1e6）的Cell实现定压边界
# 3. 使用model.iterate（而非tfc.iterate_flow）进行迭代
# 4. 使用model.get_recommended_dt自动推荐下一步长
# 5. 使用3D曲面图直观展示压力场的三维形态和漏斗叠加效果
# 6. 使用旧版plot/add_axes3/add_items/item API进行可视化
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 边界压力: 四周2MPa
# 井底压力: 两个井点均为1MPa，分别位于(12,12)和(28,28)附近
# 渗透率: 1.0e-15 m^2
# 迭代步数: 50步

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p):
    """
    设置一个Cell的属性

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m），若为None则不设置位置
        y: 单元的位置，y坐标（单位：m），若为None则不设置位置
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    # 设置孔隙属性
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    # 根据当前压力计算流体体积
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


def add_cell(model: Seepage, x, y, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标（单位：m）
        y: 单元的位置，y坐标（单位：m）
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
    生成压力分布的三维可视化数据

    使用曲面图显示压力场的三维形态，可清晰看到两个压降漏斗
    各自扩展并逐步重叠的过程。

    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向

    Returns:
        list: 包含曲面图和等值线图的绘图项列表
    """
    x = np.reshape(as_numpy(model).cells.x, (jx, jy))
    y = np.reshape(as_numpy(model).cells.y, (jx, jy))
    p = np.reshape(as_numpy(model).cells.pre / 1e6, (jx, jy))
    return [item('surf', x, y, p * 20 - 15, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
            item('contourf', x, y, p)
            ]


def test():
    """
    主测试函数：创建两个压降漏斗模型并求解。

    模拟40x40区域中，四周定压2MPa、两个位置定压1MPa时，
    两个压降漏斗的形成及相互影响过程。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 添加Cell。其中边界Cell的体积设置为无穷大(1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    for ix in range(jx):
        for iy in range(jy):
            # 边界上的Cell体积设为无穷大，保持压力2MPa不变
            if ix == 0 or ix == jx - 1 or iy == 0 or iy == jy - 1:
                add_cell(model, x=ix, y=iy, v=1e6, p=2.0e6)  # 四周定压2MPa
            else:
                add_cell(model, x=ix, y=iy, v=1, p=2.0e6)

    # 设置两个低压中心（模拟两个生产井）
    # 第一个井在(12, 12)附近，压力1MPa
    cent = model.get_nearest_cell(pos=[jx * 0.3, jy * 0.3, 0])
    set_cell(cent, x=None, y=None, v=1e6, p=1e6)

    # 第二个井在(28, 28)附近，压力1MPa
    cent = model.get_nearest_cell(pos=[jx * 0.7, jy * 0.7, 0])
    set_cell(cent, x=None, y=None, v=1e6, p=1e6)

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for ix in range(jx):
        for iy in range(jy):
            idx = iy + ix * jy  # 一维索引（按列主序存储）
            if ix < jx - 1:
                # 添加x方向的Face
                add_face(model, idx, idx + jy, area=1, perm=1.0e-15)
            if iy < jy - 1:
                # 添加y方向的Face
                add_face(model, idx, idx + 1, area=1, perm=1.0e-15)

    # 迭代并且绘图显示
    step_max = 50  # 总迭代步数
    dv_rela = 0.5  # 体积变化相对容差
    dt = 1.0e9  # 初始时间步长，单位：s
    for step in range(step_max):
        # 执行一步渗流迭代
        r = model.iterate(dt=dt, dv_rela=dv_rela)
        print(f'step = {step}/{step_max}, dt = {r.get("dt")}')
        # 根据前一步结果自动推荐下一步长
        dt = model.get_recommended_dt(r.get('dt'), cfl=dv_rela)
        # 生成绘图项并显示
        items = pressure_items(model, jx, jy)
        plot(add_axes3, add_items, *items,
             xlabel="x/m", ylabel="y/m",
             title=f'Pressure Distribution, step = {step}',
             aspect='equal', tight_layout=True,
             caption='压力场')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)

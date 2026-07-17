# ** desc = '压降漏斗的形成演化'
#
# 【物理问题描述】
# 本模型模拟二维多孔介质中压力降漏斗的形成和演化过程。在40x40的正方形区域中，
# 四周边界固定压力2MPa，中心一点固定压力1MPa（模拟生产井）。由于中心压力低于
# 四周，流体从四周向中心汇流，形成以中心为最低点的压力降漏斗。
#
# 【建模技术要点】
# 1. 通过设置体积极大（1e6 m^3）的Cell来实现定压边界条件
# 2. 四周所有Cell（ix=0或ix=39或iy=0或iy=39）都设为定压边界
# 3. 中心一个Cell设为定压低压（1MPa），模拟生产井
# 4. 使用3D曲面图（surf）显示压力分布的三维形态，直观展示漏斗形状
# 5. 使用旧版plot/add_axes3/add_items/item API（与新式fig API不同）
# 6. 使用tfc.set_dt和tfc.set_cfl设置迭代控制参数
# 7. 使用tfc.iterate_flow进行渗流迭代
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 边界压力: 四周2MPa，中心1MPa
# 渗透率: 1.0e-15 m^2
# 迭代步数: 50步
# 初始时间步长: 1e9 s
# 体积变化容差: 0.5

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p):
    """
    设置一个Cell的属性

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m），若为None则不设置位置
        y: 单元的位置，y坐标（单位：m），若为None则不设置位置
        v: 单元的体积，m3（设为极大值可实现定压边界）
        p: 单元的压力，Pa
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    # 设置孔隙属性：参考压力1MPa，参考体积v，压力变化范围1MPa对应体积变化0.1*v
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

    使用曲面图显示压力场的空间分布，z轴为压力值（经缩放和偏移处理），
    颜色映射为压力值，可以直观地看到压降漏斗的三维形态。

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
    # 曲面图：z轴 = p*20 - 15（将压力映射到适当的z范围，增强漏斗视觉效果）
    return [item('surf', x, y, p * 20 - 15, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
            item('contourf', x, y, p)
            ]


def test():
    """
    主测试函数：创建模型、运行、绘制结果

    模拟40x40区域中，四周定压2MPa、中心定压1MPa时压力降漏斗的形成过程。
    每步迭代后更新三维曲面图，展示漏斗的逐步扩展和深化。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 添加Cell。其中边界Cell的体积设置为无穷大(1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    for ix in range(jx):
        for iy in range(jy):
            # 在四个边上（ix==0或ix==jx-1或iy==0或iy==jy-1），体积设为无穷大，保持压力2MPa不变
            if ix == 0 or ix == jx - 1 or iy == 0 or iy == jy - 1:
                add_cell(model, x=ix, y=iy, v=1e6, p=2.0e6)  # 四周定压2MPa
            else:
                add_cell(model, x=ix, y=iy, v=1, p=2.0e6)

    # 将中心的Cell体积设为无穷大，压力设为1MPa（模拟生产井）
    cent = model.get_nearest_cell(pos=[jx / 2, jy / 2, 0])
    set_cell(cent, x=None, y=None, v=1e6, p=1e6)  # 中心定压1MPa

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
    tfc.set_dt(model, 1e9)  # 设置初始时间步长
    tfc.set_cfl(model, 0.5)  # 设置体积变化相对容差
    for step in range(step_max):
        # 执行一步渗流迭代，自动推荐步长并检查稳定性
        tfc.iterate_flow(model, recommend_dt=True, check_dt=True, modify_dt=True)
        print(f'step = {step}/{step_max}, dt = {tfc.get_dt(model, True)}')
        # 生成绘图项并显示
        items = pressure_items(model, jx, jy)
        plot(add_axes3, add_items, *items,
             xlabel="x/m", ylabel="y/m",
             title=f'Pressure Distribution, step = {step}',
             aspect='equal', tight_layout=True,
             caption='压力场')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)

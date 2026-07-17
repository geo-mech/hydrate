# ** desc = '和上一个Case相比，主要的差异，在于增加了迭代的次数'
#
# 【物理问题描述】
# 本模型模拟二维渗流中压力场随时间的演化过程。在30x20的矩形区域中，
# 左上角(0,0)固定压力2MPa（注入端），右下角(29,19)固定压力1MPa（采出端），
# 内部初始压力为1.5MPa。通过50步迭代，模拟压力场从初始状态逐渐演化为
# 稳态分布的过程。本模型与p_evolution1d的区别在于：
# 1. 从一维扩展到二维
# 2. 增加了迭代步数（从10步增加到50步）
# 3. 使用云图而非曲线展示压力分布
# 4. 不再在边界设置大体积Cell（所有Cell体积相同）
#
# 【建模技术要点】
# 1. 二维30x20网格，两个对角位置设置固定压力边界
# 2. 使用model.iterate进行迭代，并记录返回信息（推荐时间步长等）
# 3. 使用tfc.get_x/get_y/get_p获取网格坐标和压力数据
# 4. 使用云图（contourf）显示压力场的空间分布
# 5. 使用旧版plot/add_axes2/add_items/item API进行可视化
# 6. 与pressure.py不同，此处不设大体积边界Cell，压力会逐渐变化
#
# 【关键参数】
# 网格大小: 30x20，单元格边长1m
# 固定压力: 左上角(0,0)=2MPa，右下角(29,19)=1MPa
# 初始内部压力: 1.5MPa
# 渗透率: 1.0e-15 m^2
# 时间步长: 1e6 s
# 迭代步数: 50步

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p):
    """
    设置一个Cell的属性

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m）
        y: 单元的位置，y坐标（单位：m）
        v: 单元的体积，m3（设为极大值1e6可实现定压边界）
        p: 单元的压力，Pa
    """
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


def add_face(model: Seepage, i0, i1, area, dist, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        i0: 第一个单元的索引
        i1: 第二个单元的索引
        area: 流动的横截面积，m2
        dist: 单元之间的距离，m
        perm: 渗透率，单位：m2
    """
    face = model.add_face(i0, i1)
    face.cond = area * perm / dist


def test():
    """
    主测试函数：创建二维压力演化模型并求解。

    在30x20的二维区域中，对角设置高压和低压边界，模拟50步
    迭代过程中压力场从初始状态到稳态的逐步演化。
    每步绘制压力云图，展示压力传播的过程。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 30, 20

    # 添加所有Cell，初始压力均为1.5MPa，体积1m^3
    for ix in range(jx):
        for iy in range(jy):
            add_cell(model, x=ix, y=iy, v=1, p=1.5e6)

    # 设置对角位置的固定压力边界（通过将体积极大化实现）
    # 左上角(0,0)固定为2MPa（高压注入端）
    set_cell(model.get_cell(0), x=0, y=0, v=1e6, p=2e6)
    # 右下角(jx-1, jy-1)固定为1MPa（低压采出端）
    set_cell(model.get_cell(-1), x=jx - 1, y=jy - 1, v=1e6, p=1e6)

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for ix in range(jx):
        for iy in range(jy):
            idx = iy + ix * jy  # 一维索引（按列主序存储）
            if ix < jx - 1:
                # 添加x方向的Face
                add_face(model, idx, idx + jy, area=1, dist=1, perm=1.0e-15)
            if iy < jy - 1:
                # 添加y方向的Face
                add_face(model, idx, idx + 1, area=1, dist=1, perm=1.0e-15)

    # 迭代并且绘图显示
    step_max = 50  # 总迭代步数
    for step in range(step_max):
        # 执行一步渗流迭代，时间步长1e6秒，并返回迭代信息
        r = model.iterate(dt=1.0e6)
        print(f'step = {step}/{step_max}, r = {r}')

        # 获取网格坐标和压力数据（按二维形状重塑）
        x = tfc.get_x(model, shape=[jx, jy])
        y = tfc.get_y(model, shape=[jx, jy])
        p = tfc.get_p(model, shape=[jx, jy]) / 1e6

        # 绘制压力云图
        plot(add_axes2, add_items,
             item('contourf', x, y, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
             xlabel="x/m", ylabel="y/m", title=f'Pressure, step = {step}',
             aspect='equal', tight_layout=True,
             caption='压力场')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)

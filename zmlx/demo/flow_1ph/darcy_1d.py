# ** desc = '两端固定压力，计算压力的分布（结果显示为一条直线）'

from zmlx import *


def add_cell(model: Seepage, x, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    c = model.add_cell()
    c.pos = [x, 0, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


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


def show_pressure(model: Seepage):
    """
    显示模型中所有Cell的压力分布
    Args:
        model: 渗流模型，Seepage类的对象
    """
    x = as_numpy(model).cells.x
    p = as_numpy(model).cells.pre / 1e6
    fig.show(
        fig.axes2(
            fig.curve(
                x, p
            ),
            xlabel="x/m", ylabel="p/MPa", title='Pressure Distribution'
        ),
        caption='压力分布'
    )


def main():
    """
    运行测试：创建模型、运行、绘制结果
    """
    model = Seepage()

    # 添加一列Cell。其中第一个和最后一个Cell的体积设置为无穷大 (1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    add_cell(model, x=0, v=1e6, p=2e6)
    for x in linspace(1, 19, 19):
        add_cell(model, x=x, v=1, p=1e6)
    add_cell(model, x=20, v=1e6, p=1e6)

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for i in range(1, model.cell_number):
        add_face(model, i - 1, i, area=1, perm=1.0e-15)

    # 迭代到给定时间之后的状态
    dt = 1e8
    model.iterate(dt=dt)

    # 绘图：绘制压力分布
    show_pressure(model)

    # 实际输运的流体的体积
    v0 = model.get_cell(0).fluid_vol
    model.iterate(dt=dt)
    v1 = model.get_cell(0).fluid_vol
    dv = abs(v1 - v0)
    print(f'输运的流体的体积为：{dv:.2f} m3')

    # 按照达西定律计算，理论上理论上输运的流体的体积为：
    # dv = area * perm * dp * dt / (dist * vis)
    dv_theory = 1.0 * 1.0e-15 * 1e6 * dt / (20.0 * 1.0e-3)
    print(f'根据达西定律计算，理论上输运的流体的体积为：{dv_theory:.2f} m3')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

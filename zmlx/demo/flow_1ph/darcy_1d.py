# ** desc = '两端固定压力，计算压力的分布（结果显示为一条直线）'
#
# 【物理问题描述】
# 本模型模拟一维达西渗流问题。在长度为20m的一维多孔介质柱体中，左端（x=0）固定压力2MPa，
# 右端（x=20）固定压力1MPa，流体在压差驱动下从左向右渗流。模型展示了稳态时压力沿程
# 呈线性分布的特征，并验证数值解与达西定律理论解的一致性。
#
# 【建模技术要点】
# 1. 使用Seepage底层API手动构建一维模型（不依赖tfc.create高级接口）
# 2. 通过设置极大体积（1e6 m^3）的单元格来实现定压边界条件
# 3. 手动添加Face并计算传导系数（cond = area * perm / dist）
# 4. 使用model.iterate()进行时间步进求解
# 5. 将数值计算的流量与达西定律理论值进行对比验证
#
# 【关键参数】
# 模型长度: 20m（21个网格，每个网格间距1m）
# 渗透率: 1.0e-15 m^2
# 流体粘度: 1.0e-3 Pa.s（水）
# 边界压力: 左侧2MPa，右侧1MPa
# 横截面积: 1 m^2
# 时间步长: 1e8 s
#
# 【达西定律验证】
# 达西定律：Q = k*A*dp*dt / (mu*L)
# 理论流量: 1e-15 * 1 * 1e6 * 1e8 / (1e-3 * 20) = 5000 m^3

from zmlx import *


def add_cell(model: Seepage, x, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标（单位：m）
        v: 单元的体积，m3（设为极大值1e6可实现定压边界）
        p: 单元的压力，Pa
    """
    c = model.add_cell()
    c.pos = [x, 0, 0]
    # 设置孔隙属性：参考压力1MPa，参考体积v，压力变化范围1MPa，对应体积变化0.1*v
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    # 根据压力计算流体体积（使用孔隙压缩性关系）
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


def add_face(model: Seepage, i0, i1, area, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)

    根据两个单元之间的距离、流动横截面积和渗透率计算传导系数。
    传导系数公式：cond = area * perm / dist

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

    将压力数据转换为MPa单位并绘制压力沿程分布曲线。

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
    主函数：创建一维达西渗流模型并验证达西定律。

    构建一维21个网格的模型，两端定压（2MPa和1MPa），计算稳态压力分布，
    并通过两个时间步的流量差与达西定律理论值进行对比验证。
    """
    model = Seepage()

    # 添加一列Cell。其中第一个和最后一个Cell的体积设置为无穷大 (1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    add_cell(model, x=0, v=1e6, p=2e6)  # 左端边界：体积1e6 m^3，压力2MPa
    for x in linspace(1, 19, 19):  # 内部单元格：体积1 m^3，初始压力1MPa
        add_cell(model, x=x, v=1, p=1e6)
    add_cell(model, x=20, v=1e6, p=1e6)  # 右端边界：体积1e6 m^3，压力1MPa

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for i in range(1, model.cell_number):
        add_face(model, i - 1, i, area=1, perm=1.0e-15)

    # 迭代到给定时间之后的状态（一次迭代达到稳态）
    dt = 1e8
    model.iterate(dt=dt)

    # 绘图：绘制压力分布
    show_pressure(model)

    # 实际输运的流体的体积（通过对比两个时间步左端边界的流体体积变化计算流量）
    v0 = model.get_cell(0).fluid_vol
    model.iterate(dt=dt)
    v1 = model.get_cell(0).fluid_vol
    dv = abs(v1 - v0)
    print(f'输运的流体的体积为：{dv:.2f} m3')

    # 按照达西定律计算，理论上输运的流体的体积为：
    # dv = area * perm * dp * dt / (dist * vis)
    dv_theory = 1.0 * 1.0e-15 * 1e6 * dt / (20.0 * 1.0e-3)
    print(f'根据达西定律计算，理论上输运的流体的体积为：{dv_theory:.2f} m3')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

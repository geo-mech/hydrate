# ** desc = '两端固定压力，计算不同时刻地压力的分布（计算结果为多条曲线）'
#
# 【物理问题描述】
# 本模型模拟一维达西渗流中压力随时间演化的过程。在长度为20m的一维柱体中，
# 左端固定压力2MPa，右端固定压力1MPa，初始时刻内部压力均为1MPa。
# 随着时间推移，压力从左向右逐渐传播，最终达到稳态线性分布。在10个不同时刻
# 记录压力分布，形成一组由初始到稳态的演化曲线族。
#
# 【建模技术要点】
# 1. 一维21个单元格：左端和右端为大体积边界Cell，中间19个为内部Cell
# 2. 使用model.iterate(dt=1e6)逐时间步推进
# 3. 使用tfc.get_p(model)获取所有单元格的压力值
# 4. 使用旧版plot/add_axes2/add_items/item API，在同一坐标轴上绘制10条不同
#    时刻的压力分布曲线，清晰展示压力场从不稳态到稳态的演化过程
# 5. 使用item('legend')添加图例
#
# 【关键参数】
# 模型长度: 20m（21个网格，间距1m）
# 边界压力: 左端2MPa，右端1MPa
# 渗透率: 1.0e-15 m^2
# 时间步长: 1e6 s
# 迭代步数: 10步

from zmlx import *


def add_cell(model: Seepage, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)

    注意：此版本不显式设置位置，位置由后续的Face连接关系隐含确定。

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        v: 单元的体积，m3（设为极大值1e6可实现定压边界）
        p: 单元的压力，Pa
    """
    c = model.add_cell()
    # 设置孔隙属性：参考压力1MPa，参考体积v，压力变化范围1MPa对应体积变化0.1*v
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    # 根据当前压力计算流体体积
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


def add_face(model: Seepage, i0, i1, area, dist, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)

    显式传入dist参数计算传导系数。

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


def main():
    """
    主函数：创建一维压力演化模型并求解。

    构建一维21个网格的模型，两端定压（2MPa和1MPa），每步迭代1e6秒，
    记录10个不同时刻的压力分布，绘制从初始到稳态的演化曲线族。
    """
    model = Seepage()

    # 添加一列Cell。其中第一个和最后一个Cell的体积设置为无穷大 (1e6)，从而确保它的压力
    # 在流体流动的过程中，不会发生显著的变化.
    vx = linspace(0, 20, 21)  # 位置数组，0~20m共21个点
    for i in range(len(vx)):
        if i == 0:
            add_cell(model, v=1e6, p=2e6)  # 左端边界：体积极大，压力2MPa
        elif i + 1 == len(vx):
            add_cell(model, v=1e6, p=1e6)  # 右端边界：体积极大，压力1MPa
        else:
            add_cell(model, v=1, p=1e6)  # 内部单元格：体积1，初始压力1MPa

    # 在Cell之间添加Face，连接相邻单元
    for idx in range(1, model.cell_number):
        add_face(model, idx - 1, idx, area=1, dist=1, perm=1.0e-15)

    items = []
    # 迭代10步，每步记录压力分布曲线
    for step in range(10):
        # 在当前时刻添加压力分布曲线（压力单位转换为MPa）
        items.append(item('xy', vx, tfc.get_p(model) / 1e6, label=f'step={step}'))
        # 执行一步渗流迭代（时间步长1e6秒）
        model.iterate(dt=1e6)

    # 在同一坐标图中绘制所有时刻的压力分布曲线
    plot(add_axes2, add_items, *items, item('legend'),
         xlabel="x/m", ylabel="p/MPa", title='Pressure',
         caption='压力分布', tight_layout=True)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

# ** desc = '基于Seepage类的温度场计算（非均匀导热系数）'
"""
二维非均匀导热系数下的热传导模拟。

物理问题：
    在一个100m x 100m的二维方形区域内，岩体初始温度为400K。
    利用load_igg()生成一个随机场函数，定义非均匀导热系数：
        - 场函数值 > 0.5 的区域，导热系数为 1 W/(m.K)（高热导区）
        - 场函数值 <= 0.5 的区域，导热系数为 0.0001 W/(m.K)（近绝热区）
    在 (0,-45) 和 (0,45) 位置设置两口热源井，温度为500K。

计算分为两个阶段：
    阶段1（持续100年）：热源井持续加热，观察热量在非均匀介质中的传播路径。
    阶段2（持续20年）：移除热源井（恢复mc属性），观察热量自发扩散。

关键技术：
    - 使用 tfc.create() 创建热传导模型
    - 通过备份和恢复 mc（热容）属性来实现热源井的"开关"
    - 高分辨率100x100网格以清晰显示非均匀导热的影响
"""

from zmlx import *


def create(jx, jy):
    """
    创建非均匀导热系数的热传导模型。

    参数：
        jx: x方向网格数
        jy: y方向网格数

    返回：
        Seepage对象：初始化后的热传导模型，初始温度400K，
                     导热系数由随机场定义（非均匀），
                     时间步长上限为7天。
    """
    # 利用load_igg生成一个随机场，用于定义非均匀导热系数
    f = load_igg(xmin=-50, xmax=50, ymin=-50, ymax=50)

    def heat_cond(x, y, z):
        """
        根据空间位置返回导热系数值。
        随机场值 > 0.5 的区域为高导热区（1 W/(m.K)），
        否则为近绝热区（0.0001 W/(m.K)）。
        """
        if f(x, y) > 0.5:
            return 1  # 高导热区
        else:
            return 0.0001  # 近绝热区

    # 创建热传导模型：100m x 100m 区域，z方向仅1层网格
    model = tfc.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),  # x方向网格节点
            np.linspace(-50, 50, jy + 1),  # y方向网格节点
            (-0.5, 0.5)),                  # z方向薄层
        temperature=400.0,   # 初始温度 [K]
        denc=1.0e6,          # 体积热容 [J/(m^3.K)] = rho * c
        heat_cond=heat_cond, # 非均匀导热系数函数
        dt_max=3600 * 24 * 7, # 最大时间步长：7天
    )
    return model


def backup_mc(model: Seepage):
    """
    备份模型中所有单元格的mc（热容）属性到backup字段。

    用于在设置热源井之前保存原始热容状态，
    以便在移除热源时恢复。

    参数：
        model: Seepage对象
    """
    ca_mc = model.get_cell_key('mc')
    ca_backup = model.reg_cell_key('backup')
    cells = as_numpy(model).cells
    cells.set(ca_backup, cells.get(ca_mc))


def restore_mc(model: Seepage):
    """
    从backup字段恢复备份的mc（热容）属性。

    用于移除热源井，使单元格恢复到原始热容值。

    参数：
        model: Seepage对象
    """
    ca_mc = model.get_cell_key('mc')
    ca_backup = model.get_cell_key('backup')
    cells = as_numpy(model).cells
    cells.set(ca_mc, cells.get(ca_backup))


def set_well(model, temp, poses):
    """
    在指定位置设置恒温热源井。

    将井所在单元格温度固定为指定值（通过将mc设为极大值实现）。

    参数：
        model: Seepage对象
        temp:  井的温度 [K]
        poses: 井的位置列表，每个元素为 (x, y) 坐标 [m]
    """
    ca_t = model.get_cell_key('temperature')
    ca_mc = model.get_cell_key('mc')
    for x, y in poses:
        # 查找距离井位最近的单元格
        cell = model.get_nearest_cell(pos=[x, y, 0])
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, temp)  # 设置目标温度
        cell.set_attr(ca_mc, 1e10) # 设置极大热容，使温度几乎不变


def show(model: Seepage, jx, jy, caption=None):
    """
    绘制温度场的云图。

    参数：
        model:   Seepage对象
        jx, jy:  x和y方向的网格数
        caption: 图片标题（可选）
    """
    # 获取网格坐标（重构为二维数组）
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jy, jx))
    # 获取温度并减去300K基准值以增强对比
    t = tfc.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300
    # 绘制填充等高线图
    items = [item('contourf', x, y, t, cmap='coolwarm', cbar={'label': 'temperature (K)', 'shrink': 0.7})]
    plot(add_axes2, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {tfc.get_time(model, as_str=True)}',
         tight_layout=True,
         caption=caption, aspect='equal')


def main():
    """
    主函数：执行两阶段热传导模拟。

    阶段1：在(0,-45)和(0,45)设置500K热源，模拟100年加热过程。
    阶段2：移除热源，模拟20年温度自然扩散过程。
    """
    jx, jy = 100, 100  # 使用100x100的高分辨率网格
    model = create(jx, jy)
    backup_mc(model)  # 备份原始mc属性，供后续恢复使用

    # 阶段1：在两点设置热源井，持续加热100年
    set_well(model, 500, poses=[(0, -45), (0, 45)])
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段1'), time_forward=3600 * 24 * 365 * 100)

    # 阶段2：恢复原始热容（移除热源），让热量自由扩散20年
    restore_mc(model)  # 恢复mc属性，移除热源
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段2'), time_forward=3600 * 24 * 365 * 20)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

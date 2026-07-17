# ** desc = '基于Seepage类的温度场计算（各向异性导热系数）'
"""
二维各向异性导热系数下的热传导模拟。

物理问题：
    在一个100m x 100m的二维方形区域内，岩体初始温度为400K。
    导热系数使用Tensor3定义各向异性：
        - xx = 3 W/(m.K)（x方向导热最强）
        - yy = 0.1 W/(m.K)（y方向导热最弱）
        - zz = 1 W/(m.K)（z方向中等）
    在中心 (0,0) 位置设置一个500K的冷却井（实际表现为热源），
    模拟10年内的温度扩散过程。

关键技术：
    - 使用 Tensor3 对象定义各向异性导热系数
    - 展示了各向异性介质中热流沿不同方向传播速度的差异
    - 50x50 网格计算
"""

from zmlx import *


def create(jx, jy):
    """
    创建各向异性导热系数的热传导模型。

    参数：
        jx: x方向网格数
        jy: y方向网格数

    返回：
        Seepage对象：初始化后的热传导模型，使用Tensor3定义
                     各向异性导热系数（xx=3, yy=0.1, zz=1），
                     最大时间步长7天。
    """
    model = tfc.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),  # x方向：-50m 到 50m
            np.linspace(-50, 50, jy + 1),  # y方向：-50m 到 50m
            (-0.5, 0.5)),                  # z方向：单层薄片
        temperature=400.0,   # 初始温度 [K]
        denc=1.0e6,          # 体积热容 [J/(m^3.K)]
        heat_cond=Tensor3(xx=3, yy=0.1, zz=1),  # 各向异性导热系数
        dt_max=3600 * 24 * 7, # 最大时间步长：7天
    )
    return model


def backup_mc(model: Seepage):
    """
    备份模型中所有单元格的mc（热容）属性到backup字段。

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

    参数：
        model: Seepage对象
    """
    ca_mc = model.get_cell_key('mc')
    ca_backup = model.get_cell_key('backup')
    cells = as_numpy(model).cells
    cells.set(ca_mc, cells.get(ca_backup))


def set_well(model, temp, poses):
    """
    在指定位置设置恒温热源/冷源井。

    通过将井所在单元格的mc设为极大值，使其温度几乎保持不变。

    参数：
        model: Seepage对象
        temp:  井的目标温度 [K]
        poses: 井的位置列表，每个元素为 (x, y) 坐标 [m]
    """
    ca_t = model.get_cell_key('temperature')
    ca_mc = model.get_cell_key('mc')
    for x, y in poses:
        # 查找距离井位最近的单元格
        cell = model.get_nearest_cell(pos=[x, y, 0])
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, temp)  # 设置井温度
        cell.set_attr(ca_mc, 1e10) # 设置极大热容，使温度几乎不变


def show(model: Seepage, jx, jy, caption=None):
    """
    绘制温度场的填充等高线云图。

    参数：
        model:   Seepage对象
        jx, jy:  x和y方向的网格数
        caption: 图片标题（可选）
    """
    # 获取网格坐标，重构为二维数组
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jy, jx))
    # 获取温度值，减去300K以增强可视化对比
    t = tfc.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300
    # 绘制填充等高线图，使用冷暖色表示温度高低
    items = [item('contourf', x, y, t, cmap='coolwarm', cbar={'label': 'temperature (K)', 'shrink': 0.7})]
    plot(add_axes2, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {tfc.get_time(model, as_str=True)}',
         tight_layout=True,
         caption=caption, aspect='equal')


def main():
    """
    主函数：执行各向异性导热系数的热传导模拟。

    在区域中心 (0,0) 设置500K热源，模拟10年的加热过程。
    由于导热系数各向异性（xx=3 > zz=1 > yy=0.1），
    热量在x方向传播最快，z方向次之，y方向最慢。
    """
    jx, jy = 50, 50  # 网格数
    model = create(jx, jy)
    backup_mc(model)  # 备份原始mc属性

    # 在区域中心设置一个500K的热源
    set_well(model, 500, poses=[(0, 0)])
    # 模拟10年的加热过程
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段1'), time_forward=3600 * 24 * 365 * 10)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

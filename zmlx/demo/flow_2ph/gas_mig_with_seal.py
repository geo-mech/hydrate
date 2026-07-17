# ** desc = '浮力作用下气体运移成藏过程模拟(加入隔挡层)'
#
# 物理问题描述：
#   本模型模拟在含隔挡层（盖层）的情况下，天然气在浮力作用下运移和聚集的过程。
#   模型为二维垂直剖面，与 gas_mig.py 类似，但在-250m~-200m深度处
#   增加了一个低渗透隔挡层（区域为 x:0~200m, z:-250~-200m）。
#   该隔挡层具有高毛管压力（最大5MPa），可有效阻止CH4向上运移，
#   模拟天然气在遇到封盖层后发生侧向运移和聚集的成藏过程。
#
# 建模技术要点：
#   1. 与 gas_mig.py 相同的温压场、气源区和网格设置
#   2. 通过 get_region_id 识别隔挡层区域（ID=1）和普通区域（ID=0）
#   3. 使用 capillary.add_setting 设置不同区域的毛管压力：
#      - 普通区域：毛管压力为0（无毛管力效应）
#      - 隔挡层区域：毛管压力最大5MPa（高排驱压力，封堵效果好）
#   4. 在图上用红色矩形标注隔挡层位置

from zmlx import *


def create(jx, jz):
    """
    创建含隔挡层的天然气运移成藏模型。

    Args:
        jx: 水平方向（x）的网格单元数量
        jz: 垂直方向（z）的网格单元数量

    Returns:
        model: 渗流模型对象
    """
    # 生成二维垂直剖面网格：水平0~300m，垂直-500m~0m
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    def get_region_id(x, y, z):
        """
        定义不同区域的毛管压力曲线ID（从0开始编号）。
        隔挡层区域（x:0~200m, z:-250~-200m）返回ID=1，
        其余区域返回ID=0。
        """
        return 1 if 0 <= x <= 200 and -250 <= z <= -200 else 0

    def get_t(x, y, z):
        """定义地温梯度函数：地表约300K，地温梯度0.0443 K/m。"""
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        """定义初始压力场：顶部约15MPa，静水压力梯度1e4 Pa/m。"""
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        """判断气源区：底部中心（150, 0, -500），半径50m。"""
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def get_s(x, y, z):
        """定义初始饱和度：气源区为纯CH4，其他区域为纯H2O。"""
        if is_gas_region(x, y, z):
            return {'ch4': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        """
        定义存储系数。上下边界设为极大值（1e20）模拟封闭边界，
        内部区域设为正常值1e6。
        """
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_k(x, y, z):
        """均匀渗透率：1e-14 m2。"""
        return 1.0e-14

    def get_porosity(x, y, z):
        """气源区孔隙度为1.0（充足气源），其余为0.1。"""
        if is_gas_region(x, y, z):
            return 1.0  # 使得有更多的气体
        else:
            return 0.1

    # 创建渗流模型
    model = tfc.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24 * 30.0, gravity=(0, 0, -10)
    )

    # 设置毛管压力：
    #   区域ID=0（普通砂岩）：毛管压力为0（不产生毛管效应）
    #   区域ID=1（隔挡层）：毛管压力从0到5MPa（高排驱压力，阻止气体通过）
    capillary.add_setting(
        model, fid0='ch4', fid1='h2o', get_idx=get_region_id,
        data=[[[0, 1], [0, 1]],           # 普通区域：毛管压力≈0
              [[0, 1], [0, 5e6]]          # 隔挡层：毛管压力最大5MPa
              ]
    )

    # 设置求解参数：模拟总时长6年
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, }
    )

    return model


def show(model, jx, jz):
    """
    在界面上显示模型状态，用红色矩形标注隔挡层位置。

    Args:
        model: 渗流模型对象
        jx: 水平方向网格单元数量
        jz: 垂直方向网格单元数量
    """
    def on_figure(figure):
        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        p = tfc.get_p(model, shape=(jx, jz))
        v0 = tfc.get_v(model, fid=0, shape=(jx, jz))
        v1 = tfc.get_v(model, fid=1, shape=(jx, jz))
        v = v0 + v1

        def add_rect(ax):
            """在图上绘制隔挡层边界矩形和气源区半圆。"""
            ax.plot([0, 200, 200, 0], [-250, -250, -200, -200], color='r', linewidth=1)
            angles = np.linspace(0, np.pi, 100)
            ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

        layout = AutoLayout(figure, 3, subplot_aspect_ratio=0.6, aspect='equal', xlabel='x/m', ylabel='z/m')
        ax = layout.add_axes2(add_contourf, x, z,
                              p, cbar=dict(label='p', shrink=0.6), title='pressure', cmap='coolwarm')
        add_rect(ax)

        ax = layout.add_axes2(add_contourf, x, z,
                              v0 / v, cbar=dict(label='s0', shrink=0.6), title='ch4 saturation')
        add_rect(ax)

        ax = layout.add_axes2(add_contourf, x, z,
                              v1 / v, cbar=dict(label='s1', shrink=0.6), title='h2o saturation')
        add_rect(ax)

    plot(on_figure, caption=f'Seepage({model.handle_str})', suptitle=f'时间: {tfc.get_time(model, as_str=True)}',
         tight_layout=True)


def main():
    """
    主函数：创建60x100网格的含隔挡层运移模型，求解6年运移成藏过程。
    """
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jz))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

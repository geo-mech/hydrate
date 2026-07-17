# ** desc = '重力驱动下的对流'
#
# 本案例模拟重力驱动下的CO2对流现象。在垂直二维剖面中，上下两侧分别设置低密度和高密度
# 区（通过CO2浓度差异实现密度差），在重力作用下形成对流。模型采用热-流-化学（TFC）耦合
# 框架，仅启用流体流动模块（通过标签禁用热传导更新）。主要演示tfc模块的求解器功能，
# 以及利用matplotlib进行实时可视化，包括密度场、流体组分和CO2浓度分布图的绘制。

from zmlx import *


def create(jx, jz):
    """
    创建重力驱动对流的渗流模型

    在垂直剖面（x方向宽2m，z方向高4m）中，设置三个初始区域：
      底部圆形区域（中心(0,-1.5)，半径0.3）：纯水（h2o=1.0，无CO2）
      顶部圆形区域（中心(0,1.5)，半径0.3）：高CO2浓度（h2o=0.9，co2=0.1）
      背景区域：中等CO2浓度（h2o=0.95，co2=0.05）
    由于密度差和重力（-10 m/s^2沿z方向）驱动，形成对流运动。

    Args:
        jx: x方向的网格单元数
        jz: z方向的网格单元数

    Returns:
        model: Seepage对象，配置好的渗流模型
    """
    # 创建二维矩形网格：x范围[-1,1]，y厚度0.5m，z范围[-2,2]
    mesh = create_cube(
        x=linspace(-1, 1, jx + 1), y=[-0.5, 0.5], z=linspace(-2, 2, jz + 1)
    )
    # 定义流体：水溶液，含CO2组分，浓度范围[0.1, 1.1]（质量分数）
    fludefs = [create_aqueous(co2=[0.1, 1.1])]

    def get_s(x, y, z):
        """
        根据空间坐标返回初始饱和度/组分分布
        Args:
            x, y, z: 空间坐标
        Returns:
            dict: 包含h2o和co2的质量分数
        """
        # 底部圆形区域：纯水（高密度区）
        if point_distance((x, z), (0, -1.5)) < 0.3:
            return dict(h2o=1.0, co2=0)
        # 顶部圆形区域：高CO2浓度（低密度区，驱动对流）
        elif point_distance((x, z), (0, 1.5)) < 0.3:
            return dict(h2o=0.9, co2=0.1)
        # 背景区域：中等CO2浓度
        else:
            return dict(h2o=0.95, co2=0.05)

    # 创建TFC耦合模型
    model = tfc.create(
        mesh=mesh,
        cfl=0.5,          # CFL数，控制时间步长稳定性
        fludefs=fludefs,
        s=get_s,          # 初始流体组分分布函数
        use_mass=True,    # 使用质量守恒形式
        porosity=0.2,     # 孔隙度
        p=2e6,            # 初始压力（Pa）
        perm=10e-15,      # 渗透率（m^2）
        gravity=[0, 0, -10]  # 重力加速度，沿z负方向
    )
    # 记录每个单元的z坐标作为辅助场量（可用于分析流体运移路径）
    if np is not None:
        tfc.set_fa(model, 0, 'z0', tfc.get_z(model))
    # 禁用粘度和温度更新（本案例仅关注密度驱动对流，无需考虑温度效应）
    model.add_tag('disable_update_vis', 'disable_ther')
    return model


def show(model: Seepage, caption=None):
    """
    使用matplotlib可视化当前模型状态，绘制密度场、流体组分和CO2浓度分布

    Args:
        model: Seepage渗流模型对象
        caption: 窗口标题，默认为模型句柄字符串
    """
    if not gui.exists():
        return

    assert np is not None, 'numpy is not imported'

    # 绘制两个圆形指示标记：标记初始高低浓度区域的边界
    angles = linspace(0, np.pi * 2, 100)
    c1 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 + 1.5, 'k--')
    c2 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 - 1.5, 'r--')

    def f(figure):
        """绘图回调函数，在figure上绘制三个子图"""
        assert np is not None, 'numpy is not imported'
        figure.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}')
        x = tfc.get_x(model)   # 获取所有单元x坐标
        y = tfc.get_z(model)   # 获取所有单元z坐标（二维剖面）
        x0, x1, y0, y1 = float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))
        # 创建自动布局，3个子图，保持纵横比与实际区域一致
        layout = AutoFigLayout(figure, 3, (x1 - x0) / (y1 - y0), xlabel='x / m', ylabel='z / m',
                               aspect='equal')
        # 子图1：流体密度分布
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_den(model, 0), cbar=dict(label='密度'),
                              title='密度')
        fig.add_to_axes(ax, c1, c2)  # 叠加初始区域标记
        # 子图2：流体组分辅助场量z0（反映运移路径）
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_fa(model, 0, 'z0'), cbar=dict(label='流体z0'),
                              title='流体Z0')
        fig.add_to_axes(ax, c1, c2)
        # 子图3：CO2浓度分布
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_c(model, 'co2', 'liq'),
                              cbar=dict(label='co2浓度'),
                              title='co2浓度')
        fig.add_to_axes(ax, c1, c2)

    if caption is None:
        caption = f"Seepage({model.handle_str})"
    plot_on_figure(f, caption=caption, clear=True, tight_layout=True)


def main():
    """
    主函数：创建模型，显示初始状态，然后求解（模拟约2000天），
    并在求解过程中实时更新图形显示。
    """
    jx, jz = 50, 100   # 网格分辨率：50x100
    model = create(jx, jz)
    show(model, caption='初始状态')                     # 显示初始状态
    tfc.solve(model, time_max=3600 * 24 * 2000,         # 最大模拟时间：2000天
              extra_plot=lambda: show(model, caption='最新状态'))  # 每步后更新显示


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

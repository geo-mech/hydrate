# ** desc = '密度差驱动下的对流+扩散的综合效应 (2)'
#
# 本案例与test_2.py类似，但采用了不同的几何布局和扩散参数。在垂直二维剖面
# （x方向宽2m，z方向高4m）中设置左上和右下两个初始浓度异常区。相比于test_2.py，
# 扩散系数增大为1.0e-7 m^2/s（增大两个数量级），从而使扩散效应更加显著。
# 同时，本案例中重力方向沿z轴（垂直向下），更贴近实际地质模型中重力驱动
# 对流的物理情景。模型同样禁用粘度和温度更新，聚焦于对流-扩散耦合过程。

from zmlx import *


def create(jx, jz):
    """
    创建渗流模型，包含对流和扩散两种传质机制

    在垂直二维剖面中设置两个圆形异常区：
      左下区域（中心(-0.5,-1.5)）：纯水（无CO2，高密度）
      右上区域（中心(0.5,1.5)）：高CO2浓度（h2o=0.9，低密度）
    由于密度差和重力作用驱动对流，同时CO2扩散（D=1.0e-7 m^2/s）促使
    浓度均匀化。该扩散系数比test_2.py大两个数量级，扩散效应更显著。

    Args:
        jx: x方向网格数
        jz: z方向网格数

    Returns:
        model: Seepage对象，包含对流和扩散设置
    """
    # 创建二维垂直剖面网格
    mesh = create_cube(
        x=linspace(-1, 1, jx + 1), y=[-0.5, 0.5], z=linspace(-2, 2, jz + 1)
    )
    # 定义水溶液，含CO2组分
    fludefs = [create_aqueous(co2=[0.1, 1.1])]

    def get_s(x, y, z):
        """
        设置初始CO2浓度分布
        Args:
            x, y, z: 空间坐标
        Returns:
            dict: 组分质量分数
        """
        # 左下区域：纯水（高密度）
        if point_distance((x, z), (-0.5, -1.5)) < 0.3:
            return dict(h2o=1.0, co2=0)
        # 右上区域：高CO2（低密度，驱动对流上升）
        elif point_distance((x, z), (0.5, 1.5)) < 0.3:
            return dict(h2o=0.9, co2=0.1)
        # 背景区域：中等CO2
        else:
            return dict(h2o=0.95, co2=0.05)

    # 创建TFC模型
    model = tfc.create(
        mesh=mesh,
        cfl=0.5,
        fludefs=fludefs,
        s=get_s,
        use_mass=True,
        porosity=0.2,
        p=2e6,
        perm=10e-15,
        gravity=[0, 0, -10]    # 重力垂直向下（z负方向）
    )
    # 添加CO2扩散设置：扩散系数1.0e-7 m^2/s（比test_2大100倍）
    diffusion.add_setting(model, 'co2', 'liq', d=1.0e-7, cfl=0.2)

    # 记录每个单元的z坐标作为辅助场量（用于分析运移路径）
    if np is not None:
        tfc.set_fa(model, 0, 'z0', tfc.get_z(model))
    # 禁用粘度和温度更新（仅关注对流-扩散过程）
    model.add_tag('disable_update_vis', 'disable_ther')
    return model


def show(model: Seepage, caption=None):
    """
    可视化模型状态：密度场、流体组分和CO2浓度分布

    Args:
        model: Seepage对象
        caption: 窗口标题
    """
    if not gui.exists():
        return

    assert np is not None, 'numpy is not imported'

    # 绘制圆形标记，指示初始异常区位置
    angles = linspace(0, np.pi * 2, 100)
    c1 = fig.curve(np.cos(angles) * 0.3 + 0.5, np.sin(angles) * 0.3 + 1.5, 'k--')
    c2 = fig.curve(np.cos(angles) * 0.3 - 0.5, np.sin(angles) * 0.3 - 1.5, 'r--')

    def f(figure):
        """绘图回调函数"""
        assert np is not None, 'numpy is not imported'
        figure.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}')
        x = tfc.get_x(model)
        y = tfc.get_z(model)
        x0, x1, y0, y1 = float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))
        # 创建自动布局，3个子图，保持纵横比
        layout = AutoFigLayout(figure, 3, (x1 - x0) / (y1 - y0), xlabel='x / m', ylabel='z / m',
                               aspect='equal')
        # 子图1：密度分布
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_den(model, 0), cbar=dict(label='密度'),
                              title='密度')
        fig.add_to_axes(ax, c1, c2)
        # 子图2：流体组分辅助场量z0
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
    主函数：创建模型（50x100网格），显示初始状态，
    然后求解约2000天，实时更新图形展示对流-扩散过程
    """
    jx, jz = 50, 100
    model = create(jx, jz)
    show(model, caption='初始状态')
    tfc.solve(model, time_max=3600 * 24 * 2000,
              extra_plot=lambda: show(model, caption='最新状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

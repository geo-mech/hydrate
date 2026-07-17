# ** desc = '基于Seepage类的温度场计算'
#
# 本案例与 thermal.py 为同一物理问题（二维热传导），但使用高层辅助函数
# tfc.create() 搭建模型，代码更加简洁。
# 物理问题：在 -50m 到 50m 的方形区域内，初始时刻中心有一个半径 30m 的
# 高温区(380K)，周围为低温区(280K)。高温区的热量随时间向四周传导扩散。
# 参数通过 tfc.create 的命名参数传递：denc=热容密度，heat_cond=热导率，
# dt_max=最大时间步长，并通过 texts 参数传入求解器配置。
# 可视化方法：使用图函数 plot() + on_figure 回调方式展示温度场。
#
from zmlx import *


def create():
    """
    创建热传导模型（使用高层 API）。

    使用 tfc.create() 函数，通过命名参数方式指定网格、初始温度、
    热容密度、热导率和求解器配置，代码比 thermal.py 更简洁。

    Returns:
        Seepage: 构建完成的模型对象
    """
    return tfc.create(
        mesh=create_cube(
            np.linspace(-50, 50, 50),  # x方向50个单元，范围-50~50m
            np.linspace(-50, 50, 50),  # y方向50个单元，范围-50~50m
            (-0.5, 0.5)),              # z方向仅1层（2D问题）
        temperature=lambda *pos: 380 if point_distance(pos, (  # 初始温度：中心半径30m内380K，其余280K
            0, 0, 0)) < 30 else 280,
        denc=1.0e6,                    # 热容密度 (= 密度 * 比热容)，单位 J/(m3*K)
        heat_cond=1.0,                 # 热导率，单位 W/(m*K)
        dt_max=1.0e6,                  # 最大时间步长
        texts={'solve': {'step_max': 500, }}  # 求解器配置：最多迭代500步
    )


def show(model: Seepage):
    """
    显示当前温度场。

    使用 plot() 函数配合 on_figure 回调，在图形中添加三角网格等值线填充图，
    展示当前时刻的温度分布。

    Args:
        model: Seepage 模型对象
    """
    def on_figure(fig):
        add_axes2(fig, add_tricontourf, tfc.get_x(model), tfc.get_y(model),
                  tfc.get_ca(model, model.get_cell_key('temperature')),  # 获取温度属性值
                  title='temperature',
                  xlabel='x (m)', ylabel='y (m)', aspect='equal',
                  cbar={'label': 'temperature (K)'}, cmap='coolwarm',
                  )

    plot(on_figure, clear=True, caption='模型状态')  # 清空并更新图形


def main():
    """
    主函数：创建模型并启动求解。

    创建热传导模型后调用 tfc.solve 进行求解，求解过程中通过 extra_plot
    回调实时显示温度场。
    """
    model = create()                                                      # 创建热传导模型
    tfc.solve(model, extra_plot=lambda: show(model))  # 启动求解，关闭后不退出


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

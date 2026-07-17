# ** desc = '基于Seepage类的温度场计算'
#
# 本案例演示多个点状冷源的热传导问题（thermal3.py 的扩展）。
# 物理问题：在 -50m 到 50m 的方形区域内，初始时刻全部为 400K，
# 在四个位置 (-20,0)、(20,0)、(0,-20)、(0,20) 设置低温点 (300K) 作为热汇。
# 每个低温点具有极大的热容 (1e10)，使其温度在模拟期间几乎保持不变。
# 模拟总时长 20 年。
# 可视化方法：三维曲面图 (surf) + 等值线填充图 (contourf) 叠加显示。
# 目的：对比单冷源与多冷源的温度场演化差异。
#
from zmlx import *


def create(jx, jy):
    """
    创建带四个点状冷源的热传导模型。

    在 50x50 方形区域内设置均匀初始温度 400K，然后在四个位置
    (-20,0)、(20,0)、(0,-20)、(0,20) 设置低温点 300K，
    每个点赋予极大热容 (1e10)，使其温度近似恒定，作为多个热汇同步吸热。

    Args:
        jx: x 方向单元数
        jy: y 方向单元数

    Returns:
        Seepage: 构建完成的模型对象
    """
    model = tfc.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),  # x方向网格
            np.linspace(-50, 50, jy + 1),  # y方向网格
            (-0.5, 0.5)),                  # z方向仅1层
        temperature=400.0,                 # 初始温度均匀400K
        denc=1.0e6,                        # 热容密度
        heat_cond=1.0,                     # 热导率
        dt_max=1.0e6,                      # 最大时间步长
        texts={'solve': {'time_max': 3600 * 24 * 365 * 20, }}  # 模拟总时长20年
    )
    ca_t = model.get_cell_key('temperature')  # 温度属性键
    ca_mc = model.get_cell_key('mc')           # 热容属性键
    for x, y in [(-20, 0), (20, 0), (0, -20), (0, 20)]:  # 四个冷源位置
        cell = model.get_nearest_cell(pos=[x, y, 0])       # 找到距该位置最近的单元格
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, 300)    # 设为低温300K
        cell.set_attr(ca_mc, 1e10)  # 给予极大热容，起到热汇作用
    return model


def show(model: Seepage, jx, jy):
    """
    显示当前温度场（三维曲面 + 等值线叠加）。

    使用三维曲面图 (surf) 叠加等值线填充图 (contourf) 展示温度分布。
    温度值减去 300K 以便更清晰地显示与冷源温度的差值。

    Args:
        model: Seepage 模型对象
        jx: x 方向单元数（用于重塑数据为网格形状）
        jy: y 方向单元数（用于重塑数据为网格形状）
    """
    x = tfc.get_x(model, shape=(jx, jy))        # 获取x坐标，重塑为网格形状
    y = tfc.get_y(model, shape=(jy, jx))        # 获取y坐标，重塑为网格形状
    t = tfc.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300  # 获取温度并减去300K基准
    cmap = 'coolwarm'
    items = [item('surf', x, y, t * 100, t, cbar={'label': 'temperature (K)', 'shrink': 0.7}, cmap=cmap),  # 三维曲面（z方向放大100倍）
             item('contourf', x, y, t, cmap=cmap)  # 底面的等值线填充图
             ]
    plot(add_axes3, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {tfc.get_time(model, as_str=True)}',  # 标题显示当前模拟时间
         tight_layout=True,
         caption='温度场')


def main():
    """
    主函数：创建50x50网格的四个冷源模型并启动求解。

    求解过程中通过 extra_plot 回调实时显示三维温度场，
    观察四个冷源周围温度演化的相互影响。
    """
    jx, jy = 50, 50                             # 网格分辨率 50x50
    model = create(jx, jy)                      # 创建模型
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy))  # 启动求解


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

# ** desc = '基于Seepage类的温度场计算'
#
# 本案例演示多阶段热传导模拟，包含加热、扩散和冷却三个连续阶段。
# 物理问题：在 -50m 到 50m 的方形区域内，初始时刻全部为 400K。
# 阶段1（加热5年）：在四个位置 (-20,0)、(20,0)、(0,-20)、(0,20) 设置高温井 500K，
#   通过极大热容固定井点温度，热量从井点向周围扩散。
# 阶段2（扩散2年）：移除井点（恢复原始热容），让热量自然扩散。
# 阶段3（冷却5年）：在相同四个位置设置低温井 300K，模拟冷却过程。
# 关键技巧：backup_mc() 保存热容数组 -> set_well() 修改热容固定温度 ->
# restore_mc() 恢复原始热容，实现"钉扎/释放"温度功能。
# 时间步长：一周 (3600*24*7 秒)，便于观察短时间尺度变化。
#
from zmlx import *


def create(jx, jy):
    """
    创建基础热传导模型（不设置任何井/边界条件）。

    构建 50x50 方形网格，均匀初始温度 400K，热容密度 1.0e6，
    热导率 1.0，最大时间步长为一周。

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
        dt_max=3600 * 24 * 7,              # 最大时间步长 = 1周（秒）
    )
    return model


def backup_mc(model: Seepage):
    """
    备份所有单元的热容 (mc) 属性到 'backup' 字段。

    在设置井点温度前调用，保存原始热容值以便后续恢复。
    利用 as_numpy 将模型数据转为 NumPy 数组进行批量操作。

    Args:
        model: Seepage 模型对象
    """
    ca_mc = model.get_cell_key('mc')         # 获取热容属性键
    ca_backup = model.reg_cell_key('backup') # 注册/获取备份字段键
    cells = as_numpy(model).cells             # 将单元格数据转为NumPy数组（批量访问）
    cells.set(ca_backup, cells.get(ca_mc))    # 将mc的值复制到backup字段


def restore_mc(model: Seepage):
    """
    从 'backup' 字段恢复所有单元的热容 (mc) 属性。

    在阶段切换时调用，移除井点对热容的修改，恢复原始热容值，
    使已固定的温度点可以自由变化。

    Args:
        model: Seepage 模型对象
    """
    ca_mc = model.get_cell_key('mc')         # 获取热容属性键
    ca_backup = model.get_cell_key('backup') # 获取备份字段键（必须在backup_mc之后调用）
    cells = as_numpy(model).cells             # 将单元格数据转为NumPy数组
    cells.set(ca_mc, cells.get(ca_backup))    # 从备份恢复原始mc值


def set_well(model, temp):
    """
    在四个固定位置设置井（温度钉扎点）。

    通过修改指定单元格的温度和热容来模拟井的作用。
    极大的热容值 (1e10) 使该点温度在模拟期间几乎保持不变，
    从而实现类似"恒温边界条件"的效果。

    Args:
        model: Seepage 模型对象
        temp: 井的目标温度 (K)，高温即注热，低温即冷却
    """
    ca_t = model.get_cell_key('temperature')  # 获取温度属性键
    ca_mc = model.get_cell_key('mc')           # 获取热容属性键
    for x, y in [(-20, 0), (20, 0), (0, -20), (0, 20)]:  # 四个井的位置
        cell = model.get_nearest_cell(pos=[x, y, 0])       # 找到最近的单元格
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, temp)    # 设置井点温度
        cell.set_attr(ca_mc, 1e10)   # 给予极大热容，使温度被"钉扎"在该值


def show(model: Seepage, jx, jy, caption=None):
    """
    显示当前温度场，支持自定义标题。

    使用三维曲面图 (surf) 叠加等值线填充图 (contourf) 展示温度分布。
    caption 参数用于标识当前所处的模拟阶段。

    Args:
        model: Seepage 模型对象
        jx: x 方向单元数
        jy: y 方向单元数
        caption: 图形标题（用于区分不同模拟阶段，如'阶段1'/'阶段2'/'阶段3'）
    """
    x = tfc.get_x(model, shape=(jx, jy))        # 获取x坐标，重塑为网格形状
    y = tfc.get_y(model, shape=(jy, jx))        # 获取y坐标，重塑为网格形状
    t = tfc.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300  # 获取温度并减去300K基准
    cmap = 'coolwarm'
    items = [item('surf', x, y, t * 100, t, cbar={'label': 'temperature (K)', 'shrink': 0.7}, cmap=cmap),  # 三维曲面
             item('contourf', x, y, t, cmap=cmap)  # 等值线填充图
             ]
    plot(add_axes3, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {tfc.get_time(model, as_str=True)}',  # 标题显示模拟时间
         tight_layout=True,
         caption=caption)


def main():
    """
    主函数：执行三阶段热传导模拟。

    阶段1 - 加热阶段（5年）：在四个位置设置 500K 高温井，热量从井点向四周扩散。
    阶段2 - 扩散阶段（2年）：移除井点约束，让已积累的热量自然扩散。
    阶段3 - 冷却阶段（5年）：在同位置设置 300K 低温井，模拟地热采出或降温过程。

    各阶段之间通过 backup_mc / restore_mc 保存和恢复原始热容，
    实现井点温度的"钉扎"与"释放"。
    """
    jx, jy = 50, 50                                                     # 网格分辨率 50x50
    model = create(jx, jy)                                              # 创建基础模型
    backup_mc(model)                                                    # 备份原始热容（后续用于恢复）

    set_well(model, 500)                                                # 设置四个高温井（500K）
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段1'),  # 阶段1：加热5年
              time_forward=3600 * 24 * 365 * 5)

    restore_mc(model)                                                   # 恢复原始热容，释放井点约束
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段2'),  # 阶段2：自然扩散2年
              time_forward=3600 * 24 * 365 * 2)

    set_well(model, 300)                                                # 设置四个低温井（300K）
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段3'),  # 阶段3：冷却5年
              time_forward=3600 * 24 * 365 * 5)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)  # 通过 --no-gui 参数可禁用图形界面

# ** desc = '基于Seepage类的温度场计算'
#
# 本案例演示二维热传导问题，使用低层 Seepage API 直接操作单元格属性和面属性。
# 物理问题：在 -50m 到 50m 的方形区域内，初始时刻中心有一个半径 30m 的
# 高温区(380K)，周围为低温区(280K)。高温区的热量随时间向四周传导扩散。
# 模型参数：热容 mc = 1.0e6 * 单元体积 (J/K)，热导率 g_heat = 面积 / 长度 (W/K)，
# 时间步长 dt = 1.0e6，共迭代 500 步。
# 可视化方法：使用三角网格等值线填充图 (tricontourf) 展示温度分布。
#
from zmlx import *


class CellAttrs:
    """
    定义单元格的属性索引。
    这些类属性作为枚举值，在 set_attr / get_attr 中标识对应的物理字段。
        temperature: 温度字段索引 (0)，单位 K
        mc: 热容字段索引 (1)，即质量乘以比热容，单位 J/K
    """
    temperature = 0  # 温度属性索引
    mc = 1           # 热容属性索引


class FaceAttrs:
    """
    定义面的属性索引。
        g_heat: 热传导系数索引 (0)，表示该面上单位温差下的热流量，单位 W/K
    """
    g_heat = 0  # 热传导系数属性索引


def create():
    """
    创建热传导模型。

    构建 50x50 方形网格 (范围 -50m ~ 50m)，中心半径 30m 区域内设置
    高温 380K，其余区域 280K。每个单元的热容 mc = 1.0e6 * 单元体积，
    每个面的热导率 g_heat = 面积 / 长度。

    Returns:
        Seepage: 构建完成的模型对象
    """
    model = Seepage()
    mesh = create_cube(
        np.linspace(-50, 50, 50),
        np.linspace(-50, 50, 50),
        (-0.5, 0.5))

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        cell.set_attr(CellAttrs.temperature,
                      380 if point_distance(c.pos, (0, 0, 0)) < 30 else 280)  # 距离中心30m内为380K高温，其余为280K低温
        cell.set_attr(CellAttrs.mc, 1.0e6 * c.vol)

    for f in mesh.faces:
        face = model.add_face(
            model.get_cell(f.link[0]),
            model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.0 / f.length)

    return model


def show(model):
    """
    显示当前温度场。

    使用三角网格等值线填充图 (tricontourf) 展示温度分布。
    横轴为 x 方向位置 (m)，纵轴为 y 方向位置 (m)，颜色表示温度值 (K)。

    Args:
        model: Seepage 模型对象
    """
    tricontourf(tfc.get_x(model), tfc.get_y(model),
                tfc.get_ca(model, CellAttrs.temperature),
                caption='temperature',
                xlabel='x (m)', ylabel='y (m)', clabel='temperature (K)')


def solve(model):
    """
    执行热传导迭代求解。

    迭代 500 步，每步时间步长 dt = 1.0e6。每 50 步显示一次当前温度场
    并输出迭代信息。

    Args:
        model: Seepage 模型对象
    """
    for step in range(500):
        gui.break_point()                                               # 允许GUI在每一步中断（用于调试/步进）
        r = model.iterate_thermal(
            dt=1.0e6, ca_t=CellAttrs.temperature,                       # 温度属性索引
            ca_mc=CellAttrs.mc,                                         # 热容属性索引
            fa_g=FaceAttrs.g_heat)                                      # 热传导系数属性索引
        if step % 50 == 0:                                              # 每50步显示并输出状态
            show(model)
            print(f'step = {step}, r = {r}')


if __name__ == '__main__':
    gui.execute(solve, close_after_done=False, args=(create(),))  # 通过命令行参数 --no-gui 可禁用图形界面

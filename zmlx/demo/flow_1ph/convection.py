# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'
#
# 【物理问题描述】
# 本模型模拟单相流体（水）在重力作用下的自然对流过程。在初始状态下，模型区域中存在
# 两个密度异常体：一个低密度区（位于z=-1.5处）和一个高密度区（位于z=1.5处）。
# 在重力（g = -10 m/s^2，沿z方向）的作用下，低密度流体向上运移，高密度流体向下运移，
# 从而形成自然对流。
#
# 【建模技术要点】
# 1. 使用create_cube创建三维矩形网格（x方向-1~1m，z方向-2~2m，y方向厚度0.5m）
# 2. 通过tfc.create直接创建热-流-化耦合模型，设定孔隙度、渗透率、初始压力等
# 3. 在特定位置人工调整流体质量和密度，形成密度异常体
# 4. 通过标签'disable_update_den'、'disable_update_vis'、'disable_ther'禁用
#    密度更新、粘度更新和热力学计算，简化问题为纯流动问题
# 5. 设置流体Z0（z坐标）作为场变量，用于追踪流体的运动轨迹
#
# 【关键参数】
# 孔隙度: 0.2
# 渗透率: 10e-15 m^2 (约10 Darcy)
# 初始压力: 2e6 Pa (约20 atm)
# 饱和度: 1.0 (单相)
# 重力加速度: [0, 0, -10] m/s^2

from zmlx import *


def create(jx, jz):
    """
    创建自然对流模型。

    该函数构建一个矩形区域模型，并在其中设置两个密度异常体（低密度和高密度），
    用于模拟重力驱动下的自然对流过程。

    Args:
        jx: x方向（水平方向）的网格单元数量
        jz: z方向（垂直方向）的网格单元数量

    Returns:
        model: 所创建的Seepage模型对象
    """
    # 创建矩形网格：x方向范围[-1, 1]，y方向厚度[-0.5, 0.5]，z方向范围[-2, 2]
    mesh = create_cube(
        x=linspace(-1, 1, jx + 1), y=[-0.5, 0.5], z=linspace(-2, 2, jz + 1)
    )
    # 使用tfc引擎创建渗流模型，设置孔隙介质和流体属性
    model = tfc.create(
        mesh=mesh, cfl=0.5,  # cfl: 体积变化相对容差
        fludefs=[FluDef(name='h2o')],  # 定义流体为水
        porosity=0.2,  # 孔隙度
        p=2e6, s=1.0,  # 初始压力2MPa，饱和度1.0
        perm=10e-15,  # 渗透率 10e-15 m^2
        gravity=[0, 0, -10]  # z方向重力加速度（负号表示向下）
    )
    for cell in model.cells:  # 在z=-1.5的区域设置低密度；在z=1.5的区域设置高密度
        x, _, z = cell.pos
        flu = cell.get_fluid(0)
        # 在z=-1.5附近(半径0.3)设置低密度区：密度和质量均减半
        if point_distance((x, z), (0, -1.5)) < 0.3:
            flu.mass *= 0.5
            flu.den *= 0.5
        # 在z=1.5附近(半径0.3)设置高密度区：密度和质量均增加1.5倍
        if point_distance((x, z), (0, 1.5)) < 0.3:
            flu.mass *= 1.5
            flu.den *= 1.5
    # 设置流体的z坐标作为追踪场变量，用于观察流体运移轨迹
    tfc.set_fa(model, 0, 'z0', tfc.get_z(model))
    # 禁用密度更新、粘度更新和热力学计算，聚焦于纯流动问题
    model.add_tag('disable_update_den', 'disable_update_vis', 'disable_ther')
    return model


def fig_data(model, jx, jz):
    """
    生成模型当前状态的绘图数据。

    绘制两个子图：（1）密度分布；（2）流体Z0场（追踪流体来源）。
    同时在图上标记初始低密度区（红色虚线圆）和高密度区（黑色虚线圆）的位置。

    Args:
        model: Seepage模型对象
        jx: x方向的网格单元数量
        jz: z方向的网格单元数量

    Returns:
        一个fig布局对象，包含两个子图和总标题
    """
    # 生成圆形标记，用于显示低密度区和高密度区的初始位置
    angles = linspace(0, np.pi * 2, 100)
    c1 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 + 1.5, 'k--')  # 高密度区标记（黑色虚线）
    c2 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 - 1.5, 'r--')  # 低密度区标记（红色虚线）
    shape = [jx, jz]
    xy = [tfc.get_x(model, shape=shape), tfc.get_z(model, shape=shape)]
    # 密度分布云图
    f1 = fig.contourf(*xy, tfc.get_den(model, 0, shape=shape), cbar=dict(label='密度'))
    # 流体Z0场（追踪流体初始z位置的变化）
    f2 = fig.contourf(*xy, tfc.get_fa(model, 0, 'z0', shape=shape), cbar=dict(label='流体z0'))
    opts = dict(xlabel='x / m', ylabel='z / m', aspect='equal')
    return fig.auto_layout(
        fig.axes2(
            f1, c1, c2, title='密度', **opts
        ),
        fig.axes2(
            f2, c1, c2, title='流体Z0', **opts
        ),
        fig.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}'),
        aspect_ratio=0.5,
    )


def main():
    """
    主函数：创建模型、显示初始状态、求解并实时更新显示。

    使用50x100的网格分辨率模拟自然对流过程，总模拟时间500天。
    每步迭代后更新绘图，观察密度异常体在重力作用下的运移过程。
    """
    jx, jz = 50, 100  # x方向50个网格，z方向100个网格（保证各向同性）
    model = create(jx, jz)
    # 显示初始状态
    fig.show(fig_data(model, jx, jz), caption='初始状态', clear=True)
    # 求解并实时显示最新状态（模拟时间500天）
    tfc.solve(model, time_max=3600 * 24 * 500,
              extra_plot=lambda: fig.show(fig_data(model, jx, jz), caption='最新状态', clear=True)
              )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

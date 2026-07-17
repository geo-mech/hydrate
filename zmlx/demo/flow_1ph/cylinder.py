# ** desc = '单相流，两端固定压力，计算压力场 (在计算区域的中间，设置了一个不渗透的区域)'
#
# 【物理问题描述】
# 本模型模拟一个二维矩形多孔介质区域中的单相渗流问题。区域左侧（x=0）固定压力3MPa，
# 右侧（x=100）固定压力1MPa，上下边界无流动。在区域中心（50,25）处有一个半径为15的
# 不渗透圆形区域（渗透率为0），流体只能绕行通过。模型用于研究存在障碍物时的压力场分布。
#
# 【建模技术要点】
# 1. 使用create_cube创建100x50的矩形网格，z方向厚度1m
# 2. 使用tfc.create直接创建模型，通过函数方式定义孔隙度、初始压力、渗透率的空间分布
# 3. 在左右边界设置极大孔隙度（1e10），替代传统的定压边界条件
# 4. 在中心圆形区域设置渗透率为0，形成不渗透障碍
# 5. 流体属性使用h2o模块创建，密度1000kg/m^3，粘度1.0e-3 Pa.s
# 6. 使用tfc.solve自动求解稳态压力场
#
# 【关键参数】
# 孔隙度: 边界区域 1e10（等效定压边界），内部 0.2
# 渗透率: 内部 1e-14 m^2，障碍物区域 0
# 孔隙模量: 200e6 Pa
# 流体: 水（密度1000 kg/m^3，粘度 1e-3 Pa.s）
# 边界压力: 左侧 3MPa，右侧 1MPa

from zmlx import *


def create(jx=100, jy=50):
    """
    创建存在不渗透障碍物的二维渗流模型。

    构建一个左右两侧定压、上下无流动的矩形多孔介质区域，
    并在区域中心设置一个圆形不渗透障碍物。

    Args:
        jx: x方向（水平方向）的网格单元数量，默认100
        jy: y方向（垂直方向）的网格单元数量，默认50

    Returns:
        model: 所创建的Seepage模型对象
    """
    # 创建矩形网格：x范围0~100m，y范围0~50m，z方向厚度1m
    mesh = create_cube(x=linspace(0, 100, jx + 1),
                       y=linspace(0, 50, jy + 1),
                       z=[0, 1])
    x_min, x_max = mesh.get_pos_range(0)

    # 定义孔隙度的空间分布：左右边界（x接近边界）孔隙度极大（等效定压边界），内部为0.2
    def get_fai(x, y, z):
        return 1.0e10 if abs(x - x_max) < 0.1 or abs(x - x_min) < 0.1 else 0.2

    # 定义初始压力的空间分布：左侧3MPa，右侧1MPa，内部2MPa
    def get_p(x, y, z):
        if abs(x - x_min) < 0.1:
            return 3e6
        if abs(x - x_max) < 0.1:
            return 1e6
        else:
            return 2e6

    # 定义渗透率的空间分布：中心半径15的圆形区域内渗透率为0（不渗透），其余为1e-14
    def get_k(x, y, z):
        return 0 if get_distance([x, y], [50, 25]) < 15 else 1e-14

    # 使用tfc引擎创建渗流模型
    model = tfc.create(mesh=mesh, cfl=0.2,
                       fludefs=[h2o.create(name='h2o', density=1000.0,
                                           viscosity=1.0e-3)],
                       porosity=get_fai, pore_modulus=200e6, p=get_p, s=1.0,
                       perm=get_k
                       )

    # 设置求解参数：最大模拟时间30天
    tfc.set_solve(model, time_max=3600 * 24 * 30)
    return model


def fig_data(model, jx, jy):
    """
    生成模型压力场的绘图数据。

    绘制压力分布云图，并叠加显示不渗透障碍物的位置（黑色虚线圆）。

    Args:
        model: Seepage模型对象
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量

    Returns:
        一个fig.axes2对象，包含压力云图和障碍物标记
    """
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jx, jy))
    p = tfc.get_p(model, shape=(jx, jy))
    # 生成圆形标记，显示不渗透障碍物的边界
    angles = np.linspace(0, 2 * np.pi, 100)
    return fig.axes2(
        fig.contourf(x, y, p, cbar=dict(label='Pressure', shrink=0.7), cmap='coolwarm'),
        fig.curve(50 + 15 * np.cos(angles), 25 + 15 * np.sin(angles), 'k--'),
        aspect='equal', xlabel='x/m', ylabel='y/m',
        title=f'Pressure. Time={tfc.get_time(model, as_str=True)}'
    )


def main():
    """
    主函数：创建模型并求解压力场。

    使用100x50的网格分辨率，求解存在圆形不渗透障碍物的稳态压力场，
    并在求解过程中实时显示压力分布。
    """
    jx, jy = 100, 50
    model = create(jx=jx, jy=jy)
    tfc.solve(model,
              extra_plot=lambda: fig.show(fig_data(model, jx, jy), caption='模型状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

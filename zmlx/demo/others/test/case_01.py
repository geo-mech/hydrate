# ** desc = '显示1维的，根据达西定律所计算出来的压力场'
#
# 本示例模拟一维达西流动，展示在恒定压差驱动下
# 多孔介质中压力沿流动方向的分布规律。
# 模型为50m长的一维流动管道（截面1m×1m），采用50个网格剖分。
# 左端压力3MPa，右端压力1MPa，形成2MPa的驱动压差。
# 流体为水（密度1000 kg/m^3，粘度1e-3 Pa·s），
# 渗透率1e-14 m^2，孔隙度0.2。
# 模拟时长30天，足够让压力场达到稳态（线性分布）。
# 结果绘制压力沿x轴的分布曲线，理论上应为一条直线，
# 验证达西定律的正确性和求解器的稳定性。

from zmlx import *


def create():
    """
    创建一维达西流动模型。

    模型为沿x方向的细长管道（50m长，截面1m×1m），
    两端分别施加3MPa和1MPa的恒定压力，模拟达西流动。
    采用50个网格沿x方向均匀剖分。

    Returns:
        返回创建的Seepage模型对象，包含网格、流体定义和边界条件。
    """
    mesh = create_cube(
        x=np.linspace(-25, 25, 50),  # x方向：-25到25m，50个网格
        y=[-0.5, 0.5],  # y方向：仅1个单元
        z=[-0.5, 0.5])  # z方向：仅1个单元（形成一维流动通道）
    x_min, x_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        """定义孔隙度：两端设极大值以固定压力边界条件"""
        return 1.0e10 if abs(x - x_max) < 0.1 or abs(x - x_min) < 0.1 else 0.2  # 边界10^10，内部0.2

    def get_p(x, y, z):
        """定义初始压力：左端3MPa，右端1MPa"""
        return 3e6 if x < 0 else 1e6  # 左半部分3MPa，右半部分1MPa

    model = tfc.create(
        mesh=mesh,
        cfl=0.2,  # 体积相对变化率限制（时间步长控制）
        fludefs=[h2o.create(name='h2o',  # 使用水作为流体
                            density=1000.0,  # 密度1000 kg/m^3
                            viscosity=1.0e-3)],  # 粘度1e-3 Pa·s
        porosity=get_fai,  # 函数定义：两端大孔隙固定压力
        pore_modulus=200e6,  # 孔隙模量200MPa
        p=get_p,  # 初始压力分布
        s=1.0,  # 初始饱和度：100%水
        perm=1e-14  # 渗透率1e-14 m^2
    )
    tfc.set_solve(
        model,
        time_max=3600 * 24 * 30  # 模拟总时长30天
    )
    return model


def show_model(model: Seepage):
    """
    可视化压力沿x轴的分布曲线。

    提取各单元的压力值，绘制压力-位置关系图。
    对于一维达西流动，稳态时压力应呈线性分布。

    Args:
        model: 待可视化的Seepage渗流模型对象。
    """
    x = as_numpy(model).cells.x  # 提取所有单元的x坐标
    p = as_numpy(model).cells.pre  # 提取所有单元的压力值
    plot_xy(x=x, y=p, xlabel='x', ylabel='p')  # 绘制压力沿x轴的分布


def main():
    """
    主函数：创建一维达西流动模型并求解。

    使用tfc.solve进行瞬态求解，总时长30天，足以达到稳态。
    求解过程中实时显示压力分布曲线，验证达西定律。

    Returns:
        无返回值。
    """
    model = create()
    gui.execute(lambda: tfc.solve(model,
              extra_plot=lambda: show_model(model)),  # 求解过程中实时显示压力分布
              close_after_done=False)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

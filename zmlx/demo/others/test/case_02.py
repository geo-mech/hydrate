# ** desc = '显示静水压力场'
#
# 本示例模拟在重力作用下的静水压力场分布。
# 模型为50m长的水平管道，但施加了x方向的重力加速度（-10 m/s^2），
# 模拟在重力场中流体柱的压力分布。
# 流体为水（密度1000 kg/m^3，粘度1e-3 Pa·s），
# 渗透率1e-14 m^2，孔隙度0.2。
# 初始压力为2MPa，在重力作用下压力沿x轴呈线性梯度分布。
# 模拟时长30天，压力从初始均匀分布逐渐演化为静水压力梯度分布，
# 理论上压力梯度为ρg = 1000×10 = 10000 Pa/m。
# 本例展示了zmlx中重力项的处理方法，对于理解地下流体
# 在重力作用下的分布具有重要意义。

from zmlx import *


def create():
    """
    创建静水压力场模型。

    模型为沿x方向的细长管道，施加x方向重力加速度，
    模拟流体在重力作用下的静水压力分布。
    初始压力均匀为2MPa，在重力作用下逐渐形成线性压力梯度。

    Returns:
        返回创建的Seepage模型对象。
    """
    mesh = create_cube(
        x=np.linspace(-25, 25, 50),  # x方向：-25到25m，50个网格
        y=[-0.5, 0.5],  # y方向：仅1个单元
        z=[-0.5, 0.5])  # z方向：仅1个单元（一维问题）

    model = tfc.create(
        mesh=mesh,
        cfl=0.2,  # 体积相对变化率限制
        fludefs=[h2o.create(  # 使用水作为流体
            name='h2o',
            density=1000.0,  # 密度1000 kg/m^3
            viscosity=1.0e-3)],  # 粘度1e-3 Pa·s
        porosity=0.2,  # 均匀孔隙度20%
        pore_modulus=200e6,  # 孔隙模量200MPa
        p=2e6,  # 初始均匀压力2MPa
        s=1.0,  # 初始饱和度100%水
        perm=1e-14,  # 渗透率1e-14 m^2
        gravity=[-10, 0, 0],  # x方向重力加速度-10m/s^2（沿x轴负方向）
    )
    tfc.set_solve(model,
                  time_max=3600 * 24 * 30  # 模拟总时长30天
                  )
    return model


def show_model(model: Seepage):
    """
    可视化静水压力沿x轴的分布曲线。

    提取各单元的压力值，绘制压力-位置关系图。
    稳态时压力应呈线性梯度分布，梯度为ρg = 10000 Pa/m。

    Args:
        model: 待可视化的Seepage渗流模型对象。
    """
    x = as_numpy(model).cells.x  # 提取所有单元的x坐标
    p = as_numpy(model).cells.pre  # 提取所有单元的压力值
    plot_xy(x=x, y=p, xlabel='x', ylabel='p')  # 绘制压力沿x轴的分布


def main():
    """
    主函数：创建静水压力模型并求解。

    使用tfc.solve进行瞬态求解，总时长30天，足以达到静水平衡。
    求解过程中实时显示压力分布曲线的演化。

    Returns:
        无返回值。
    """
    model = create()
    tfc.solve(
        model,
        extra_plot=lambda: show_model(model))  # 求解过程中实时显示压力分布


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

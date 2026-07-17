# ** desc = '密度差驱动下的对流+扩散的综合效应 (1)'
#
# 本案例模拟密度差驱动下的对流与扩散综合效应。在二维水平（xy）平面中设置两个
# 不同CO2浓度的圆形区域，由于浓度差导致密度差异，在重力作用下驱动流体运移。
# 同时，模型中还添加了CO2组分的扩散设置（扩散系数1.0e-9 m^2/s），从而同时
# 考虑对流和扩散两种传质机制。主要用于演示tfc求解器中扩散模块的启用方法
# 以及多组分输运的可视化。

from zmlx import *


def show(model: Seepage, jx, jy, time=None):
    """
    显示模型的压力和盐度
    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向
        time: 模拟的时间，单位：s
    """
    assert np is not None, 'numpy is not imported'
    if not gui:
        return
    # 将模型单元数据转为numpy数组并按网格形状重塑
    cells = as_numpy(model).cells
    x = np.reshape(cells.x, (jx, jy))
    y = np.reshape(cells.y, (jx, jy))
    # 获取CO2在液相中的浓度，并重塑为二维矩阵
    c = tfc.get_c(model, 'co2', 'liq', shape=[jx, jy])

    # 实施绘图：使用填充等值线展示CO2浓度分布
    fig.show(
        fig.axes2(
            fig.contourf(
                x, y, c, cmap='coolwarm',
                cbar={'label': 'CO2 Concentration', 'shrink': 0.7},
            ),
            title=f'CO2浓度分布. 时间={time2str(time)}', xlabel="x/m", ylabel="y/m",
            aspect='equal'
        ),
        fig.tight_layout(),
        caption='浓度分布'
    )


def main(jx=50, jy=50):
    """
    运行测试：创建模型、运行、绘制结果

    在二维平面上（50x50网格）设置初始CO2浓度不均匀分布：两个圆形区域分别具有
    0和0.1的CO2浓度，背景浓度为0.05。由于密度差和重力作用形成对流，
    同时CO2的分子扩散（D=1.0e-9 m^2/s）促使浓度均匀化。
    """
    # 创建二维矩形网格（xy平面，z方向厚度1m）
    # 第一个和最后一个Cell的体积设置为无穷大（边界条件）
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5]
    )

    # 定义流体：水溶液，CO2组分的质量分数范围[0.1, 1.1]
    fludefs = [create_aqueous(co2=[0.1, 1.1])]

    def get_s(x, y, z):
        """
        根据坐标设置初始CO2饱和度/组分分布
        在(0.3*jx, 0.3*jy)和(0.7*jx, 0.7*jy)两处设置圆形异常区
        """
        # 左下圆形区域：纯水（无CO2，高密度）
        if get_distance([x, y], [jx * 0.3, jy * 0.3]) < 3:
            return dict(h2o=1, co2=0)
        # 右上圆形区域：高CO2浓度（低密度）
        elif get_distance([x, y], [jx * 0.7, jy * 0.7]) < 3:
            return dict(h2o=0.9, co2=0.1)
        # 背景区域：中等CO2浓度
        else:
            return dict(h2o=0.95, co2=0.05)

    # 创建TFC耦合模型
    model = tfc.create(
        mesh=mesh,
        cfl=0.5,
        fludefs=fludefs,
        s=get_s,               # 初始组分分布函数
        use_mass=True,         # 使用质量守恒形式
        porosity=0.2,
        p=1.5e6,               # 初始压力 1.5 MPa
        perm=10e-15,           # 渗透率 10 mD
        gravity=[0, -1, 0]     # 重力沿y负方向
    )
    # 添加CO2扩散设置：扩散系数1.0e-9 m^2/s，扩散CFL限制0.2
    diffusion.add_setting(model, 'co2', 'liq', d=1.0e-9, cfl=0.2)

    # 设置初始时间步长和最大时间步长
    tfc.set_dt(model, 10)
    tfc.set_dt_max(model, 1e10)

    # 求解，最多100步，每一步后更新图形显示
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, time=tfc.get_time(model)),
              step_max=100)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

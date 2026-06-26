# ** desc = '密度差驱动下的对流+扩散的综合效应 (1)'

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
    cells = as_numpy(model).cells
    x = np.reshape(cells.x, (jx, jy))
    y = np.reshape(cells.y, (jx, jy))
    c = tfc.get_c(model, 'co2', 'liq', shape=[jx, jy])

    # 实施绘图
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
    """
    # 创建SeepageMesh(并将第一个和最后一个Cell的体积设置为无穷大)
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5]
    )

    fludefs = [create_aqueous(co2=[0.1, 1.1])]

    def get_s(x, y, z):
        if get_distance([x, y], [jx * 0.3, jy * 0.3]) < 3:
            return dict(h2o=1, co2=0)
        elif get_distance([x, y], [jx * 0.7, jy * 0.7]) < 3:
            return dict(h2o=0.9, co2=0.1)
        else:
            return dict(h2o=0.95, co2=0.05)

    model = tfc.create(
        mesh=mesh,
        cfl=0.5,
        fludefs=fludefs,
        s=get_s,
        use_mass=True,
        porosity=0.2,
        p=1.5e6,
        perm=10e-15,
        gravity=[0, -1, 0]
    )
    diffusion.add_setting(model, 'co2', 'liq', d=1.0e-9, cfl=0.2)

    tfc.set_dt(model, 10)
    tfc.set_dt_max(model, 1e10)

    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, time=tfc.get_time(model)), gui_mode=True, step_max=100)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

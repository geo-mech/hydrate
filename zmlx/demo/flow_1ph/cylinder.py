# ** desc = '单相流，两端固定压力，计算压力场 (在计算区域的中间，设置了一个不渗透的区域)'

from zmlx import *


def create(jx=100, jy=50):
    """
    创建模型.
    Args:
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量

    Returns:
        model: 模型对象
    """
    mesh = create_cube(x=linspace(0, 100, jx + 1),
                       y=linspace(0, 50, jy + 1),
                       z=[0, 1])
    x_min, x_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        return 1.0e10 if abs(x - x_max) < 0.1 or abs(x - x_min) < 0.1 else 0.2

    def get_p(x, y, z):
        if abs(x - x_min) < 0.1:
            return 3e6
        if abs(x - x_max) < 0.1:
            return 1e6
        else:
            return 2e6

    def get_k(x, y, z):
        return 0 if get_distance([x, y], [50, 25]) < 15 else 1e-14

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=[h2o.create(name='h2o', density=1000.0,
                                               viscosity=1.0e-3)],
                           porosity=get_fai, pore_modulus=200e6, p=get_p, s=1.0,
                           perm=get_k
                           )

    seepage.set_solve(model, time_max=3600 * 24 * 30)
    return model


def fig_data(model, jx, jy):
    x = seepage.get_x(model, shape=(jx, jy))
    y = seepage.get_y(model, shape=(jx, jy))
    p = seepage.get_p(model, shape=(jx, jy))
    angles = np.linspace(0, 2 * np.pi, 100)
    return fig.axes2(
        fig.contourf(x, y, p, cbar=dict(label='Pressure', shrink=0.7), cmap='coolwarm'),
        fig.curve(50 + 15 * np.cos(angles), 25 + 15 * np.sin(angles), 'k--'),
        aspect='equal', xlabel='x/m', ylabel='y/m',
        title=f'Pressure. Time={seepage.get_time(model, as_str=True)}'
    )


def main():
    """
    执行建模并且求解的主函数.
    """
    jx, jy = 100, 50
    model = create(jx=jx, jy=jy)
    seepage.solve(model, close_after_done=False,
                  extra_plot=lambda: fig.show(fig_data(model, jx, jy), caption='模型状态'))


if __name__ == '__main__':
    main()

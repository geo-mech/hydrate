# ** desc = '重力驱动下的对流'

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=linspace(-1, 1, jx + 1), y=[-0.5, 0.5], z=linspace(-2, 2, jz + 1)
    )
    fludefs = [create_aqueous(co2=[0.1, 1.1])]

    def get_s(x, y, z):
        if point_distance((x, z), (0, -1.5)) < 0.3:
            return dict(h2o=1.0, co2=0)
        elif point_distance((x, z), (0, 1.5)) < 0.3:
            return dict(h2o=0.9, co2=0.1)
        else:
            return dict(h2o=0.95, co2=0.05)

    model = tfc.create(
        mesh=mesh,
        dv_relative=0.5,
        fludefs=fludefs,
        s=get_s,
        use_mass=True,
        porosity=0.2,
        p=2e6,
        perm=10e-15,
        gravity=[0, 0, -10]
    )
    if np is not None:
        tfc.set_fa(model, 0, 'z0', tfc.get_z(model))
    model.add_tag('disable_update_vis', 'disable_ther')
    return model


def show(model: Seepage, caption=None):
    if not gui.exists():
        return

    assert np is not None, 'numpy is not imported'

    angles = linspace(0, np.pi * 2, 100)
    c1 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 + 1.5, 'k--')
    c2 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 - 1.5, 'r--')

    def f(figure):
        assert np is not None, 'numpy is not imported'
        figure.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}')
        x = tfc.get_x(model)
        y = tfc.get_z(model)
        x0, x1, y0, y1 = float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))
        layout = AutoFigLayout(figure, 3, (x1 - x0) / (y1 - y0), xlabel='x / m', ylabel='z / m',
                               aspect='equal')
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_den(model, 0), cbar=dict(label='密度'),
                              title='密度')
        fig.add_to_axes(ax, c1, c2)
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_fa(model, 0, 'z0'), cbar=dict(label='流体z0'),
                              title='流体Z0')
        fig.add_to_axes(ax, c1, c2)
        ax = layout.add_axes2(add_tricontourf, x, y, tfc.get_c(model, 'co2', 'liq'),
                              cbar=dict(label='co2浓度'),
                              title='co2浓度')
        fig.add_to_axes(ax, c1, c2)

    if caption is None:
        caption = f"Seepage({model.handle_str})"
    plot_on_figure(f, caption=caption, clear=True, tight_layout=True)


def main():
    jx, jz = 50, 100
    model = create(jx, jz)
    show(model, caption='初始状态')
    tfc.solve(model, time_max=3600 * 24 * 2000, extra_plot=lambda: show(model, caption='最新状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)

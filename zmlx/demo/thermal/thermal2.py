# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


def create():
    return seepage.create(
        mesh=create_cube(
            np.linspace(-50, 50, 50),
            np.linspace(-50, 50, 50),
            (-0.5, 0.5)),
        temperature=lambda *pos: 380 if point_distance(pos, (
            0, 0, 0)) < 30 else 280,
        denc=1.0e6,
        heat_cond=1.0,
        dt_max=1.0e6,
        texts={'solve': {'step_max': 500, }}
    )


def show(model: Seepage):
    def on_figure(fig):
        add_axes2(fig, add_tricontourf, seepage.get_x(model), seepage.get_y(model),
                  seepage.get_ca(model, model.get_cell_key('temperature')),
                  caption='temperature',
                  xlabel='x (m)', ylabel='y (m)', aspect='equal',
                  cbar={'label': 'temperature (K)'}, cmap='coolwarm',
                  )

    plot(on_figure, clear=True, caption='模型状态')


def main():
    model = create()
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model))


if __name__ == '__main__':
    main()

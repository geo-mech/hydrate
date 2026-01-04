from zmlx.fig.plt_render.field2 import add_field2


def show_field2(f, xr, yr, **opts):
    """
    显示一个二维的场，用于测试
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    plot(add_axes2, add_field2, f, xr, yr, **opts)


def test():
    from zmlx.fluid.ch4 import create
    flu = create()
    show_field2(
        flu.den, xr=[4e6, 15e6], yr=[274, 290], caption='Density',
        cbar=dict(label='Density', title='Title', shrink=0.5),
        xlabel='Pressure / MPa', ylabel='Temperature',
        title='Density', cmap='coolwarm',
        x_times=1.0e-6
    )
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='Viscosity')


if __name__ == '__main__':
    from zmlx import gui

    gui.execute(test, close_after_done=False)

from zmlx.plt.plot_on_axes import plot_on_axes


def show_field2(f, xr, yr, clabel=None, **opts):
    """
    显示一个二维的场，用于测试
    """
    def on_axes(ax):
        x = []
        y = []
        z = []
        va = [xr[0] + (xr[1] - xr[0]) * i * 0.01 for i in range(101)]
        vb = [yr[0] + (yr[1] - yr[0]) * i * 0.01 for i in range(101)]
        for a in va:
            for b in vb:
                x.append(a)
                y.append(b)
                z.append(f(a, b))
        item = ax.tricontourf(
            x, y, z,
            levels=30,
            cmap='coolwarm',
            antialiased=True
        )
        cbar = ax.get_figure().colorbar(item, ax=ax)
        if isinstance(clabel, str):
            cbar.set_label(clabel)

    plot_on_axes(on_axes, **opts)


def test_1():
    from zmlx.fluid.ch4 import create
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test_1, close_after_done=False)

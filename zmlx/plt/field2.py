def add_field2(ax, f, xr, yr, *, cmap=None, levels=None, clabel=None):
    """
    显示一个二维的场，用于测试
    """
    va = [xr[0] + (xr[1] - xr[0]) * i * 0.01 for i in range(101)]
    vb = [yr[0] + (yr[1] - yr[0]) * i * 0.01 for i in range(101)]
    x = []
    y = []
    z = []
    for a in va:
        for b in vb:
            x.append(a)
            y.append(b)
            z.append(f(a, b))
    res = ax.tricontourf(
        x, y, z,
        levels=levels,
        cmap=cmap,
        antialiased=True
    )
    if clabel is not None:
        cbar = ax.get_figure().colorbar(res, ax=ax)
        cbar.set_label(clabel)
    return res


def show_field2(f, xr, yr, clabel=None, cmap=None, levels=None, **opts):
    """
    显示一个二维的场，用于测试
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    plot(add_axes2, add_field2, f, xr, yr, cmap=cmap,
         levels=levels, clabel=clabel, **opts)


def test_1():
    from zmlx.fluid.ch4 import create
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test_1, close_after_done=False)

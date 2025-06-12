def add_dfn2(ax, dfn2):
    """
    将一个二维的离散裂缝网络添加到Axes上.
    """
    for pos in dfn2:
        ax.plot([pos[0], pos[2]], [pos[1], pos[3]])


def show_dfn2(dfn2, **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络. 主要用于测试.
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    def on_axes(ax):
        add_dfn2(ax, dfn2)

    opts.setdefault('aspect', 'equal')
    plot(add_axes2, on_axes, **opts)


def __test():
    from zmlx.geometry.dfn2 import dfn2
    fractures = dfn2(
        lr=[10, 100], ar=[0, 1], p21=0.2, xr=[-100, 100],
        yr=[-100, 100], l_min=2)
    show_dfn2(fractures)


if __name__ == '__main__':
    __test()

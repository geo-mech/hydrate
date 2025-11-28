def add_dfn2(ax, dfn2, **opts):
    """
    将一个二维的离散裂缝网络添加到Axes上.
    注意：
        此函数效率有待优化
    """
    for pos in dfn2:
        ax.plot([pos[0], pos[2]], [pos[1], pos[3]], **opts)


def show_dfn2(dfn2, **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络. 主要用于测试.
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    default_opts = dict(
        aspect='equal',
        xlabel='x / m', ylabel='y / m',
        title='Discrete Fracture Network', tight_layout=True)
    opts = {**default_opts, **opts}

    plot(add_axes2, add_dfn2, dfn2, **opts)


def test():
    from zmlx.geometry.dfn2 import dfn2
    fractures = dfn2(
        lr=[10, 100], ar=[0, 1], p21=0.2, xr=[-100, 100],
        yr=[-100, 100], l_min=2)
    show_dfn2(fractures)


if __name__ == '__main__':
    test()

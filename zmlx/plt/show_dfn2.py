from zmlx.plt.plot_on_axes import plot_on_axes


def show_dfn2(dfn2, **opts):
    """
    利用画线的方式显示一个二维的离散裂缝网络. 主要用于测试.
    """

    def on_axes(ax):
        for pos in dfn2:
            ax.plot([pos[0], pos[2]], [pos[1], pos[3]])

    plot_on_axes(on_axes, **opts)


def __test():
    from zmlx.geometry.dfn2 import dfn2
    fractures = dfn2(lr=[10, 100], ar=[0, 1], p21=0.2, xr=[-100, 100],
                     yr=[-100, 100], l_min=2)
    show_dfn2(fractures)


if __name__ == '__main__':
    __test()

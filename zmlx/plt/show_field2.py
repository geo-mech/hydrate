from zmlx.ui.GuiBuffer import plot


def show_field2(f, xr, yr, xlabel=None, ylabel=None, clabel=None, title=None,
                **opts):
    """
    显示一个二维的场，用于测试
    """

    def on_figure(fig):
        ax = fig.subplots()
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
        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        item = ax.tricontourf(
            x, y, z,
            levels=30,
            cmap='coolwarm',
            antialiased=True
        )
        cbar = fig.colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    plot(on_figure, **opts)

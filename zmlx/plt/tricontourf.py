from zmlx.ui.GuiBuffer import plot


def _load(ipath=None, ix=None, iy=None, iz=None):
    import numpy as np
    data = np.loadtxt(ipath, float)
    return data[:, ix], data[:, iy], data[:, iz]


def tricontourf(x=None, y=None, z=None,
                ipath=None, ix=None, iy=None, iz=None,
                title=None,
                triangulation=None,
                levels=20,
                cmap='coolwarm',
                xlabel='x',
                ylabel='y',
                clabel=None,
                aspect='equal',
                **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """

    def on_figure(fig):
        ax = fig.subplots()

        if aspect is not None:
            ax.set_aspect(aspect)

        if xlabel is not None:
            ax.set_xlabel(xlabel)

        if ylabel is not None:
            ax.set_ylabel(ylabel)

        if title is not None:
            ax.set_title(title)

        args = (x, y, z) if ipath is None else _load(ipath, ix, iy, iz)
        if triangulation is None:
            item = ax.tricontourf(*args, levels=levels, cmap=cmap, antialiased=True)
        else:
            item = ax.tricontourf(triangulation, args[2], levels=levels, cmap=cmap, antialiased=True)

        cbar = fig.colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    plot(on_figure, **opts)

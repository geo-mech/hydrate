from zmlx.plt.plot_on_axes import plot_on_axes


def _load(ipath=None, ix=None, iy=None, iz=None):
    import numpy as np
    data = np.loadtxt(ipath, float)
    return data[:, ix], data[:, iy], data[:, iz]


def tricontourf(x=None, y=None, z=None,
                ipath=None, ix=None, iy=None, iz=None,
                triangulation=None,
                levels=20,
                cmap='coolwarm',
                clabel=None,
                **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """

    def on_axes(ax):
        args = (x, y, z) if ipath is None else _load(ipath, ix, iy, iz)
        if triangulation is None:
            item = ax.tricontourf(*args, levels=levels, cmap=cmap,
                                  antialiased=True)
        else:
            item = ax.tricontourf(triangulation, args[2], levels=levels,
                                  cmap=cmap, antialiased=True)

        cbar = ax.get_figure().colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    opts.setdefault('aspect', 'equal')
    plot_on_axes(on_axes, **opts)

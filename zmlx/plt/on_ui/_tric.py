from zmlx.plt.on_axes import add_tricontourf
from zmlx.plt.on_figure import plot_on_axes


def show_tricontourf(
        x=None, y=None, z=None,
        ipath=None, ix=None, iy=None, iz=None,
        triangulation=None,
        clabel=None, cbar=None,
        gui_mode=None, caption=None,
        **opts
):
    """
    利用给定的x，y，z来画一个二维的云图.
    """
    if x is None or y is None or z is None:
        if ipath is not None:
            from zmlx.io.xyz import load_xyz
            x, y, z = load_xyz(ipath, ix, iy, iz)

    opts.setdefault('aspect', 'equal')
    opts.setdefault('tight_layout', True)
    if clabel is not None:
        if cbar is None:
            cbar = dict(label=clabel)
        else:
            cbar.setdefault('label', clabel)

    def on_ax(ax):
        if triangulation is None:
            add_tricontourf(ax, x, y, z, cbar=cbar, antialiased=True)
        else:
            add_tricontourf(ax, triangulation, z, cbar=cbar, antialiased=True)

    plot_on_axes(on_ax, gui_mode=gui_mode, caption=caption, **opts)


def test():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    show_tricontourf(x.flatten(), y.flatten(), z.flatten(),
                     title='Triangle Contourf', xlabel='x', ylabel='y', gui_mode=True)


if __name__ == '__main__':
    test()

from zmlx.fig.plt_render.tricontourf import add_tricontourf
from zmlx.io.xyz import load_xyz

on_axes = add_tricontourf


def tricontourf(
        x=None, y=None, z=None,
        ipath=None, ix=None, iy=None, iz=None,
        triangulation=None,
        clabel=None, cbar=None,
        gui_mode=None, caption=None,
        **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """
    from zmlx.fig import tric, axes2, plt_show

    if ipath is not None:
        x, y, z = load_xyz(ipath, ix, iy, iz)

    opts = {'aspect': 'equal', 'tight_layout': True, **opts}
    if clabel is not None:
        if cbar is None:
            cbar = dict(label=clabel)
        else:
            cbar.setdefault('label', clabel)

    if triangulation is None:
        o = tric(x, y, z, cbar=cbar, antialiased=True)
    else:
        o = tric(triangulation, z, cbar=cbar, antialiased=True)

    plt_show(axes2(o, **opts),
             gui_mode=gui_mode, caption=caption)


def test():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    tricontourf(x.flatten(), y.flatten(), z.flatten(),
                title='Triangle Contourf', xlabel='x', ylabel='y', gui_mode=True)


if __name__ == '__main__':
    test()

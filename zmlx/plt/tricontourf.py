from zmlx.io.xyz import load_xyz
from zmlx.plt.cbar import add_cbar


def add_tricontourf(ax, *args, cbar=None, **opts):
    """
    绘制二维填充等高线图.
    Args:
        ax: Axes对象，用于绘制二维填充等高线图
        *args: 传递给ax.tricontourf函数的参数
        cbar: 颜色条的配置参数，字典形式
        **opts: 传递给ax.tricontourf函数的关键字参数
    Returns:
        绘制的填充等高线图对象
    """
    opts.setdefault('antialiased', True)
    obj = ax.tricontourf(*args, **opts)
    if cbar is not None:
        add_cbar(ax, obj=obj, **cbar)
    return obj


on_axes = add_tricontourf


def tricontourf(
        x=None, y=None, z=None,
        ipath=None, ix=None, iy=None, iz=None,
        triangulation=None,
        clabel=None, cbar=None,
        **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    if ipath is not None:
        x, y, z = load_xyz(ipath, ix, iy, iz)

    opts = {'aspect': 'equal', 'antialiased': True, 'tight_layout': True, **opts}
    if clabel is not None:
        if cbar is None:
            cbar = dict(label=clabel)
        else:
            cbar.setdefault('label', clabel)

    if triangulation is None:
        plot(add_axes2, add_tricontourf, x, y, z, cbar=cbar, **opts)
    else:
        plot(add_axes2, add_tricontourf, triangulation, z, cbar=cbar, **opts)


def test():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    tricontourf(x.flatten(), y.flatten(), z.flatten(), gui_mode=True,
                title='Triangle Contourf', xlabel='x', ylabel='y', )


if __name__ == '__main__':
    test()

from zmlx.plt.on_figure import add_axes2
from zmlx.ui import plot

__all__ = ['tricontourf', 'on_axes', 'add_tricontourf']


def add_tricontourf(ax, *args, cbar=None, **kwargs):
    """
    绘制二维填充等高线图.
    Args:
        ax: Axes对象，用于绘制二维填充等高线图
        *args: 传递给ax.tricontourf函数的参数
        cbar: 颜色条的配置参数，字典形式
        **kwargs: 传递给ax.tricontourf函数的关键字参数
    Returns:
        绘制的填充等高线图对象
    """
    kwargs.setdefault('antialiased', True)
    obj = ax.tricontourf(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


on_axes = add_tricontourf


def tricontourf(
        x=None, y=None, z=None,
        ipath=None, ix=None, iy=None, iz=None,
        triangulation=None,
        clabel=None,
        **opts):
    """
    利用给定的x，y，z来画一个二维的云图.
    """

    def _load(ipath_=None, ix_=None, iy_=None, iz_=None):
        import numpy as np
        data = np.loadtxt(ipath_, float)
        return data[:, ix_], data[:, iy_], data[:, iz_]

    if ipath is not None:
        x, y, z = _load(ipath, ix, iy, iz)

    opts.setdefault('aspect', 'equal')
    opts.setdefault('antialiased', 'True')
    opts.setdefault('tight_layout', True)
    cbar = dict(label=clabel)
    if triangulation is None:
        plot(add_axes2, add_tricontourf, x, y, z, cbar=cbar, **opts)
    else:
        plot(add_axes2, add_tricontourf, triangulation, z, cbar=cbar, **opts)

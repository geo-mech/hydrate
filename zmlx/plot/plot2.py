# -*- coding: utf-8 -*-
"""
基于Matplotlib的二维绘图
"""

from zml import gui, plot as do_plot
from zmlx.plot.kernels import kernels

version = 221027


def plot2(caption=None, gui_only=False, title=None, fname=None, dpi=300,
          xlabel='x', ylabel='y', clear=True,
          data=None, aspect=None, on_top=None):
    """
    调用其它内核函数来做一个二维的绘图. 可以多个数据叠加绘图;
    其中plots为绘图的数据，其中的每一个item都是一个dict，在每一个dict中，必须包含三个元素：name, args和krargs
    """
    if gui_only and not gui.exists():
        return
    if data is None:
        return

    def f(fig):
        """
        执行绘图
        """
        ax = fig.subplots()
        if aspect is not None:
            ax.set_aspect(aspect)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        for d in data:
            name = d.get('name')
            if name is not None:
                try:
                    kernel = kernels.get(name, None)
                    if kernel is not None:
                        x = kernel(ax, *d.get('args', []), **d.get('kwargs', {}))
                        if d.get('has_colorbar', False):
                            fig.colorbar(x, ax=ax)
                    else:
                        print(f'Warning: can not found kernel <{name}>')
                except Exception as e:
                    print(f'Error: {e}')
                    pass

    # 在gui界面上绘图
    do_plot(kernel=f, caption=caption, clear=clear, fname=fname, dpi=dpi, on_top=on_top)


def _test():
    """
    测试
    """
    import matplotlib.tri as mtri
    import numpy as np

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5])
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x)
    d1 = {'name': 'tricontourf', 'kwargs': {'triangulation': triang, 'z': z, 'levels': 30}, 'has_colorbar': True}

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5]) + 3
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x) + 3
    d2 = {'name': 'tricontourf', 'kwargs': {'triangulation': triang, 'z': z, 'levels': 10}}

    x = np.linspace(0, 5, 100)
    y = np.sin(x)
    d3 = {'name': 'plot', 'args': [x, y], 'kwargs': {'c': (1, 0, 0, 0.5)}}

    x = np.linspace(0, 5, 100)
    y = np.cos(x)
    d4 = {'name': 'plot', 'args': [x, y], 'kwargs': {'c': 'r', 'linewidth': 0.1}}

    plot2(caption=None, gui_only=False, title=None, fname=None, dpi=200,
          xlabel='x', ylabel='y', clear=True,
          data=(d1, d2, d3, d4))


if __name__ == '__main__':
    _test()

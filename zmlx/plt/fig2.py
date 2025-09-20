"""
这里，定义在gui上绘图的顶层的函数，直接操作gui或者在控制台绘图.
"""
from zmlx.exts.base import np
from zmlx.plt.contourf import contourf
from zmlx.plt.curve2 import plotxy, plot_xy
from zmlx.plt.dfn2 import show_dfn2
from zmlx.plt.field2 import show_field2
from zmlx.plt.fn2 import show_fn2
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import tricontourf
from zmlx.plt.trimesh import trimesh
from zmlx.ui import plot

_keep = [contourf, plotxy, plot_xy, show_dfn2, show_field2,
         tricontourf, show_fn2, trimesh
         ]


def tricontourf_(
        ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None,
        iz=None,
        triangulation=None, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if ipath is not None:
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]
        if iz is not None:
            z = data[:, iz]

    if triangulation is None:
        return ax.tricontourf(x, y, z, levels=levels, cmap=cmap,
                              antialiased=True)
    else:
        return ax.tricontourf(triangulation, z, levels=levels,
                              cmap=cmap, antialiased=True)


kernels = {'tricontourf': tricontourf_}


def plot2(data=None, **opts):
    """
    调用内核函数来做一个二维的绘图. 可以多个数据叠加绘图;
    其中plots为绘图的数据，其中的每一个item都是一个dict，
        在每一个dict中，必须包含三个元素：name, args和kwargs
    """

    def on_axes(ax):
        """
        执行绘图
        """
        if data is None:
            return
        for d in data:
            name = d.get('name')
            if name is None:
                continue
            args, kwargs, kwds = d.get('args', []), d.get(
                'kwargs', {}), d.get('kwds', {})
            kwargs.update(kwds)  # 优先使用kwds
            succeed = False
            obj = None
            if not succeed:
                try:  # 优先去使用标准的版本
                    obj = getattr(ax, name, None)(*args, **kwargs)
                    succeed = True
                except:
                    pass
            if not succeed:
                try:  # 尝试使用自定义的内核函数
                    obj = kernels.get(name)(ax, *args, **kwargs)
                    succeed = True
                except:
                    pass
            if succeed:  # 绘图成功，尝试添加colorbar
                clabel = d.get('clabel')
                if d.get('has_colorbar') or clabel is not None:
                    cbar = ax.get_figure().colorbar(obj, ax=ax)
                    if clabel is not None:
                        cbar.set_label(clabel)
            else:
                print(f'plot failed: name={name}, '
                      f'args={args}, kwargs={kwargs}')

    plot(add_axes2, on_axes, dim=2, **opts)

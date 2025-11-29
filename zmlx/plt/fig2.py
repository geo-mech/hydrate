"""
这里，定义在gui上绘图的顶层的函数，直接操作gui或者在控制台绘图.
"""

from zmlx.io.xyz import load_xyz
from zmlx.plt.contourf import contourf
from zmlx.plt.curve2 import plotxy, plot_xy
from zmlx.plt.dfn2 import show_dfn2
from zmlx.plt.field2 import show_field2
from zmlx.plt.fn2 import show_fn2
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import tricontourf, add_tricontourf
from zmlx.plt.trimesh import trimesh

_keep = [contourf, plotxy, plot_xy, show_dfn2, show_field2,
         tricontourf, show_fn2, trimesh
         ]


def tricontourf_(
        ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None,
        iz=None,
        triangulation=None, **opts):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if ipath is not None:
        x2, y2, z2 = load_xyz(ipath, ix=ix, iy=iy, iz=iz)
        if x2 is not None:
            x = x2
        if y2 is not None:
            y = y2
        if z2 is not None:
            z = z2

    opts = {'antialiased': True, 'cmap': 'coolwarm', 'levels': 20,
            **opts}
    if triangulation is None:
        return add_tricontourf(ax, x, y, z, **opts)
    else:
        return add_tricontourf(ax, triangulation, z, **opts)


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

    from zmlx.ui import plot
    plot(add_axes2, on_axes, **opts)

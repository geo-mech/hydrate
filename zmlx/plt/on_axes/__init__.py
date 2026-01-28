"""
在这里，处理对axes的各种操作。这是定义绘图的底层的操作。
"""
from zmlx.plt.on_axes.cbar import add_cbar
from zmlx.plt.on_axes.contourf import add_contourf as contourf
from zmlx.plt.on_axes.data import item, add_items, plot2d, plot3d
from zmlx.plt.on_axes.scatter import add_scatter as scatter3
from zmlx.plt.on_axes.tricontourf import add_tricontourf as tricontourf
from zmlx.plt.on_axes.trisurf import add_trisurf as trisurf3

_keep = [contourf, trisurf3, tricontourf, scatter3, item, add_items]


def add_subplot(*args, **kwargs):
    from zmlx.plt.on_figure import add_subplot as impl
    return impl(*args, **kwargs)


def add_axes2(*args, **kwargs):
    from zmlx.plt.on_figure import add_axes2 as impl
    return impl(*args, **kwargs)


def add_axes3(*args, **kwargs):
    from zmlx.plt.on_figure import add_axes3 as impl
    return impl(*args, **kwargs)


def colorbar(ax, obj, **opts):
    """
    为Axes添加颜色条.
    Args:
        ax: Axes对象，用于添加颜色条
        obj: 用于创建颜色条的对象，例如散点图、填充等高线图等
        **opts: 传递给ax.colorbar函数的关键字参数
    Returns:
        颜色条对象
    """
    return add_cbar(ax, obj=obj, **opts)


def call_ax(ax, name, *args, **kwargs):
    """
    调用Axes的方法，在ax上绘图。
    Args:
        ax: Axes对象，用于绘制图形
        name: 方法的名称，字符串形式
        *args: 传递给方法的参数
        **kwargs: 传递给方法的关键字参数
    Returns:
        调用方法的返回值
    """
    return getattr(ax, name)(*args, **kwargs)


def curve(ax, *args, **kwargs):
    """
    绘制曲线图.
    Args:
        ax: Axes对象，用于绘制曲线图
        *args: 传递给ax.plot函数的参数
        **kwargs: 传递给ax.plot函数的关键字参数
    Returns:
        绘制的曲线对象
    """
    return ax.plot(*args, **kwargs)


def plot_on_axes(on_axes, dim=2, **opts):
    """
    给定on_axes的函数，然后在界面上绘图。
    注意：
        此函数后续废弃。
    """
    from zmlx.ui import plot
    add_axes = add_axes2 if dim == 2 else add_axes3
    return plot(add_axes, on_axes, **opts)


def test_1():
    from zmlx.data.surf import get_data
    from zmlx.plt.cmap import get_cm
    from zmlx.plt.on_axes.data import surf, cbar, add_items

    cmap = get_cm('jet')
    x, y, z, v = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    v0 = v.min()
    v1 = v.max() + 1
    items = [
        surf(x, y, z, v, clim=(v0, v1), cmap=cmap),
        surf(x + 10, y, z + 1, v + 1,
             clim=(v0, v1), alpha=v + 1, cmap=cmap),
        cbar(clim=(v0, v1), label='Hehe', shrink=0.5, cmap=cmap)
    ]
    plot3d(*items)


def test_2():
    import numpy as np
    from zmlx.plt.cmap import get_cm
    from zmlx.geometry.dfn2 import dfn2 as make_fractures
    from zmlx.plt.on_axes import data

    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    a = np.linspace(-4, 15, 100)
    b = np.sin(a)
    fractures = make_fractures(
        lr=[2, 10], ar=[0, 1], p21=4,
        xr=[-5, 17],
        yr=[5, 17.5], l_min=0.2
    )

    cmap = get_cm('coolwarm')

    items = [
        data.cont(x, y, z, cmap=cmap),
        data.tric(x.flatten() + 12, y.flatten(), z.flatten(),
                  cmap=cmap),
        data.cbar(clim=(-1, 1), label='label', title='title',
                  shrink=0.8, cmap=cmap),
        data.comb(
            data.curve(a, b),
            data.curve(a, b + 1),
            data.curve(a, b + 2),
        ),
        data.dfn2(fractures),
        data.comb(
            data.xlabel('x/m'),
            data.ylabel('y/m'),
            data.comb(
                data.aspect('equal'),
                data.xlim([-3, 16]),
            )
        ),
    ]
    plot2d(*items)


if __name__ == '__main__':
    test_2()

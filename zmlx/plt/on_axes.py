"""
在这里，处理对axes的各种操作。这是定义绘图的底层的操作。
"""

from zmlx.fig import add_to_axes as add_items
from zmlx.fig import data as fig
from zmlx.fig.data import item
from zmlx.fig.plt_render import add_scatter as scatter3
from zmlx.plt.cbar import add_cbar
from zmlx.plt.contourf import add_contourf as contourf
from zmlx.plt.on_figure import add_subplot, add_axes2, add_axes3
from zmlx.plt.tricontourf import add_tricontourf as tricontourf
from zmlx.plt.trisurf import add_trisurf as trisurf3

_keep = [contourf, trisurf3, tricontourf, scatter3, item, add_items,
         add_subplot, add_axes2, add_axes3]


def plot2d(*items, **opts):
    """
    绘制二维图.
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    from zmlx.ui import plot
    plot(add_axes2, add_items, *items, **opts)


def plot3d(*items, **opts):
    """
    绘制三维图.
    Args:
        *items: 项目的元组，每个元组包含项目的名称、参数和关键字参数
        **opts: 传递给plot函数的关键字参数

    Returns:
        None
    """
    from zmlx.ui import plot
    plot(add_axes3, add_items, *items, **opts)


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
    from zmlx.plt.on_figure import add_axes2, add_axes3
    from zmlx.ui import plot
    add_axes = add_axes2 if dim == 2 else add_axes3
    return plot(add_axes, on_axes, **opts)


def test_1():
    """
    测试plot3d函数.
    """
    from zmlx.plt.data.surf import get_data
    from zmlx.plt.cmap import get_cm
    from zmlx.fig import surf, cbar, show, axes3, tight_layout

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
    show(axes3(*items), tight_layout(), caption='Test')


def test_2():
    """
    测试plot2d函数.
    """
    from zmlx.plt.cmap import get_cm
    import numpy as np
    from zmlx.geometry.dfn2 import dfn2 as make_fractures
    from zmlx import fig

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
        fig.cont(x, y, z, cmap=cmap),
        fig.tric(x.flatten() + 12, y.flatten(), z.flatten(),
                 cmap=cmap),
        fig.cbar(clim=(-1, 1), label='label', title='title',
                 shrink=0.8, cmap=cmap),
        fig.comb(
            fig.curve(a, b),
            fig.curve(a, b + 1),
            fig.curve(a, b + 2),
        ),
        fig.dfn2(fractures),
        fig.comb(
            fig.xlabel('x/m'),
            fig.ylabel('y/m'),
            fig.comb(
                fig.aspect('equal'),
                fig.xlim([-3, 16]),
            )
        ),
    ]
    fig.show(fig.axes2(*items), fig.tight_layout(), caption='Test', gui_mode=True)


if __name__ == '__main__':
    test_1()

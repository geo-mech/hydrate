"""
在这里，处理对axes的各种操作。这是定义绘图的底层的操作。
"""
from zmlx.plt.on_axes._cbar import add_cbar
from zmlx.plt.on_axes._contourf import add_contourf as contourf, add_contourf
from zmlx.plt.on_axes._dfn2 import add_dfn2
from zmlx.plt.on_axes._field2 import add_field2
from zmlx.plt.on_axes._fn2 import add_fn2
from zmlx.plt.on_axes._legend import add_legend
from zmlx.plt.on_axes._rc3 import add_rc3
from zmlx.plt.on_axes._scatter import add_scatter as scatter3, add_scatter
from zmlx.plt.on_axes._seepage_mesh import add_seepage_mesh
from zmlx.plt.on_axes._surf import add_surf
from zmlx.plt.on_axes._tricontourf import add_tricontourf as tricontourf, add_tricontourf
from zmlx.plt.on_axes._trimesh import add_trimesh
from zmlx.plt.on_axes._trisurf import add_trisurf as trisurf3, add_trisurf

_keep = [contourf, trisurf3, tricontourf, scatter3]


def add_subplot(*args, **kwargs):
    """
    在Figure上添加一个子图，返回Axes对象。
    Args:
        *args: 传递给fig.add_subplot函数的参数
        **kwargs: 传递给fig.add_subplot函数的关键字参数

    Returns:
        Axes对象
    """
    from zmlx.plt.on_figure import add_subplot as impl
    return impl(*args, **kwargs)


def add_axes2(*args, **kwargs):
    """
    在Figure上添加一个2D子图，返回Axes对象。
    Args:
        *args: 传递给fig.add_subplot函数的参数
        **kwargs: 传递给fig.add_subplot函数的关键字参数

    Returns:
        Axes对象
    """
    from zmlx.plt.on_figure import add_axes2 as impl
    return impl(*args, **kwargs)


def add_axes3(*args, **kwargs):
    """
    在Figure上添加一个3D子图，返回Axes对象。
    Args:
        *args: 传递给fig.add_subplot函数的参数
        **kwargs: 传递给fig.add_subplot函数的关键字参数

    Returns:
        Axes对象
    """
    from zmlx.plt.on_figure import add_axes3 as impl
    return impl(*args, **kwargs)


def plot_on_axes(on_axes, *args, dim=2, **opts):
    """
    给定on_axes的函数，然后在界面上绘图。
    """
    from zmlx.plt.on_figure import plot_on_axes as impl
    return impl(on_axes, *args, dim=dim, **opts)


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


def add_curve(ax, *args, **kwargs):
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


curve = add_curve
add_curve2 = add_curve

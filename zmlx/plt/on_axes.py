"""
在这里，处理对axes的各种操作。这是定义绘图的底层的操作。
"""

def scatter3(ax, *args, cbar=None, **kwargs):
    """
    在给定Axes上绘制散点图.
    Args:
        ax: Axes对象，用于绘制散点图
        cbar: 创建colorbar的参数
        *args: 传递给ax.scatter的参数
        **kwargs: 传递给ax.scatter函数的关键字参数
    Returns:
        绘制的散点图对象
    """
    obj = ax.scatter(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


def contourf(ax, *args, cbar=None, **kwargs):
    """
    绘制二维填充等高线图（云图）。
    Args:
        ax: Axes对象，用于绘制二维填充等高线图
        cbar: 颜色条的配置参数，字典形式
        *args: 传递给ax.contourf函数的参数
        **kwargs: 传递给ax.contourf函数的关键字参数
    Returns:
        绘制的填充等高线图对象
    """
    kwargs.setdefault('antialiased', True)
    obj = ax.contourf(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


def tricontourf(ax, *args, cbar=None, **kwargs):
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


def trisurf3(ax, *args, cbar=None, **kwargs):
    """
    绘制三维三角化曲面图.
    Args:
        ax: Axes对象，用于绘制三维三角化曲面图
        cbar: 颜色条的配置参数，字典形式
        *args: 传递给ax.plot_trisurf函数的参数
        **kwargs: 传递给ax.plot_trisurf函数的关键字参数
    Returns:
        绘制的三维三角化曲面图对象
    """
    kwargs.setdefault('antialiased', True)
    obj = ax.plot_trisurf(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj

def add_subplot(*args, **kwargs):
    from zmlx.plt.on_figure import add_subplot as impl
    return impl(*args, **kwargs)

def add_axes2(*args, **kwargs):
    from zmlx.plt.on_figure import add_axes2 as impl
    return impl(*args, **kwargs)

def add_axes3(*args, **kwargs):
    from zmlx.plt.on_figure import add_axes3 as impl
    return impl(*args, **kwargs)

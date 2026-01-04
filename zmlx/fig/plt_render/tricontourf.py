from zmlx.fig.plt_render.cbar import add_cbar


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

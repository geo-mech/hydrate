from zmlx.fig.plt_render.cbar import add_cbar


def add_contourf(ax, *args, cbar=None, **kwargs):
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
    obj = ax.contourf(*args, **kwargs)
    if cbar is not None:
        add_cbar(ax, obj=obj, **cbar)
    return obj

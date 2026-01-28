from zmlx.plt.on_axes.cbar import add_cbar


def add_scatter(ax, *args, cbar=None, **kwargs):
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
        add_cbar(ax, obj=obj, **cbar)
    return obj

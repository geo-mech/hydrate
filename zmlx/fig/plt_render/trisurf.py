from zmlx.fig.plt_render.cbar import add_cbar


def add_trisurf(ax, *args, cbar=None, **kwargs):
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
    kwargs.setdefault('antialiased', False)
    obj = ax.plot_trisurf(*args, **kwargs)
    if cbar is not None:
        add_cbar(ax, obj=obj, **cbar)
    return obj

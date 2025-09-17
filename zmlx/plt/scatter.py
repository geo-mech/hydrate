from zmlx.plt.on_figure import add_axes3
from zmlx.ui import plot


def add_scatter3(ax, *args, cbar=None, **kwargs):
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


def scatter(
        items=None, get_val=None, x=None, y=None, z=None, c=None, get_pos=None, cb_label=None, **opts):
    """
    绘制三维的散点图
    """
    if x is None or y is None or z is None:
        if get_pos is None:
            def get_pos(item):
                return item.pos
        vpos = [get_pos(item) for item in items]
        x = [pos[0] for pos in vpos]
        y = [pos[1] for pos in vpos]
        z = [pos[2] for pos in vpos]
    if c is None:
        assert get_val is not None
        c = [get_val(item) for item in items]

    plot(add_axes3, add_scatter3, x, y, z, c=c,
         cbar=dict(label=cb_label), **opts)


def test_1():
    from zmlx.ui import plot
    from zmlx.plt.on_figure import add_axes3
    import numpy as np

    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    plot(add_axes3, add_scatter3, x, y, z, c=c,
         gui_mode=True, clear=True, caption='MyTest', title='My Scatter Plot', xlabel='x/m',
         cbar=dict(label='xxx'))


if __name__ == '__main__':
    test_1()

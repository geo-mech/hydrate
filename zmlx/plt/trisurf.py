from zmlx.plt.on_figure import add_axes3
from zmlx.ui import plot


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
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


def plot_trisurf(*args, **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置
    """
    plot(add_axes3, add_trisurf, *args, **kwargs)


def test_1():
    from zmlx.plt.data.surf import get_data
    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    plot_trisurf(x.flatten(), y.flatten(), z.flatten(),
                 gui_mode=True, cbar={}, cmap='viridis')


if __name__ == '__main__':
    test_1()

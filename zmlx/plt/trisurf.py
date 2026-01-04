from zmlx.plt.on_axes.trisurf import add_trisurf
from zmlx.plt.on_figure import add_axes3


def plot_trisurf(*args, **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置
    """
    from zmlx.ui import plot
    plot(add_axes3, add_trisurf, *args, **kwargs)


def test():
    from zmlx.data.surf import get_data
    from zmlx.plt.on_axes.data import trisurf
    from zmlx.plt.on_axes import plot3d
    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    obj = trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis')
    plot3d(obj, gui_mode=True)


def test2():
    from zmlx.data.surf import get_data
    from zmlx.plt.on_axes import plot3d
    from zmlx.plt.on_axes.data import trisurf

    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    plot3d(trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis'),
           xlabel='x', ylabel='y', zlabel='z', )


if __name__ == '__main__':
    test2()

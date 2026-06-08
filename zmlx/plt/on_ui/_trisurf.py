from zmlx.plt.on_axes import add_trisurf
from zmlx.plt.on_figure import plot_on_figure, add_axes3


def show_trisurf(*args, **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置
    """
    plot_on_figure(add_axes3, add_trisurf, *args, **kwargs)


def test():
    from zmlx.data.surf import get_data
    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    show_trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis')


if __name__ == '__main__':
    test()

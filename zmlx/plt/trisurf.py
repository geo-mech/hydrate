from zmlx.fig.plt_render.trisurf import add_trisurf
from zmlx.plt.on_figure import add_axes3


def plot_trisurf(*args, **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置
    """
    from zmlx.ui import plot
    plot(add_axes3, add_trisurf, *args, **kwargs)


def test():
    from zmlx.plt.data.surf import get_data
    from zmlx.fig import trisurf
    from zmlx.plt.on_axes import plot3d
    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))
    obj = trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis')
    plot3d(obj, gui_mode=True)


def test2():
    from zmlx.fig import plt_show, trisurf, axes3, tight_layout
    from zmlx.plt.data.surf import get_data

    x, y, z, _ = get_data(jx=40, jy=20, xr=(-5, 5), yr=(-3, 3))

    item = axes3(
        trisurf(x.flatten(), y.flatten(), z.flatten(), cbar={}, cmap='viridis'),
        xlabel='x', ylabel='y', zlabel='z',
    )
    plt_show(item, tight_layout(), gui_mode=True)


if __name__ == '__main__':
    test2()

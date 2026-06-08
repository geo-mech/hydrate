from zmlx.plt.on_axes import add_scatter
from zmlx.plt.on_figure import plot_on_axes


def show_scatter(*args, dim=3, **kwargs):
    """
    绘制散点图
    """
    plot_on_axes(add_scatter, *args, dim=dim, **kwargs)


def test():
    import numpy as np
    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    show_scatter(x, y, z, c=c, cbar=dict(label='label', title='title'), title='My Scatter Plot',
                 xlabel='x/m', gui_mode=True, clear=True, caption='MyTest')


if __name__ == '__main__':
    test()

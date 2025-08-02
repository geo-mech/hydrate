import zmlx.alg.sys as warnings

from zmlx.plt.fig3 import *

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test_1():
    from zmlx.ui import plot
    from zmlx.plt.on_figure import add_axes3
    from zmlx.plt.on_axes import scatter3
    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    plot(add_axes3, scatter3, x, y, z, c=c,
         gui_mode=True, clear=True, caption='MyTest', title='My Scatter Plot', xlabel='x/m',
         cbar=dict(label='xxx'))


if __name__ == '__main__':
    test_1()

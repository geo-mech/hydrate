import zmlx.alg.sys as warnings

from zmlx.plt.fig3 import *

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test_1():
    from zmlx.ui import plot
    from zmlx.plt.on_axes import add_subplot, scatter3
    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    plot(add_subplot, scatter3, x, y, z, c,
         gui_mode=True, clear=True, caption='MyTest', title='My Scatter Plot', xlabel='x/m', projection='3d')


if __name__ == '__main__':
    test_1()

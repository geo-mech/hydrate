import zmlx.alg.sys as warnings

from zmlx.plt.fig2 import plotxy

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test_1():
    try:
        import numpy as np
    except ImportError:
        np = None
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plotxy(x, y, title='sin(x)', xlabel='x', ylabel='y',
            caption='sin(x)', gui_mode=True)


if __name__ == '__main__':
    test_1()

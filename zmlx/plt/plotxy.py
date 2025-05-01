import warnings

from zmlx.plt.fig2 import plotxy

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




def test_1():
    import numpy as np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plotxy(x, y, title='sin(x)', xlabel='x', ylabel='y',
           caption='sin(x)', gui_mode=True)


if __name__ == '__main__':
    test_1()

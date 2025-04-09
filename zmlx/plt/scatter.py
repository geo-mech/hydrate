import zmlx.alg.sys as warnings

from zmlx.plt.fig3 import scatter

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test_1():
    try:
        import numpy as np
    except ImportError:
        np = None
    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    scatter(x=x, y=y, z=z, c=c, cb_label='value')


if __name__ == '__main__':
    test_1()

import zmlx.alg.sys as warnings

from zmlx.plt.fig2 import contourf

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test():
    try:
        import numpy as np
    except ImportError:
        np = None
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    contourf(x, y, z)


if __name__ == '__main__':
    test()

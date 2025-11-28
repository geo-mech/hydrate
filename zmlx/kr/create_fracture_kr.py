from zmlx.kr.base import create_fracture_kr

__all__ = ['create_fracture_kr']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    from zmlx.plt.fig2 import plot_xy

    x, y = create_fracture_kr()
    plot_xy(x, y)

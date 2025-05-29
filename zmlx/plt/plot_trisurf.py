import zmlx.alg.sys as warnings

from zmlx.plt.fig3 import plot_trisurf

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test_1():
    try:
        import numpy as np
    except ImportError:
        np = None
    # 生成 x 和 y 坐标
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)

    # 生成网格
    X, Y = np.meshgrid(x, y)

    # 生成 z 坐标
    Z = np.sin(np.sqrt(X ** 2 + Y ** 2))
    plot_trisurf(x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
                 gui_mode=True)


if __name__ == '__main__':
    test_1()

"""
二维的曲线
"""
import zmlx.alg.sys as warnings
from zmlx.plt.on_ui import show_xy as plot_xy

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


def plotxy(*args, **kwargs):
    import zmlx.alg.sys as warnings
    warnings.warn(
        "plotxy is deprecated, please use plot_xy instead",
        DeprecationWarning,
        stacklevel=2)
    plot_xy(*args, **kwargs)


def test():
    import numpy as np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plot_xy(x, y, title='sin(x)', xlabel='x', ylabel='y',
            caption='sin(x)', gui_mode=True)


if __name__ == '__main__':
    test()

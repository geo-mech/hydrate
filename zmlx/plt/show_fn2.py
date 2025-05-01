"""
定义数据格式 fn2，主要包括4列数据，用于定义裂缝位置，1列数据，用于定义裂缝的宽度，
1列数据，用于定义裂缝的颜色（如压力）
"""
import warnings

from zmlx.plt.fig2 import show_fn2

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def test():
    from zmlx.data.example_fn2 import pos, w, c
    show_fn2(pos, w, c, w_max=3, clabel='Pressure [Pa]', gui_mode=True)


if __name__ == '__main__':
    test()

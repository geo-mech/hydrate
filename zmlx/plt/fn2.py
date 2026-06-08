"""
定义数据格式 fn2，主要包括4列数据，用于定义裂缝位置，1列数据，用于定义裂缝的宽度，
1列数据，用于定义裂缝的颜色（如压力）
"""

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)
from zmlx.plt.on_ui import show_fn2


def test():
    from zmlx.data.example_fn2 import pos, w, c
    show_fn2(pos, w, c, w_max=3, clabel='Pressure', ctitle='Pa')


if __name__ == '__main__':
    test()

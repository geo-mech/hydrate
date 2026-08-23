"""show fn2 绘图工具。

Modified by Claude, 2026-08-12
"""
import zmlx.alg.sys as warnings

from zmlx.plt.on_ui import show_fn2

_keep = [show_fn2]
warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)

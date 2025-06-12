import zmlx.alg.sys as warnings

from zmlx.plt.curve2 import plotxy

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)

_keep = [plotxy]

from zmlx.io.load_txt import load_txt as loadtxt

__all__ = ['loadtxt']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

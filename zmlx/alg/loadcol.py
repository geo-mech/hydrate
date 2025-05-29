from zmlx.io.load_col import load_col as loadcol

__all__ = ['loadcol']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

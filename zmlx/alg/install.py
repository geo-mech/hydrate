from zmlx.alg.sys import add_pth_file as install

__all__ = ['install']

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

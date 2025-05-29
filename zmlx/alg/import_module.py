from zmlx.alg.sys import import_module

__all__ = ['import_module']

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

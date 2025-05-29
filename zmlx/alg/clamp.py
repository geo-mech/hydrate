from zmlx.alg.base import clamp

__all__ = ['clamp']

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} will be removed after 2026-4-16, please '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)

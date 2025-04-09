from zmlx.alg.base import year_to_seconds

__all__ = ['year_to_seconds']

import zmlx.alg.sys as warnings

warnings.warn(f'The {__name__} will be removed after 2026-4-17',
              DeprecationWarning, stacklevel=2)

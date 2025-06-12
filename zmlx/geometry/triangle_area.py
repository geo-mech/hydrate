from zmlx.geometry.triangle import get_area as triangle_area

__all__ = ['triangle_area', ]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

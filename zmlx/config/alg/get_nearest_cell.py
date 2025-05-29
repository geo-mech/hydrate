import zmlx.alg.sys as warnings

from zmlx.base.has_cells import get_nearest_cell

warnings.warn(
    'This module is deprecated (will be removed after 2026-4-9), use zmlx.base.nearest_cell instead',
    DeprecationWarning, stacklevel=2)

__all__ = [
    "get_nearest_cell",
]

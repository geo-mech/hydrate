from zmlx.geometry.base import \
    seg_point_distance as get_seg_point_distance

__all__ = ['get_seg_point_distance']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

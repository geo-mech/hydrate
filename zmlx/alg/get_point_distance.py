import zmlx.alg.sys as warnings

from zmlx.geometry.base import point_distance as get_point_distance

__all__ = ['get_point_distance']

warnings.warn('The modulus get_point_distance is deprecated '
              '(will be removed after 2026-4-9), '
              'please use zmlx.geometry.point_distance instead.',
              DeprecationWarning, stacklevel=2)

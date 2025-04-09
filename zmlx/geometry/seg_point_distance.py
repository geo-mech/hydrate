from zmlx.geometry.base import seg_point_distance

__all__ = ['seg_point_distance']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    p1 = (0, 0, 0)
    p2 = (1, 0, 0)
    p3 = (2, 0, 0)
    print(seg_point_distance((p1, p2), p3))

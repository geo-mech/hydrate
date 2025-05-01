from zmlx.geometry.utils import seg_intersection
__all__ = ['seg_intersection', ]

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

def test():
    """
    测试
    """
    ax, ay, bx, by = 0, 0, 1, 1
    cx, cy, dx, dy = 0, 1, 1, 0
    print(seg_intersection(ax, ay, bx, by, cx, cy, dx, dy))

    ax, ay, bx, by = 0, 0, 1, 0
    cx, cy, dx, dy = 0, 0, 0, 1
    print(seg_intersection(ax, ay, bx, by, cx, cy, dx, dy))


if __name__ == '__main__':
    test()

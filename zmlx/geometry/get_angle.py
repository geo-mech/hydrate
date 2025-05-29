from zmlx.geometry.base import get_angle

__all__ = ['get_angle']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)




def test():
    from zml import Array2
    import random
    for i in range(100):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        a1 = get_angle(x, y)
        a2 = Array2(x, y).get_angle()
        print(x, y, a1, a2)


if __name__ == '__main__':
    test()

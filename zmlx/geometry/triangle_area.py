from zmlx.geometry.base import triangle_area

__all__ = ['triangle_area', ]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    print(triangle_area(3, 4, 5))

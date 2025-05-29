from numpy.linalg import norm as get_norm

__all__ = ['get_norm']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    print(get_norm([3, 4]))

import zmlx.alg.sys as warnings

from zmlx.alg.base import make_index

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    print(make_index(1))
    print(make_index((1, 2)))

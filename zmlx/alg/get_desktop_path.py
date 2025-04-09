import zmlx.alg.sys as warnings

from zmlx.alg.os import get_desktop_path

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    print(get_desktop_path('x', 'y'))

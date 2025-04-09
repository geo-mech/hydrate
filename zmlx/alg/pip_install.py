import zmlx.alg.sys as warnings

from zmlx.alg.sys import pip_install

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    pip_install('numpy')

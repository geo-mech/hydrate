import zmlx.alg.sys as warnings

from zmlx.alg.sys import get_pythonw_path

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    print(get_pythonw_path())

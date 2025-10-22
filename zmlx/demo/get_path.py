import zmlx.alg.sys as warnings

warnings.warn(
    f'The {__name__} is deprecated, please use the "path.py" in the '
    f'same folder instead. This file will be removed after 2026-4-15',
    DeprecationWarning, stacklevel=2)

from zmlx.demo.path import get_path

if __name__ == "__main__":
    print(get_path())

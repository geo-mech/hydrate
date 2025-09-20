import zmlx.alg.sys as warnings

from zmlx.alg.fsys import count_lines

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    from zmlx.exts.base import get_dir

    count_lines(path=get_dir())

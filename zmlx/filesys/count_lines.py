from zmlx.alg.fsys import count_lines

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



if __name__ == '__main__':
    from zml import get_dir

    count_lines(path=get_dir())

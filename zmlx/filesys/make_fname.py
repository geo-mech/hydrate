from zmlx.alg.fsys import make_fname
__all__ = ['make_fname']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


if __name__ == '__main__':
    print(make_fname(1, '.', '.txt'))
    print(make_fname(1, '.', 'txt'))

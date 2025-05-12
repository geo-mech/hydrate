from zmlx.alg.fsys import join_paths

__all__ = ['join_paths']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    print(join_paths('x', 'y'))
    print(join_paths('x', 'y', None))

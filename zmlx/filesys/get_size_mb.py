from zmlx.alg.fsys import get_size_mb

__all__ = ['get_size_mb']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    print(get_size_mb(path='.'))

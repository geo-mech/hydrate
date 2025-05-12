from zmlx.alg.fsys import get_latest_file

__all__ = [
    'get_latest_file'
]

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    import os

    print(get_latest_file(os.path.dirname(__file__)))

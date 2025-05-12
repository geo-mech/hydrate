from zmlx.io.utils import get_text_back

__all__ = ['get_text_back']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    print(get_text_back(__file__, max_length=200))

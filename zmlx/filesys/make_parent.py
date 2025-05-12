from zml import make_parent

__all__ = ['make_parent']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

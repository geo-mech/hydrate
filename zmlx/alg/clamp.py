from zmlx.alg.utils import clamp

__all__ = ['clamp']

import warnings

warnings.warn(f'The modulus {__name__} will be removed after 2026-4-16, please '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

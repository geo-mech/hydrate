from zmlx.fluid.alg import from_data

__all__ = [
    "from_data",
]

import warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please use '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

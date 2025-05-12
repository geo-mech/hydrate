from zmlx.alg.utils import year_to_seconds

__all__ = ['year_to_seconds']

import warnings

warnings.warn(f'The {__name__} will be removed after 2026-4-17',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

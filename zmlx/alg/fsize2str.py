from zmlx.alg.utils import fsize2str

__all__ = ['fsize2str']

import warnings

warnings.warn(f'{__file__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

from zmlx.alg.utils import *

__all__ = [
'mass2str', 'time2str', 'fsize2str'
]

import warnings

warnings.warn(f'{__name__} will be removed after 2026-5-8', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

from zmlx.alg.multi_proc import apply_async, create_async

__all__ = [
    "apply_async",
    "create_async",
]

import warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

from zmlx.alg.multi_proc import apply_async, create_async

__all__ = [
    "apply_async",
    "create_async",
]

import zmlx.alg.sys as warnings

warnings.warn(
    f'{__name__} will be removed after 2026-4-15, please import from zmlx instead',
    DeprecationWarning,
    stacklevel=2)

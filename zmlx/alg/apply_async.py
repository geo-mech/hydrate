"""已弃用的模块，请改用 zmlx.alg.multi_proc.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.multi_proc import apply_async, create_async

__all__ = [
    "apply_async",
    "create_async",
]


warn(
    f'{__name__} will be removed after 2026-4-15, please import from zmlx instead',
    DeprecationWarning,
    stacklevel=2)

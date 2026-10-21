"""已弃用的模块，请改用 zmlx.seepage_mesh.edit.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.seepage_mesh.edit import swap_yz, swap_xy, swap_xz

__all__ = [
    'swap_yz',
    'swap_xy',
    'swap_xz'
]


warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.edit) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

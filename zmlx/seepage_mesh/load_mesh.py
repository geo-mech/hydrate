"""已弃用的模块，请改用 zmlx.seepage_mesh.io.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.seepage_mesh.io import load_mesh

__all__ = [
    'load_mesh'
]


warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.io) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

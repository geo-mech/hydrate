"""已弃用的模块，请改用 zmlx.mesh.triangle.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.mesh.triangle import layered_triangles

__all__ = [
    'layered_triangles'
]


warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

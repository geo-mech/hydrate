"""已弃用的模块，请改用 zmlx.alg.around_seg.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.alg.around_seg import get_faces_around_seg, get_face_ids_around_seg

__all__ = ['get_faces_around_seg', 'get_face_ids_around_seg']

warn('The modulus get_faces_around_seg is deprecated '
              'will be removed after 2026-4-9), '
              'please use zmlx.base.around_seg instead.',
              DeprecationWarning, stacklevel=2)

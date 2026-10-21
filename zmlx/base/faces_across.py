"""已弃用的模块，请改用 zmlx.algs.faces_across.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.faces_across import *

_keep = [get_faces_across]


warn(f'{__name__} will be removed after 2027-5-17', DeprecationWarning, stacklevel=2)

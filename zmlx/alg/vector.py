"""已弃用的模块，请改用 zmlx.alg.vec.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

from zmlx.alg.vec import *

_keep = [read_numpy, write_numpy, to_numpy]

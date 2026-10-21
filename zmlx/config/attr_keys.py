"""已弃用的模块，请改用 zmlx.tfc.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.tfc import *

_keep = [DynKeys]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

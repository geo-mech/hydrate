"""已弃用的模块，请改用 zmlx.scen.frac.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.scen.frac import *

_keep = [get_fn2]


warn(f'{__name__} will be removed after 2027-5-17', DeprecationWarning, stacklevel=2)

"""已弃用的模块，请改用 zmlx.scen.icp.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.scen.icp import *

_keep = [create_fludefs]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

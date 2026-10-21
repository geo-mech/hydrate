"""已弃用的模块，请改用 zmlx.tfc.config.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.tfc.config import *

_keep = [TherFlowConfig, SeepageTher]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

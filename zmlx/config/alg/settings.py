"""已弃用的模块，请改用 zmlx.tfc.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.tfc import get_configs as get, put_configs as put, add_config as add

_keep = [get, put, add]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

"""已弃用的模块，请改用 zmlx.scen.hydrate.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.scen.hydrate import *

_keep = [create_caps, create_fludefs, create_opts]


def create(*args, **kwargs):
    """
    在旧的版本中，create函数用于创建配置对象。已废弃。
    """
    warn(
        "The function create() will be removed in future version", DeprecationWarning, stacklevel=2)
    return Config(*args, **kwargs)



warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

"""
定义处于测试阶段的方法.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg._slowdown import get_velocity_after_slowdown_by_viscosity

_keep = [
    get_velocity_after_slowdown_by_viscosity,
]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

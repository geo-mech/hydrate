"""
定义处于测试阶段的方法
"""
from zmlx.alg._slowdown import get_velocity_after_slowdown_by_viscosity

_keep = [
    get_velocity_after_slowdown_by_viscosity,
]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

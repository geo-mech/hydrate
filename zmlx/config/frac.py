"""
裂缝相关的算法
"""

from zmlx.scen.frac import get_fn2

__all__ = [
    "get_fn2"
]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

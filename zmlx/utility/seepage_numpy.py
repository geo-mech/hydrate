"""已弃用的模块，重定向到 zmlx.tfc（提供 SeepageNumpy 与 as_numpy）.

Modified by Claude, 2026-08-12
"""

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-5-2',
              DeprecationWarning, stacklevel=2)

from zmlx.tfc import SeepageNumpy, as_numpy

__all__ = ['SeepageNumpy', 'as_numpy']

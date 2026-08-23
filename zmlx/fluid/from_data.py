"""已弃用的模块，请改用 zmlx.fluid.alg."""
from zmlx.fluid.alg import from_data

__all__ = [
    "from_data",
]

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please use '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)

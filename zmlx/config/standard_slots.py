from zmlx.config.slots import standard_slots

__all__ = [
    "standard_slots"
]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

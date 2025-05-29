from zmlx.alg.base import mean

__all__ = ['mean']

import zmlx.alg.sys as warnings

warnings.warn(
    f'The {__name__} will be removed after 2026-4-17, please import from zmlx instead.',
    DeprecationWarning, stacklevel=2)

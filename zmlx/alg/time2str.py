from zmlx.alg.base import time2str

__all__ = ['time2str']

import zmlx.alg.sys as warnings

warnings.warn(
    f'{__name__} will be removed after 2026-4-15, please from zmlx import timestr instead. ',
    DeprecationWarning,
    stacklevel=2)

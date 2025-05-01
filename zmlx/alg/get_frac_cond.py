from zmlx.alg.frac import get_frac_cond, g_1cm

__all__ = ['get_frac_cond', 'g_1cm']

import warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



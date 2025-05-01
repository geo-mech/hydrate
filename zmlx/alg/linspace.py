from zmlx.alg.utils import linspace

__all__ = ['linspace']

import warnings

warnings.warn(
    f'The {__name__} will be removed after 2026-4-17, please import from zmlx instead.',
    DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



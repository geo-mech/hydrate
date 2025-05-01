import warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


from zmlx.utility.heat_injector import *

__all__ = ['HeatInjector']

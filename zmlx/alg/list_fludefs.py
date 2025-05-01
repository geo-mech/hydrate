import warnings

from zmlx.base.seepage import list_fludefs

__all__ = [
    'list_fludefs'
]

warnings.warn('The zmlx.alg.list_fludefs module is deprecated, '
              'please use zmlx.base.seepage instead.',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



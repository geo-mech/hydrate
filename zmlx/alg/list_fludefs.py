import zmlx.alg.sys as warnings

from zmlx.base.seepage import list_fludefs

__all__ = [
    'list_fludefs'
]

warnings.warn('The zmlx.alg.list_fludefs module is deprecated, '
              'please use zmlx.base.seepage instead.',
              DeprecationWarning, stacklevel=2)

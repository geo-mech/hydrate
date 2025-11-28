from zmlx.base.zml import make_dirs, makedirs

__all__ = ['make_dirs', 'makedirs']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

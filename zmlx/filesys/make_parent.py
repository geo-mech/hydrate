from zmlx.base.zml import make_parent

__all__ = ['make_parent']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15, import make_parent from "zml" instead',
              DeprecationWarning, stacklevel=2)

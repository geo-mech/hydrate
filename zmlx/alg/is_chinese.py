import zmlx.alg.sys as warnings

from zml import is_chinese

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

__all__ = ['is_chinese']

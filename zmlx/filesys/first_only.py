import zmlx.alg.sys as warnings

from zmlx.alg.fsys import first_only

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

__all__ = ['first_only']

from zmlx.react.alg import add_reaction

__all__ = [
    'add_reaction'
]

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)

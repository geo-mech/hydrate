from zmlx.react.alg import create_reaction

__all__ = [
    'create_reaction'
]

import zmlx.alg.sys as warnings

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please use '
              f'"from zmlx import create_reaction" instead',
              DeprecationWarning, stacklevel=2)

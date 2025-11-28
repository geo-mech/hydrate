from zmlx.seepage_mesh.wellbore import create_wellbore

__all__ = [
    'create_wellbore'
]

import zmlx.alg.sys as warnings

warnings.warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.wellbore) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

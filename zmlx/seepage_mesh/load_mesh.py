from zmlx.seepage_mesh.io import load_mesh

__all__ = [
    'load_mesh'
]

import zmlx.alg.sys as warnings

warnings.warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.io) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)



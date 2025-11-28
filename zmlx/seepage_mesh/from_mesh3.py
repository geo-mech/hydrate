from zmlx.seepage_mesh.mesh3 import face_centered

__all__ = [
    'face_centered'
]

import zmlx.alg.sys as warnings

warnings.warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.mesh3) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

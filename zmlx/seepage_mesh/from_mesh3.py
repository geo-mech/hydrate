from zmlx.seepage_mesh.mesh3 import face_centered
__all__ = [
    'face_centered'
]

import warnings

warnings.warn(f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.mesh3) and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


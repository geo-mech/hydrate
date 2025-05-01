from zmlx.seepage_mesh.triangle import split_triangles, create

__all__ = [
    'split_triangles',
   'create'
]

import warnings

warnings.warn(f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.triangle) and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


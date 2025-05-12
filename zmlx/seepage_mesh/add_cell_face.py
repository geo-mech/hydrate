from zmlx.seepage_mesh.edit import add_cell_face

__all__ = [
    'add_cell_face'
]

import warnings

warnings.warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.edit) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

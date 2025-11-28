from zmlx.seepage_mesh.edit import swap_yz, swap_xy, swap_xz

__all__ = [
    'swap_yz',
    'swap_xy',
    'swap_xz'
]

import zmlx.alg.sys as warnings

warnings.warn(
    f'The modulus {__name__} is deprecated (use zmlx.seepage_mesh.edit) and '
    f'will be removed after 2026-4-16',
    DeprecationWarning, stacklevel=2)

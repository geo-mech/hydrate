from zmlx.mesh.io import load_trimesh

__all__ = [
    'load_trimesh'
]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

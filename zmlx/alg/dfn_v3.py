from zmlx.geometry.dfn_v3 import *

__all__ = ['from_segs', 'create_fractures', 'remove_small', 'create_links',
           'save_c14',
           'to_rc3', 'create_demo']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

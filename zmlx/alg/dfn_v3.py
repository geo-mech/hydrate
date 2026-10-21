"""已弃用的模块，请改用 zmlx.geometries.dfn_v3.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.geometries.dfn_v3 import *

__all__ = ['from_segs', 'create_fractures', 'remove_small', 'create_links',
           'save_c14',
           'to_rc3', 'create_demo']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

import warnings

from zmlx.exts.vector import *

warnings.warn("zmlx.geometry.Vector is deprecated "
              "(will be removed after 2026-4-4), "
              "please use zmlx.exts.vector instead",
              DeprecationWarning)

__all__ = ['read_numpy', 'write_numpy', 'to_numpy']

import warnings

from zmlx.base.vector import *

warnings.warn("zmlx.geometry.Vector is deprecated "
              "(will be removed after 2026-4-4), "
              "please use zmlx.base.vector instead",
              DeprecationWarning, stacklevel=2)

__all__ = ['read_numpy', 'write_numpy', 'to_numpy']

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

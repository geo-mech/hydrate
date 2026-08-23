"""已弃用的模块，请改用 zmlx.tfc._vis."""
from zmlx.tfc._vis import *

_keep = [adjust]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

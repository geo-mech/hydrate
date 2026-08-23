"""已弃用的模块，请改用 zmlx.tfc._solid."""
from zmlx.tfc._solid import *

_keep = [backup]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

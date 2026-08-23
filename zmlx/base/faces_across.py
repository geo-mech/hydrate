"""已弃用的模块，请改用 zmlx.alg.faces_across."""
from zmlx.alg.faces_across import *

_keep = [get_faces_across]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-17', DeprecationWarning, stacklevel=2)

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

from zmlx.alg.vec import *

_keep = [read_numpy, write_numpy, to_numpy]

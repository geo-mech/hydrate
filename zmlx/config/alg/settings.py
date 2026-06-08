from zmlx.tfc import get_configs as get, put_configs as put, add_config as add

_keep = [get, put, add]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

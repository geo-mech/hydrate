"""已弃用的模块，请改用 zmlx.tfc.config."""
from zmlx.tfc.config import *

_keep = [TherFlowConfig, SeepageTher]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

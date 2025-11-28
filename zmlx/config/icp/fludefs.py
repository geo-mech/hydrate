from zmlx.config.icp._fluid import create_fludefs

_keep = [create_fludefs]

import zmlx.alg.sys as warnings

warnings.warn(
    f'{__name__} will be removed after 2026-12-9',
    DeprecationWarning,
    stacklevel=2)

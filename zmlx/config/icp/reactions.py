from zmlx.config.icp._react import create_reactions

_keep = [create_reactions]

import zmlx.alg.sys as warnings

warnings.warn(
    f'{__name__} will be removed after 2026-12-9',
    DeprecationWarning,
    stacklevel=2)

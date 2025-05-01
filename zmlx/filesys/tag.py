from zmlx.alg.fsys import *
__all__ = ['print_tag', 'time_string', 'is_time_string', 'has_tag']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

from zmlx.alg.multi_thread import *

__all__ = [
    'create_task',
    'exec_task',
    'exec_task_and_set_res',
    'apply_threads'
]

import warnings

warnings.warn(f'{__file__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

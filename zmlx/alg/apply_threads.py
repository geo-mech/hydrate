"""已弃用的模块，请改用 zmlx.alg.multi_thread.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.multi_thread import *

__all__ = [
    'create_task',
    'exec_task',
    'exec_task_and_set_res',
    'apply_threads'
]


warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

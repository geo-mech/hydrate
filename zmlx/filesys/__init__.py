"""
文件系统相关的操作

注意：
    本模块处于deprecated的状态，将在未来的版本中移除。

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
from zmlx.algs.fsys import *

__keep = [print_tag]
warn(f'The <zmlx.filesys> will be removed after 2026-4-15, please use zmlx.algs.fsys instead',
              DeprecationWarning, stacklevel=2)

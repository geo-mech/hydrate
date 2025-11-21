"""
文件系统相关的操作

注意：
    本模块处于deprecated的状态，将在未来的版本中移除。
"""

import zmlx.alg.sys as warnings
from zmlx.alg.fsys import *

__keep = [print_tag]
warnings.warn(f'The <zmlx.filesys> will be removed after 2026-4-15, please use zmlx.alg.fsys instead',
              DeprecationWarning, stacklevel=2)

"""已弃用的模块，请改用 zmlx.kr.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.kr.base import *

_ = [create_kr]


warn(f'The module {__name__} will be removed after 2026-5-17',
              DeprecationWarning, stacklevel=2)

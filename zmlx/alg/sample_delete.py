"""已弃用的模块，请改用 zmlx.alg.os.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import os


from zmlx.alg.os import sample_delete

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    sample_delete(os.getcwd(), count_keep=100)

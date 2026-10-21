"""已弃用的模块，请改用 zmlx.alg.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.alg.base import rand_dir3

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    for i in range(30):
        print(rand_dir3())

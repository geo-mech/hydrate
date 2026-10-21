"""已弃用的模块，请改用 zmlx.algs.sys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import time


from zmlx.algs.sys import timing_show

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def test():
    timing_show('test1', time.sleep, 1)
    timing_show('test2', time.sleep, 2)


if __name__ == '__main__':
    test()

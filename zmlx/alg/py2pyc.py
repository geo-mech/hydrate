"""已弃用的模块，请改用 zmlx.alg.sys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import sys


from zmlx.alg.sys import py2pyc

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        py2pyc(ipath=sys.argv[1], opath=sys.argv[2])

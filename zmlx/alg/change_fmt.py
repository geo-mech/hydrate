"""已弃用的模块，请改用 zmlx.tfc.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import sys


from zmlx.tfc import seepage2txt, txt2seepage

warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        key = sys.argv[1]
        path = None
        if len(sys.argv) >= 3:
            path = sys.argv[2]
        if key == 'seepage2txt':
            seepage2txt(path)

        if key == 'txt2seepage':
            txt2seepage(path)

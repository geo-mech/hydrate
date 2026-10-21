"""已弃用的模块，请改用 zmlx.algs.fsys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.fsys import get_latest_file

__all__ = [
    'get_latest_file'
]


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    import os

    print(get_latest_file(os.path.dirname(__file__)))

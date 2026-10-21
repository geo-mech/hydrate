"""已弃用的模块，请改用 zmlx.algs.fsys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.fsys import make_fname

__all__ = ['make_fname']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(make_fname(1, '.', '.txt'))
    print(make_fname(1, '.', 'txt'))

"""已弃用的模块，请改用 zmlx.algs.fsys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.fsys import join_paths

__all__ = ['join_paths']


warn(f'The module {__name__} will be removed after 2026-4-15, please import from "zmlx.algs.fsys" instead',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(join_paths('x', 'y'))
    print(join_paths('x', 'y', None))

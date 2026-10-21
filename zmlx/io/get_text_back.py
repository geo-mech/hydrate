"""已弃用的模块，请改用 zmlx.io.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.io.base import get_text_back

__all__ = ['get_text_back']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(get_text_back(__file__, max_length=200))

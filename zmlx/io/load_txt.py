"""已弃用的模块，请改用 zmlx.io.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.io.base import load_txt

__all__ = [
    'load_txt'
]


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


def test():
    from io import StringIO
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_txt(StringIO(text)))


if __name__ == '__main__':
    test()

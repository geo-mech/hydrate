"""已弃用的模块，请改用 zmlx.algs.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.algs.base import divide_list

warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


def test1():
    # 示例用法
    original_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n = 3
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


def test2():
    # 示例用法
    original_list = []
    n = 3
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


def test3():
    # 示例用法
    original_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n = 20
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


if __name__ == '__main__':
    test3()

"""已弃用的模块，请改用 zmlx.algs.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.algs.base import join_rows
from zmlx.exts import np

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def test():
    assert np is not None
    a = np.array([[1, 2], [3, 4]])
    b = np.array([[5, 6]])

    combined_matrix = join_rows(a, b)
    print(combined_matrix)


if __name__ == '__main__':
    test()

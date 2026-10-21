"""已弃用的模块，请改用 zmlx.data.path.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import os


from zmlx.algs.fsys import join_paths
from zmlx.exts import make_parent

warn(
    f'The {__name__} is deprecated, please use the "path.py" in the same folder instead. '
    f'This file will be removed after 2026-4-15',
    DeprecationWarning, stacklevel=2)


def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))


if __name__ == "__main__":
    print(get_path())

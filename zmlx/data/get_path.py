import os
import zmlx.alg.sys as warnings

from zmlx.base.zml import make_parent
from zmlx.alg.fsys import join_paths

warnings.warn(
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

import os

from zmlx.exts.base import make_parent
from zmlx.alg.fsys import join_paths


def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))


if __name__ == "__main__":
    print(get_path())

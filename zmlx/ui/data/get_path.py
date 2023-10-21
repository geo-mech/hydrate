import os

from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_parent import make_parent


def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))


if __name__ == "__main__":
    print(get_path())

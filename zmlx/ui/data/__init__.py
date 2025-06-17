import os

from zml import make_parent
from zmlx.alg.fsys import join_paths


def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))

from icp_xz.opath import opath as get_opath
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_parent import make_parent


def opath(*args):
    """
    返回输出的目录
    """
    return make_parent(join_paths(get_opath('steam-v3'), *args))

import os

from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_dirs import make_dirs
from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.tag import print_tag
from zmlx.io.path import get_path


class TaskFolder:
    """
    当前任务的文件夹
    """

    def __init__(self, *names, **kwargs):
        # 找到数据目录
        self.folder = get_path(*names, **kwargs)

        # 创建目录
        if not os.path.isdir(self.folder):
            make_dirs(self.folder)

        # 创建时间标签
        print_tag(self.folder)

    def __call__(self, *args):
        """
        返回文件路径，并确保上一级目录的存在
        """
        if len(args) > 0:
            return make_parent(join_paths(self.folder, *args))
        else:
            return self.folder

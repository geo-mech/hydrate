"""
todo:
    此模块后续可能需要转移到io中，因为和文件的输入输出更加接近
    @20230726
"""

import os

from zml import app_data, get_dir
from zmlx.alg.is_chinese import is_chinese
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_dirs import make_dirs
from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.tag import print_tag


def opath(*args, tag=None):
    """
    返回一个用于输出的文件路径. 如果给定的args为空，则返回root路径（由 current_work_directory 定义的环境变量或者当前工作路径）
    等同于UI界面设置的工作目录.

    当tag给定的时候，将检查主目录下是否存在给定tag的文件 (从而确保对文件夹进行误操作).
    """

    # 当data文件夹存在的时候，则会优先使用 (有的时候，可能没有创建环境变量的权限)
    data_folder = os.path.join(get_dir(), 'data')
    if not os.path.isdir(data_folder):
        data_folder = os.getcwd()

    # 读取环境变量
    root = app_data.getenv('current_work_directory',
                           encoding='utf-8',
                           default=data_folder)
    assert not is_chinese(root), f'String contains Chinese. root: {root}'

    # 检查根目录是否存在需要的tag
    if tag is not None:
        fname = os.path.join(root, tag)
        assert os.path.isfile(fname), f'The required tag file not exists: {fname}'

    # 找到所需要的路径
    if len(args) > 0:
        for arg in args:
            assert not is_chinese(arg), f'String contains Chinese. args = {args}'
        path = join_paths(root, *args)
    else:
        path = root

    # 因为是输出目录，因此创建必要的文件夹.
    return make_parent(path)


def get(*args, **kwargs):
    """
    获得输出目录＜等同于UI界面设置的工作目录＞
    """
    return opath(*args, **kwargs)


def set(folder=None):
    """
    设置输出目录＜等同于UI界面设置的工作目录＞
    """
    if folder is None:
        return

    assert not is_chinese(folder), f'Error: folder contains Chinese. folder = {folder}'
    if not os.path.isdir(folder):
        make_dirs(folder)

    if os.path.isdir(folder):
        app_data.setenv('current_work_directory', folder, encoding='utf-8')


class TaskFolder:
    """
    当前任务的文件夹
    """

    def __init__(self, *names, **kwargs):
        # 找到数据目录
        self.folder = opath(*names, **kwargs)

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


if __name__ == '__main__':
    print(opath())
    print(opath('x'))

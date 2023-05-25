# -*- coding: utf-8 -*-


from zml import *
from zmlx.alg.join_paths import join_paths
from zmlx.alg.is_chinese import is_chinese
import os


def opath(*args):
    """
    返回一个用于输出的文件路径. 如果给定的args为空，则返回root路径（由 current_work_directory 定义的环境变量或者当前工作路径）
    等同于UI界面设置的工作目录
    """
    root = app_data.getenv('current_work_directory', encoding='utf-8', default=os.getcwd())
    assert not is_chinese(root), f'String contains Chinese. root: {root}'

    if len(args) > 0:
        for arg in args:
            assert not is_chinese(arg), f'String contains Chinese. args = {args}'
        path = join_paths(root, *args)
    else:
        path = root

    return make_parent(path)


def get(*args):
    """
    获得输出目录＜等同于UI界面设置的工作目录＞
    """
    return opath(*args)


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
    def __init__(self, *names):
        # 找到数据目录
        self.folder = opath(*names)

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

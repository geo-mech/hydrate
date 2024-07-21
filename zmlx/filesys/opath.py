"""
todo:
    此模块后续可能需要转移到io中，因为和文件的输入输出更加接近
    @20230726
"""

import os
import warnings

from zml import app_data, get_dir
from zmlx.alg.is_chinese import is_chinese
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_dirs import make_dirs
from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.tag import print_tag
from zmlx.filesys.in_directory import in_directory


def opath(*args, tag=None):
    """
    返回一个用于输出的文件路径. 如果给定的args为空，则返回root路径（由 current_work_directory 定义的环境变量或者当前工作路径）
    等同于UI界面设置的工作目录.

    当tag给定的时候，将检查主目录下是否存在给定tag的文件 (从而确保对文件夹进行误操作).

    注意，当任何错误发生的时候，此函数返回None. (应用程序可以继续执行). Since 24-5-20
    """

    # 当data文件夹存在的时候，则会优先使用 (有的时候，可能没有创建环境变量的权限)
    data_folder = os.path.join(get_dir(), 'data')
    if not os.path.isdir(data_folder):
        data_folder = os.getcwd()

    # 读取环境变量
    root = app_data.getenv('current_work_directory',
                           encoding='utf-8',
                           default=data_folder)

    if root is None:
        warnings.warn('The root is None')
        return

    if is_chinese(root):
        warnings.warn(f'The root contains Chinese. root = {root}')
        return

    # 检查根目录是否存在需要的tag
    if tag is not None:
        fname = os.path.join(root, tag)
        if not os.path.isfile(fname):
            warnings.warn(f'The required tag file not exists: {fname}')
            return

    # 找到所需要的路径
    if len(args) > 0:
        for arg in args:
            if is_chinese(arg):
                warnings.warn(f'String contains Chinese. args = {args}')
                return
        path = join_paths(root, *args)
    else:
        path = root

    # 因为是输出目录，因此创建必要的文件夹.
    if not in_directory(path, get_dir()):   # 确保不在脚本目录内输出.
        return make_parent(path)


# 两个别名
get = opath
get_opath = opath


def set_opath(folder=None, tag=None):
    """
    设置输出目录＜等同于UI界面设置的工作目录＞
    """
    if folder is None:
        warnings.warn('The given folder is None')
        return

    # 转化为绝对路径，这很重要
    folder = os.path.abspath(folder)

    assert not is_chinese(folder), f'Error: folder contains Chinese. folder = {folder}'

    # 不可以在脚本目录下输出
    assert not in_directory(folder, get_dir()), f'Error: try to export data to code folder: {get_dir()}'

    # 尝试创建目录
    if not os.path.isdir(folder):
        make_dirs(folder)

    if os.path.isdir(folder):   # 只有目录存在的时候才执行
        if tag is not None:
            # 当给定tag的时候，需要确保这个目录是一个空目录，
            # 或者此tag已经存在，防止数据被覆盖
            assert isinstance(tag, str), 'The tag should be string'
            f_name = os.path.join(folder, tag)
            if not os.path.exists(f_name):
                assert len(os.listdir(folder)) == 0, 'The folder is NOT empty'
                with open(f_name, 'w') as file:
                    # 写入文件
                    file.write('tag')

        # 修改工作目录
        app_data.setenv('current_work_directory',
                        folder,  # 这里，写入绝对路径
                        encoding='utf-8')

        # 显示消息
        print(f'Succeed set data path to: "{folder}" ')


def set(*args, **kwargs):
    """
    设置输出目录
    """
    warnings.warn('Use set_opath instead. '
                  'This function will be remove after 2025-5-21',
                  DeprecationWarning)
    set_opath(*args, **kwargs)


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

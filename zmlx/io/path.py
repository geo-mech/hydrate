import os
import zmlx.alg.sys as warnings

from zml import app_data, get_dir, is_chinese, make_parent, make_dirs
from zmlx.alg.fsys import in_directory, join_paths


def get_path(*args, tag=None, key=None):
    """
    返回一个用于输出的文件路径. 如果给定的args为空，则返回root路径（由 key 定义的环境变量或者当前工作路径）
    等同于UI界面设置的工作目录.

    当tag给定的时候，将检查主目录下是否存在给定tag的文件 (从而确保对文件夹进行误操作).

    注意，当任何错误发生的时候，此函数返回None. (应用程序可以继续执行). Since 24-5-20
    """

    if key is None:
        # 当data文件夹存在的时候，则会优先使用 (有的时候，可能没有创建环境变量的权限)
        data_folder = os.path.join(get_dir(), 'data')
        if not os.path.isdir(data_folder):
            data_folder = os.getcwd()
        key = 'current_work_directory'
        # 读取环境变量
        root = app_data.getenv(key, encoding='utf-8', default=data_folder)
    else:
        # 读取环境变量
        root = app_data.getenv(key, encoding='utf-8')

    if root is None:
        # warnings.warn(f'The root is None. (key={key})')
        return None

    if is_chinese(root):
        warnings.warn(f'The root contains Chinese. key={key}, root = {root}')
        return None

    # 检查根目录是否存在需要的tag
    if tag is not None:
        f_name = os.path.join(root, tag)
        if not os.path.isfile(f_name):
            warnings.warn(f'The required tag file not exists: {f_name}')
            return None

    # 找到所需要的路径
    if len(args) > 0:
        for arg in args:
            if is_chinese(arg):
                warnings.warn(f'String contains Chinese. args = {args}')
                return None
        path = join_paths(root, *args)
    else:
        path = root

    # 因为是输出目录，因此创建必要的文件夹.
    if not in_directory(path, os.path.join(get_dir(), 'zmlx')):  # 确保不在脚本目录内输出.
        return make_parent(path)
    return None


def set_path(folder=None, tag=None, key=None):
    """
    设置输出目录＜等同于UI界面设置的工作目录＞
    """
    if folder is None:
        warnings.warn('The given folder is None')
        return

    # 转化为绝对路径，这很重要
    folder = os.path.abspath(folder)

    assert not is_chinese(
        folder), f'Error: folder contains Chinese. folder = {folder}'

    # 尝试创建目录
    if not os.path.isdir(folder):
        make_dirs(folder)

    if os.path.isdir(folder):  # 只有目录存在的时候才执行
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

        if key is None:
            key = 'current_work_directory'

        # 修改工作目录
        app_data.setenv(key,
                        folder,  # 这里，写入绝对路径
                        encoding='utf-8')

        # 显示消息
        print(f'Succeed set data path (key = {key}) to: "{folder}" ')


if __name__ == '__main__':
    print(get_path())
    print(get_path('x'))
    print(get_path('y', key='Test'))

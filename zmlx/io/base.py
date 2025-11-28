import os
from io import StringIO

import zmlx.alg.sys as warnings
from zmlx.base.zml import make_dirs, make_parent, np


def load_txt(*args, **kwargs):
    """
    将文本读取到list (非numpy数组)。返回值类型的不同，是这个函数和 numpy.loadtxt唯一的不同.
    """
    return np.loadtxt(*args, **kwargs).tolist()


def load_col(fname=None, index=0, dtype=float, text=None):
    """
    从给定的数据文件导入一列数据。 其中index为列的编号. 和 numpy.loadtxt的主要不同，在于参数名称略有不同，另外返回值的类型不同.
    """
    if text is not None:
        fname = StringIO(text)
    assert fname is not None
    return load_txt(fname, dtype=dtype, usecols=index)


def append_file(filename, text, encoding=None):
    """
    在给定文件的末尾附加文本
    Args:
        filename: 文件名（当为None的时候则不执行操作）
        text: 要附加的文本或者其它可以通过file来write的数据
        encoding: 编码格式
    return:
        None
    """
    try:
        if filename is not None:
            with open(make_parent(filename), 'a', encoding=encoding) as file:
                file.write(text)
    except Exception as err:
        warnings.warn(
            f'meet exception in append_file. filename={filename}. error={err}')


def get_text_back(filename, max_length=None):
    try:
        # 添加errors参数处理解码问题
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            if max_length is None:
                return file.read()

            file.seek(0, 2)
            file_size = file.tell()
            start_pos = max(0, file_size - max_length)
            file.seek(start_pos)
            return file.read()[-max_length:]

    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None


class TaskFolder:
    """
    当前任务的文件夹
    """

    def __init__(self, *names, **kwargs):
        from zmlx.io.path import get_path
        from zmlx.alg.fsys import print_tag
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
        from zmlx.alg.fsys import join_paths
        if len(args) > 0:
            return make_parent(join_paths(self.folder, *args))
        else:
            return self.folder

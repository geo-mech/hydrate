from zmlx.plt.on_axes.data import *
from zmlx.plt.on_figure.data import *

_keep = [subplot, surface]


def save(fname, data):
    """
    将数据存入Json文件
    Args:
        fname: 文件名，字符串形式
        data: 要存入的数据，任意类型

    Returns:

    """
    from zmlx.io import json_ex
    json_ex.write(fname, data)


def load(fname):
    """
    从Json文件导入数据
    Args:
        fname: Json文件的路径

    Returns:
        包含从Json文件中导入的数据
    """
    from zmlx.io import json_ex
    return json_ex.read(fname)

"""
定义数据驱动的绘图模式
"""
from zmlx.plt.on_axes.data import *
from zmlx.plt.on_figure.data import *
from zmlx.plt.on_figure.data import show as plt_show

_keep = [add_to_axes, add_to_figure, show, plt_show, subplot, surface
         ]


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


from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())

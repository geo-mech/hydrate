"""
定义数据驱动的绘图模式
"""

# 作用在Axes上的项目
from zmlx.fig._on_ax import *

# 作用在Figure上的项目
from zmlx.fig._on_fig import *

# 基于matplotlib的绘图函数
from zmlx.fig._plt import show, show as plt_show, plot2d, plot3d, add_to_figure, add_to_axes


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

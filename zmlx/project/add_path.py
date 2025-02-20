import sys
import os


def add_path():
    """
    将当前文件所在的文件夹添加到 Python 的搜索路径中。在运行定义在 project文件夹中的
    文件的时候，最好先add_path，这样就可以导入project文件夹中的其他文件了。
    """
    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 将当前目录添加到 sys.path 中
    if current_dir not in sys.path:
        sys.path.append(current_dir)

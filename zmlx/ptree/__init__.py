"""
属性树，以及利用属性树对一些数据类型进行初始化。此模块主要用于辅助建模。
"""

from zmlx.exts import SelfPath
from zmlx.ptree.ptree import open_pt, PTree

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())

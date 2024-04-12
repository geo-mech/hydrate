"""
在project中，定义具体的项目。因此这个project文件夹，本质上并非一个package.
"""

import os
import sys


def add_path():
    """
    将project文件夹添加到sys的path，方便后续位于project中的项目被import使用;
    """
    folder = os.path.abspath(os.path.dirname(__file__))
    if folder not in sys.path:
        sys.path.append(folder)
        print(f'Succeed add path: {folder}')

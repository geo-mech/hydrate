# -*- coding: utf-8 -*-
"""
zmlx: zml模块的扩展，将首先引入zml的所有功能，并定义数据和扩展功能。

说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；

    2. 用户可添加文件，但勿修改现有文件内容；
"""

from zml import *
from zmlx.alg import get_latest_version, clamp, opath, linspace, \
    has_PyQt5, has_numpy, has_matplotlib, join_paths
import os

# 部分函数容易混淆，借助zml调用
import zml
do_plot = zml.plot

try:
    from zmlx.config import create_hydrate as create_hydconfig
except:
    pass

try:
    from zmlx.plt import plot2
except:
    pass

try:
    from zmlx.ui import tricontourf, plotxy, find, find_all
    has_gui = True
except:
    has_gui = False

try:
    from zmlx.utility import GuiIterator
except:
    pass

try:
    from zmlx.utility import LinearField
except:
    pass

try:
    from zmlx.utility import PressureController
except:
    pass

try:
    from zmlx.utility import SaveManager
except:
    pass

try:
    from zmlx.utility import SeepageCellMonitor
except:
    pass

try:
    import numpy as np
except:
    np = None

try:
    folder = os.path.dirname(__file__)
    app_data.add_path(folder)
    app_data.add_path(os.path.join(folder, 'data'))
    if has_gui:
        app_data.add_path(os.path.join(folder, 'ui', 'data'))
except:
    pass


def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))


def open_gui():
    def do_install():
        try:
            install(name='zml.pth',
                    folder=os.path.dirname(os.path.dirname(__file__)))
        except Exception as e:
            print(f'Error: {e}')

    gui.execute(do_install, keep_cwd=False, close_after_done=False)


if __name__ == "__main__":
    open_gui()

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
import warnings

# 部分函数容易混淆，借助zml调用
import zml
do_plot = zml.plot

try:
    from zmlx.config import create_hydrate as create_hydconfig
except Exception as err:
    warnings.warn(f'meet exception when import create_hydconfig. error = {err}')

try:
    from zmlx.plt import plot2
except Exception as err:
    warnings.warn(f'meet exception when import plot2. error = {err}')


try:
    from zmlx.plt.tricontourf import tricontourf
except Exception as err:
    warnings.warn(f'meet exception when import tricontourf. error = {err}')

try:
    from zmlx.plt.plotxy import plotxy
except Exception as err:
    warnings.warn(f'meet exception when import plotxy. error = {err}')

try:
    from zmlx.ui import find, find_all
    has_gui = True
except Exception as err:
    has_gui = False
    warnings.warn(f'meet exception when import find, find_all. error = {err}')

try:
    from zmlx.utility import GuiIterator
except Exception as err:
    warnings.warn(f'meet exception when import GuiIterator. error = {err}')

try:
    from zmlx.utility import LinearField
except Exception as err:
    warnings.warn(f'meet exception when import LinearField. error = {err}')

try:
    from zmlx.utility import PressureController
except Exception as err:
    warnings.warn(f'meet exception when import PressureController. error = {err}')

try:
    from zmlx.utility import SaveManager
except Exception as err:
    warnings.warn(f'meet exception when import SaveManager. error = {err}')

try:
    from zmlx.utility import SeepageCellMonitor
except Exception as err:
    warnings.warn(f'meet exception when import SeepageCellMonitor. error = {err}')

try:
    import numpy as np
except Exception as err:
    np = None
    warnings.warn(f'meet exception when import numpy. error = {err}')

try:
    __folder = os.path.dirname(__file__)
    app_data.add_path(__folder)
    app_data.add_path(os.path.join(__folder, 'data'))
    if has_gui:
        app_data.add_path(os.path.join(__folder, 'ui', 'data'))
except Exception as err:
    warnings.warn(f'meet exception when add path to app_data. error = {err}')


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

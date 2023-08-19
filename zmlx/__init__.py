# -*- coding: utf-8 -*-
"""
zmlx: zml模块的扩展，将首先引入zml的所有功能，并定义数据和扩展功能。

说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；

    2. 用户可添加文件，但勿修改现有文件内容；
"""

from zml import *
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.opath import opath
from zmlx.alg.sys import get_latest_version
from zmlx.alg.clamp import clamp
from zmlx.alg.linspace import linspace
from zmlx.alg.has_module import has_numpy, has_PyQt5, has_matplotlib
from zmlx.alg.make_fname import make_fname
import os
import warnings

# 部分函数容易混淆，借助zml调用
import zml

do_plot = zml.plot

setenv = app_data.setenv
getenv = app_data.getenv

try:
    from zmlx.fluid.ch4 import create as create_ch4
    from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
    from zmlx.fluid.co2 import create as create_co2
    from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
    from zmlx.fluid.h2o import create as create_h2o
    from zmlx.fluid.h2o_gas import create as create_h2o_gas
    from zmlx.fluid.h2o_ice import create as create_h2o_ice
except Exception as err:
    warnings.warn(f'meet exception when import fluid. error = {err}')


try:
    from zmlx.config.hydrate import create as create_hydconfig
except Exception as err:
    warnings.warn(f'meet exception when import create_hydconfig. error = {err}')

try:
    from zmlx.plt.plot2 import plot2
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
    from zmlx.ui.Config import find, find_all
except Exception as err:
    warnings.warn(f'meet exception when import find, find_all. error = {err}')

try:
    from zmlx.utility.GuiIterator import GuiIterator
except Exception as err:
    warnings.warn(f'meet exception when import GuiIterator. error = {err}')

try:
    from zmlx.utility.LinearField import LinearField
except Exception as err:
    warnings.warn(f'meet exception when import LinearField. error = {err}')

try:
    from zmlx.utility.PressureController import PressureController
except Exception as err:
    warnings.warn(f'meet exception when import PressureController. error = {err}')

try:
    from zmlx.utility.SaveManager import SaveManager
except Exception as err:
    warnings.warn(f'meet exception when import SaveManager. error = {err}')

try:
    from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor
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

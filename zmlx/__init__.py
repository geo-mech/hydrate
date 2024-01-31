"""
zmlx: zml模块的扩展，将首先引入zml的所有功能，并定义数据和扩展功能。

说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；

    2. 用户可添加文件，但勿修改现有文件内容；
"""

from zml import *

try:
    from zmlx.ui.GuiBuffer import gui, information, question, plot as do_plot, break_point, gui_exec
except Exception as err:
    warnings.warn(f'meet exception when import GuiBuffer. error = {err}')

# 下面这几个，主要用来覆盖zml中的定义
from zmlx.alg.time2str import time2str
from zmlx.alg.mass2str import mass2str
from zmlx.utility.Field import Field
from zmlx.utility.AttrKeys import AttrKeys, add_keys
from zmlx.config.TherFlowConfig import TherFlowConfig, SeepageTher
from zmlx.filesys.first_only import first_only
from zmlx.filesys.tag import print_tag

from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.opath import opath
from zmlx.filesys.make_fname import make_fname
from zmlx.alg.sys import get_latest_version
from zmlx.alg.clamp import clamp
from zmlx.alg.linspace import linspace
from zmlx.alg.has_module import has_numpy, has_PyQt5, has_matplotlib

# 使得import的时候，尽可能不去执行复杂的操作
from zmlx.utility.RuntimeFunc import RuntimeFunc
import os
import warnings
import zml

setenv = app_data.setenv
getenv = app_data.getenv

create_ch4 = RuntimeFunc(pack_name='zmlx.fluid.ch4', func_name='create')
create_ch4_hydrate = RuntimeFunc(pack_name='zmlx.fluid.ch4_hydrate', func_name='create')
create_co2 = RuntimeFunc(pack_name='zmlx.fluid.co2', func_name='create')
create_co2_hydrate = RuntimeFunc(pack_name='zmlx.fluid.co2_hydrate', func_name='create')
create_h2o = RuntimeFunc(pack_name='zmlx.fluid.h2o', func_name='create')
create_h2o_gas = RuntimeFunc(pack_name='zmlx.fluid.h2o_gas', func_name='create')
create_h2o_ice = RuntimeFunc(pack_name='zmlx.fluid.h2o_ice', func_name='create')

create_hydconfig = RuntimeFunc(pack_name='zmlx.config.hydrate', func_name='create',
                               deprecated_name='zmlx.create_hydconfig', deprecated_date='2025-5-7')

plot2 = RuntimeFunc(pack_name='zmlx.plt.plot2', func_name='plot2')
tricontourf = RuntimeFunc(pack_name='zmlx.plt.tricontourf', func_name='tricontourf')
plotxy = RuntimeFunc(pack_name='zmlx.plt.plotxy', func_name='plotxy')
find = RuntimeFunc(pack_name='zmlx.ui.Config', func_name='find')
find_all = RuntimeFunc(pack_name='zmlx.ui.Config', func_name='find_all')

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
            from zmlx.alg.install import install
            install(name='zml.pth',
                    folder=os.path.dirname(os.path.dirname(__file__))
                    )
        except Exception as e:
            print(f'Error: {e}')

        try:
            gui.trigger('readme.py')
        except Exception as e:
            print(f'Error: {e}')

    gui.execute(do_install, keep_cwd=False, close_after_done=False)


if __name__ == "__main__":
    open_gui()

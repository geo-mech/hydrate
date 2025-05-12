"""
zmlx: zml模块的扩展，将首先引入zml的所有功能，并定义数据和扩展功能。

说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；
    2. 用户可添加文件，但勿修改现有文件内容；
"""

########################################
# zml中的内容
from zml import *

if is_chinese(get_dir()):
    warnings.warn('Please make sure to install zml in a pure English path, '
                  'otherwise it may cause unpredictable errors.')

setenv = app_data.setenv
getenv = app_data.getenv

try:
    __folder = os.path.dirname(__file__)
    app_data.add_path(__folder)
    app_data.add_path(os.path.join(__folder, 'data'))
    app_data.add_path(os.path.join(__folder, 'ui', 'data'))
except Exception as err:
    warnings.warn(f'meet exception when add path to app_data. error = {err}')

########################################
# alg
# from zmlx.alg.has_module import has_numpy, has_matplotlib # Remove since 2025-4-18
# from zmlx.alg.sys import get_latest_version  # Remove since 2025-4-30
from zmlx.alg.utils import clamp, linspace, time2str, mass2str, fsize2str
from zmlx.alg.multi_proc import create_async, apply_async
from zmlx.alg.sbatch import sbatch
from zmlx.alg.fsys import first_only, print_tag, join_paths, make_fname
from zmlx.alg import fsys, fsys as path

########################################
# base
from zmlx.base import ip, has_cells
from zmlx.base.has_cells import get_cell_mask
from zmlx.base.has_cells import get_pos_range

########################################
# config
from zmlx.config import (seepage, seepage as seepage_config, hydrate,
                         step_iteration, adjust_vis, icp, timer as timer_config,
                         sand as sand_config)
from zmlx.config.TherFlowConfig import TherFlowConfig, SeepageTher
from zmlx.config import capillary

########################################
# data
from zmlx.data.mesh_c10000 import \
    get_face_centered_seepage_mesh as create_c10000

########################################
# demo

########################################
# kit

########################################
# exts

########################################
# fem

########################################
# filesys


########################################
# fluid
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.fluid import h2o
from zmlx.fluid.alg import from_data, from_file

########################################
# geometry
from zmlx.geometry import dfn2, dfn_v3, rect_3d, rect_v3
from zmlx.geometry.utils import (get_angle, get_center, get_seg_angle,
                                 seg_intersection, triangle_area,
                                 point_distance, seg_point_distance,
                                 get_norm)

########################################
# io
from zmlx.io.path import get_path as opath

########################################
# kr
from zmlx.kr.pre_defines import create_kr
from zmlx.kr.pre_defines import create_krf

########################################
# mesh

########################################
# pg

########################################
# plt
from zmlx.plt.on_figure import plot_on_figure
from zmlx.plt.on_axes import plot_on_axes
from zmlx.plt.fig2 import (plotxy, show_dfn2, show_field2, show_fn2,
                           tricontourf, trimesh, contourf, plot2)
from zmlx.plt.fig3 import plot_trisurf, scatter, show_rc3

########################################
# ptree

########################################
# react
from zmlx.react.alg import create_reaction, add_reaction
from zmlx.react.inh import create_inh, add_inh

########################################
# seepage_mesh
from zmlx.seepage_mesh.cube import (create_cube as create_cube_seepage_mesh,
                                    create_cube, create_xz, create_xyz)
from zmlx.seepage_mesh.cylinder import create_cylinder
from zmlx.seepage_mesh.edit import scale as seepage_mesh_rescale
from zmlx.seepage_mesh.edit import (swap_yz, swap_xy, swap_xz,
                                    swap_yz as seepage_mesh_swap_yz,
                                    swap_xy as seepage_mesh_swap_xy,
                                    swap_xz as seepage_mesh_swap_xz)
from zmlx.seepage_mesh.edit import add_cell_face

########################################
# ui
from zmlx.ui import (gui, information, question,
                     plot as do_plot, plot, break_point, gui_exec)
from zmlx.ui.main import open_gui

########################################
# utility
from zmlx.utility.fields import Field, LinearField
from zmlx.utility.attr_keys import AttrKeys, add_keys
from zmlx.utility.runtime_fn import RuntimeFunc
from zmlx.base.seepage import as_numpy
from zmlx.utility.gui_iterator import GuiIterator
from zmlx.utility.pressure_controller import PressureController
from zmlx.utility.save_manager import SaveManager
from zmlx.utility.seepage_cell_monitor import SeepageCellMonitor
from zmlx.utility.capillary_effect import CapillaryEffect


########################################
# 其它
def get_path(*args):
    """
    返回数据目录
    """
    return make_parent(join_paths(os.path.dirname(__file__), *args))


import zml

__unused = [zml]

########################################
# deprecated
create_hydconfig = RuntimeFunc(pack_name='zmlx.config.hydrate',
                               func_name='create',
                               deprecated_name='zmlx.create_hydconfig',
                               deprecated_date='2025-5-7')
find = RuntimeFunc(pack_name='zmlx.ui.Config',
                   func_name='find')
find_all = RuntimeFunc(pack_name='zmlx.ui.Config',
                       func_name='find_all')

if __name__ == "__main__":
    try:
        open_gui(sys.argv)
    except:
        print(about())

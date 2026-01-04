"""
说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；
    2. 用户可添加文件，但勿修改现有文件内容；
"""
# 单独导入zml
import zmlx.exts as zml

########################################
# 导入zml中的内容
from zmlx.exts import *


def get_dir() -> str:
    """获取当前执行文件所在目录的绝对路径。

    Returns:
        str: 当前文件所在目录的完整路径

    Note:
        - 等价于 os.path.dirname(os.path.realpath(__file__))
        - 常用于动态加载库时的路径定位
        - 结果不包含末尾路径分隔符
    """
    return os.path.dirname(os.path.realpath(__file__))


if contain_chinese(get_dir()):
    warnings.warn('Please make sure to install zmlx in a pure English path, '
                  'otherwise it may cause unpredictable errors.')

setenv = app_data.setenv
getenv = app_data.getenv

try:
    __folder = os.path.dirname(__file__)
    if isinstance(__folder, str):
        app_data.add_path(__folder)
        app_data.add_path(os.path.join(__folder, 'data'))
        app_data.add_path(os.path.join(__folder, 'ui', 'data'))
except Exception as err:
    warnings.warn(f'meet exception when add path to app_data. error = {err}')

########################################
# alg
from zmlx.alg import (
    create_async, apply_async, sbatch, first_only, print_tag, join_paths, make_fname, clamp, linspace,
    time2str, mass2str, fsize2str, fsys, fsys as path, ip
)

########################################
# tfc
from zmlx.tfc import (
    seepage, seepage as seepage_config, adjust_vis, capillary, diffusion, sand as sand_config, step_iteration,
    timer as timer_config, as_numpy, SeepageNumpy
)
from zmlx.tfc.config import TherFlowConfig, SeepageTher  # 弃用的

########################################
# data
from zmlx.data import create_c10000, load_igg

########################################
# fluid
from zmlx.fluid import (
    create_ch4, create_ch4_hydrate, create_co2, create_co2_hydrate,
    create_h2o, create_h2o_gas, create_h2o_ice, h2o,
    ch4, from_data, from_file, load_fludefs
)

########################################
# geometry
from zmlx.geometry import (
    get_angle, get_center, get_seg_angle, seg_intersection, triangle_area,
    point_distance, seg_point_distance, get_norm, dfn2, dfn_v3, rect_3d, rect_v3
)

########################################
# io
from zmlx.io import opath, json_ex

########################################
# kr
from zmlx.kr import create_kr, create_krf

########################################
# plt
from zmlx.plt import (
    plot_on_figure, add_axes2, add_axes3, add_subplot,
    add_tricontourf, add_contourf, add_surf, add_cbar, add_curve, add_curve2, curve, add_legend,
    plot_on_axes, add_items, item, plot2d, plot3d,
    plot_xy, plotxy, show_dfn2, show_field2, show_fn2,
    tricontourf, trimesh, contourf, plot2,
    plot_trisurf, scatter, show_rc3
)

########################################
# react
from zmlx.react import load_reactions, create_reaction, add_reaction, create_inh, add_inh

########################################
# scen
from zmlx.scen import hydrate, icp

########################################
# seepage_mesh
from zmlx.seepage_mesh import (
    create_cube_seepage_mesh,
    create_cube, create_xz, create_xyz, create_cylinder,
    seepage_mesh_rescale, swap_yz, swap_xy, swap_xz,
    seepage_mesh_swap_yz, seepage_mesh_swap_xy, seepage_mesh_swap_xz, add_cell_face
)

########################################
# ui
from zmlx.ui import (
    gui, information, question,
    plot as do_plot, plot, break_point, gui_exec,
    open_gui, open_gui_without_setup
)

########################################
# utility
from zmlx.utility import (
    load_field3, Field, LinearField, AttrKeys, add_keys, RuntimeFunc, GuiIterator, PressureController, SaveManager,
    SeepageCellMonitor, CapillaryEffect
)

########################################
# 其它
get_path = SelfPath(__file__)

########################################
# deprecated
create_hydconfig = RuntimeFunc(
    pack_name='zmlx.config.hydrate',
    func_name='create',
    deprecated_name='zmlx.create_hydconfig',
    deprecated_date='2025-5-7')
find = RuntimeFunc(
    pack_name='zmlx.ui.Config',
    func_name='find')
find_all = RuntimeFunc(
    pack_name='zmlx.ui.Config',
    func_name='find_all')

if __name__ == "__main__":
    try:
        open_gui(sys.argv)
    except:
        print(about())

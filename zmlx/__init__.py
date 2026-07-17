"""
说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；
    2. 用户可添加文件，但勿修改现有文件内容；
"""
# 导入其它的内容，兼容之前的代码
import timeit

# 单独导入zml
import zmlx.exts as zml
########################################
# 导入zmlx.exts中的内容
from zmlx.exts import *

_keep = [timeit]


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
# system
from zmlx.system import (
    is_headless
)

########################################
# alg
from zmlx.alg import (
    create_async, apply_async, sbatch, first_only, print_tag, join_paths, make_fname, clamp, linspace,
    time2str, mass2str, fsize2str, fsys, fsys as path
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
    ch4, from_data, from_file, load_fludefs, create_aqueous
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
    add_tricontourf, add_contourf, add_surf, add_cbar, add_curve, add_curve2, curve, add_legend, add_scatter, add_fn2,
    add_dfn2, add_trisurf, add_seepage_mesh,

    plot_on_figure, plot_on_axes, add_subplot, add_axes2, add_axes3, add_axes_img, AutoLayout as AutoFigLayout,
    AutoLayout, calculate_subplot_layout, calc_best_layout,

    show_xy, show_dfn2, show_field2, show_fn2, show_rc3, show_scatter, show_trisurf, show_trimesh, show_contourf,
    show_tricontourf,

    tricontourf, trimesh, contourf, plot_trisurf, plot_xy, plotxy,
)

########################################
# fig
from zmlx.fig import add_to_figure, add_to_axes, plot2d, plot3d, add_to_axes as add_items, item
import zmlx.fig as fig

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


def _env(*args):
    """
    基于pip安装zmlx的依赖项. 包括numpy, scipy, matplotlib, pyqtgraph, PyOpenGL6,
     PyQt6, PyQt6-WebEngine, pyqt6-qscintilla, PyOpenGL,
     dulwich, pillow, pyvista, pyvistaqt, vtk, pandas, openpyxl 等
    """
    from zmlx.alg import install_dep
    install_dep()


def _demo(*args):
    """
    打开界面并显示demo，在这个界面，可以尝试打开demo代码或者直接运行demo代码
    """
    from zmlx.ui import gui
    def f():
        gui.show_demo()

    gui.execute(f, close_after_done=False)


def _ui(*args):
    """
    打开gui界面.
    """
    from zmlx.ui.gui_buffer import open_gui, open_gui_without_setup
    if len(args) < 2:
        open_gui()
    else:
        open_gui_without_setup(args)


def _ver(*args):
    """
    显示zmlx的版本信息
    """
    from zmlx.exts import about
    print(about())


class _CommandRegistry:
    """
    命令注册器：管理命令行子命令的注册、查找和执行。

    使用方式：
        cmds = _CommandRegistry()

        # 方式1：装饰器注册（推荐）
        @cmds.register('ui', desc='打开gui界面')
        def _ui(args):
            ...

        # 方式2：字典式注册（兼容旧方式）
        cmds['ui'] = _ui

        # 方式3：批量注册
        cmds.register_all(env=_env, ui=_ui)
    """

    def __init__(self):
        self._commands = {}

    def register(self, name, *, desc=None, usage=None):
        """
        装饰器：注册一个命令。

        参数:
            name: 命令名称（命令行中使用）
            desc: 命令的简短描述（用于帮助信息）
            usage: 用法说明（可选，如 'ui [--safe]'）
        """

        def decorator(func):
            self._commands[name] = {
                'func': func,
                'desc': desc or (func.__doc__ or '').strip().split('\n')[0],
                'usage': usage or name,
            }
            return func

        return decorator

    def register_all(self, **kwargs):
        """
        批量注册命令。每个关键字参数为 命令名=函数。

        示例:
            cmds.register_all(env=_env, ui=_ui)
        """
        for name, func in kwargs.items():
            self[name] = func

    def __setitem__(self, name, func):
        """支持 cmds['name'] = func 的字典式注册（兼容旧方式）"""
        self._commands[name] = {
            'func': func,
            'desc': (func.__doc__ or '').strip().split('\n')[0] if func.__doc__ else '',
            'usage': name,
        }

    def __getitem__(self, name):
        return self._commands[name]['func']

    def __contains__(self, name):
        return name in self._commands

    def get(self, name):
        """获取命令函数，不存在返回 None"""
        entry = self._commands.get(name)
        return entry['func'] if entry else None

    def items(self):
        """迭代 (名称, 函数) 对（兼容旧代码的 for cmd, f in cmds.items()）"""
        for name, entry in self._commands.items():
            yield name, entry['func']

    def keys(self):
        return self._commands.keys()

    def get_desc(self, name):
        """获取命令描述"""
        entry = self._commands.get(name)
        return entry['desc'] if entry else ''

    def get_usage(self, name):
        """获取命令用法"""
        entry = self._commands.get(name)
        return entry['usage'] if entry else name

    def help(self, name=None):
        """
        打印帮助信息。
        - 不指定 name：列出所有可用命令
        - 指定 name：显示该命令的详细帮助
        """
        if name:
            entry = self._commands.get(name)
            if entry:
                func = entry['func']
                doc = (func.__doc__ or '').strip()
                print(f"命令: {name}")
                print(f"用法: python -m zmlx {entry['usage']}")
                if doc:
                    print(f"\n{doc}")
            else:
                print(f"未知命令: {name}")
                print(f"使用 'python -m zmlx help' 查看可用命令。")
        else:
            print("IGG-Hydrate (zmlx) 命令行工具")
            print(f"用法: python -m zmlx <命令> [参数...]\n")
            print("可用命令:")
            max_len = max(len(n) for n in self._commands.keys()) if self._commands else 0
            for cmd_name, entry in sorted(self._commands.items()):
                print(f"  {cmd_name:<{max_len + 2}}{entry['desc']}")
            print(f"\n使用 'python -m zmlx help <命令>' 查看命令详情。")

    def execute(self, argv):
        """
        解析命令行参数并执行对应命令。

        参数:
            argv: 命令行参数列表，如 ['zmlx', 'ui', '--safe']
        """
        if len(argv) < 2:
            self.help()
            return

        key = argv[1]

        # 处理 help 命令或 --help/-h 标志
        if key in ('help', '--help', '-h'):
            if len(argv) > 2 and argv[2] not in ('--help', '-h'):
                self.help(name=argv[2])
            else:
                self.help()
            return

        entry = self._commands.get(key)
        if entry is None:
            print(f"未知命令: {key}")
            print(f"使用 'python -m zmlx help' 查看可用命令。")
            return

        # 检查子命令是否请求帮助
        args = argv[2:]  # 不再包含命令名本身
        if args and args[0] in ('--help', '-h'):
            self.help(name=key)
            return

        # 执行命令
        entry['func'](args)


# 创建全局命令注册器
_cmds = _CommandRegistry()

# 注册命令（兼容旧的 _cmds 字典接口）
_cmds['env'] = _env
_cmds['ui'] = _ui
_cmds['demo'] = _demo
_cmds['ver'] = _ver


def main(argv):
    """
    命令行入口。支持的命令:
        env  - 安装依赖
        ui   - 打开GUI界面
        demo - 打开Demo浏览器
        ver  - 显示版本信息
        help - 显示帮助
    """
    _cmds.execute(argv)


if __name__ == "__main__":
    main(sys.argv)

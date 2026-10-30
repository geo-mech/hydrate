"""
说明：
    1. 优先从zmlx中import，只有当zmlx中没有定义，再考虑从次一级文件夹import；
    2. 用户可添加文件，但勿修改现有文件内容；

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

# 版本号：必须与 pyproject.toml 中的 version 保持一致（提交时同步更新，见 AGENTS.md）
__version__ = "1.9.7"


def version_at_least(version):
    """判断当前 ``zmlx`` 的版本是否**不低于** ``version``。

    典型用法 —— 只在需要新版本才有的功能时才走那条分支::

        from zmlx import version_at_least

        if version_at_least('1.10'):
            ...     # 1.10 及以上

    Args:
        version (str): 要比较的版本号字符串，如 ``'1.10'``、``'1.9.5'``。

    Returns:
        bool: 当前版本 >= ``version`` 时为 True（**相等也算 True**）。

    Raises:
        ValueError: ``version`` 不是字符串，或解析不出版本号。

    Note:
        - 比较按**数字**逐段进行：``'1.10'`` 比 ``'1.9'`` 新。
          ⚠️ 不要用字符串直接比 —— ``'1.10' > '1.9'`` 是 **False**（逐字符比，
          ``'9' > '1'``），这正是本函数存在的理由。
        - 缺的段补 0，所以 ``'1.9'`` 等价于 ``'1.9.0'``。
        - ``zmlx`` 的版本号固定是 ``x.y.z`` 三段纯数字，不含 ``rc`` / ``dev``
          后缀，故这里不做 PEP 440 的完整解析。
    """
    if not isinstance(version, str):
        raise TypeError(f"version must be a str, got {type(version).__name__}")

    def _parse(text):
        parts = []
        for piece in text.strip().split("."):
            digits = "".join(ch for ch in piece if ch.isdigit())
            parts.append(int(digits) if len(digits) > 0 else 0)
        if all(p == 0 for p in parts):
            raise ValueError(f"cannot parse version from {text!r}")
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])

    return _parse(__version__) >= _parse(version)


# 导入其它的内容，兼容之前的代码
import timeit

# 单独导入zml
import zmlx.exts as zml

########################################
# 导入zmlx.exts中的内容
from zmlx.exts import *
from zmlx.system import warn

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
    warn(
        "Please make sure to install zmlx in a pure English path, "
        "otherwise it may cause unpredictable errors."
    )

setenv = app_data.setenv
getenv = app_data.getenv

try:
    __folder = os.path.dirname(__file__)
    if isinstance(__folder, str):
        app_data.add_path(__folder)
        app_data.add_path(os.path.join(__folder, "data"))
        app_data.add_path(os.path.join(__folder, "ui", "data"))
except Exception as err:
    warn(f"meet exception when add path to app_data. error = {err}")

########################################
# system
from zmlx import fig

########################################
# alg
from zmlx.algs import (
    apply_async,
    clamp,
    create_async,
    first_only,
    fsize2str,
    fsys,
    get_last_file,
    has_tag,
    is_time_string,
    join_paths,
    linspace,
    make_fname,
    make_fpath,
    mass2str,
    pip_install,
    prepare_dir,
    print_tag,
    sbatch,
    time2str,
    time_string,
)
from zmlx.algs import fsys as path
from zmlx.algs import pip_install as install

########################################
# data
from zmlx.data import create_c10000, load_igg

########################################
# fig
from zmlx.fig import add_to_axes, add_to_figure, item, plot2d, plot3d
from zmlx.fig import add_to_axes as add_items

########################################
# fluids
from zmlx.fluids import (
    ch4,
    create_aqueous,
    create_ch4,
    create_ch4_hydrate,
    create_co2,
    create_co2_hydrate,
    create_h2o,
    create_h2o_gas,
    create_h2o_ice,
    from_data,
    from_file,
    h2o,
    load_fludefs,
)

########################################
# geometries
from zmlx.geometries import (
    dfn2,
    dfn_v3,
    get_angle,
    get_center,
    get_norm,
    get_seg_angle,
    point_distance,
    rect_3d,
    rect_v3,
    seg_intersection,
    seg_point_distance,
    triangle_area,
)

########################################
# io
from zmlx.io import json_ex, opath, read_py, write_py

########################################
# kr
from zmlx.krs import create_kr, create_krf

########################################
# plt
from zmlx.plt import (
    AutoLayout,
    add_axes2,
    add_axes3,
    add_axes_img,
    add_cbar,
    add_contourf,
    add_curve,
    add_curve2,
    add_dfn2,
    add_fn2,
    add_legend,
    add_scatter,
    add_seepage_mesh,
    add_subplot,
    add_surf,
    add_tricontourf,
    add_trisurf,
    calc_best_layout,
    calculate_subplot_layout,
    contourf,
    curve,
    plot_on_axes,
    plot_on_figure,
    plot_trisurf,
    plot_xy,
    plotxy,
    show_contourf,
    show_dfn2,
    show_field2,
    show_fn2,
    show_rc3,
    show_scatter,
    show_tricontourf,
    show_trimesh,
    show_trisurf,
    show_xy,
    tricontourf,
    trimesh,
)
from zmlx.plt import (
    AutoLayout as AutoFigLayout,
)

########################################
# react
from zmlx.reactions import (
    add_inh,
    add_reaction,
    create_inh,
    create_reaction,
    load_reactions,
)

########################################
# scen
from zmlx.scen import hydrate, icp

########################################
# seepage_mesh
from zmlx.seepage_meshes import (
    add_cell_face,
    create_cube,
    create_cube_seepage_mesh,
    create_cylinder,
    create_xyz,
    create_xz,
    seepage_mesh_rescale,
    seepage_mesh_swap_xy,
    seepage_mesh_swap_xz,
    seepage_mesh_swap_yz,
    swap_xy,
    swap_xz,
    swap_yz,
)
from zmlx.system import is_headless

########################################
# tfc
from zmlx.tfc import (
    SeepageNumpy,
    adjust_vis,
    as_numpy,
    capillary,
    diffusion,
    seepage,
    step_iteration,
)
from zmlx.tfc import sand as sand_config
from zmlx.tfc import seepage as seepage_config
from zmlx.tfc import timer as timer_config
from zmlx.tfc.config import SeepageTher, TherFlowConfig  # 弃用的

########################################
# ui
from zmlx.ui import (
    break_point,
    gui,
    gui_exec,
    information,
    open_gui,
    open_gui_without_setup,
    plot,
    question,
)
from zmlx.ui import (
    break_point as breakpoint,
)
from zmlx.ui import plot as do_plot

########################################
# utility
from zmlx.utils import (
    AttrKeys,
    CapillaryEffect,
    Field,
    GuiIterator,
    LinearField,
    PressureController,
    RuntimeFunc,
    SaveManager,
    SeepageCellMonitor,
    add_keys,
    get_gui_iter,
    load_field3,
)

########################################
# 其它
get_path = SelfPath(__file__)

########################################
# deprecated
create_hydconfig = RuntimeFunc(
    pack_name="zmlx.config.hydrate",
    func_name="create",
    deprecated_name="zmlx.create_hydconfig",
    deprecated_date="2025-5-7",
)
find = RuntimeFunc(pack_name="zmlx.ui.Config", func_name="find")
find_all = RuntimeFunc(pack_name="zmlx.ui.Config", func_name="find_all")


def _env(*args):
    """
    基于pip安装zmlx的依赖项. 包括numpy, scipy, matplotlib, pyqtgraph, PyOpenGL6,
     PyQt6, PyQt6-WebEngine, pyqt6-qscintilla, PyOpenGL,
     dulwich, pillow, pyvista, pyvistaqt, vtk, pandas, openpyxl 等
    """
    from zmlx.algs import install_dep

    install_dep()


def _demo(*args):
    """
    打开界面并显示demo，在这个界面，可以尝试打开demo代码或者直接运行demo代码
    """

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
                "func": func,
                "desc": desc or (func.__doc__ or "").strip().split("\n")[0],
                "usage": usage or name,
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
            "func": func,
            "desc": (func.__doc__ or "").strip().split("\n")[0] if func.__doc__ else "",
            "usage": name,
        }

    def __getitem__(self, name):
        return self._commands[name]["func"]

    def __contains__(self, name):
        return name in self._commands

    def get(self, name):
        """获取命令函数，不存在返回 None"""
        entry = self._commands.get(name)
        return entry["func"] if entry else None

    def items(self):
        """迭代 (名称, 函数) 对（兼容旧代码的 for cmd, f in cmds.items()）"""
        for name, entry in self._commands.items():
            yield name, entry["func"]

    def keys(self):
        return self._commands.keys()

    def get_desc(self, name):
        """获取命令描述"""
        entry = self._commands.get(name)
        return entry["desc"] if entry else ""

    def get_usage(self, name):
        """获取命令用法"""
        entry = self._commands.get(name)
        return entry["usage"] if entry else name

    def help(self, name=None):
        """
        打印帮助信息。
        - 不指定 name：列出所有可用命令
        - 指定 name：显示该命令的详细帮助
        """
        if name:
            entry = self._commands.get(name)
            if entry:
                func = entry["func"]
                doc = (func.__doc__ or "").strip()
                print(f"命令: {name}")
                print(f"用法: python -m zmlx {entry['usage']}")
                if doc:
                    print(f"\n{doc}")
            else:
                print(f"未知命令: {name}")
                print("使用 'python -m zmlx help' 查看可用命令。")
        else:
            print("IGG-Hydrate (zmlx) 命令行工具")
            print("用法: python -m zmlx <命令> [参数...]\n")
            print("可用命令:")
            max_len = max(len(n) for n in self._commands) if self._commands else 0
            for cmd_name, entry in sorted(self._commands.items()):
                print(f"  {cmd_name:<{max_len + 2}}{entry['desc']}")
            print("\n使用 'python -m zmlx help <命令>' 查看命令详情。")

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
        if key in ("help", "--help", "-h"):
            if len(argv) > 2 and argv[2] not in ("--help", "-h"):
                self.help(name=argv[2])
            else:
                self.help()
            return

        entry = self._commands.get(key)
        if entry is None:
            print(f"未知命令: {key}")
            print("使用 'python -m zmlx help' 查看可用命令。")
            return

        # 检查子命令是否请求帮助
        args = argv[2:]  # 不再包含命令名本身
        if args and args[0] in ("--help", "-h"):
            self.help(name=key)
            return

        # 执行命令
        entry["func"](args)


# 创建全局命令注册器
_cmds = _CommandRegistry()


def _test(args):
    """
    以无头模式运行所有 demo 测试。
    """
    import os
    import subprocess
    import sys

    script = os.path.join(os.path.dirname(__file__), "demos", "test_all_demos.py")
    if not isinstance(args, list):
        args = []
    subprocess.run([sys.executable, script, "--no-gui"] + args)


# 注册命令（兼容旧的 _cmds 字典接口）
_cmds["env"] = _env
_cmds["ui"] = _ui
_cmds["demo"] = _demo
_cmds["ver"] = _ver
_cmds["test"] = _test


def main(argv):
    """
    命令行入口。支持的命令:
        env  - 安装依赖
        ui   - 打开GUI界面
        demo - 打开Demo浏览器
        test - 无头模式运行所有demo测试
        ver  - 显示版本信息
        help - 显示帮助
    """
    _cmds.execute(argv)


########################################
# 自动反馈历史日志（导入 zmlx 时执行一次）
#
# ⚠️ **必须留在文件底部**：此刻整个 zmlx（含 `ui` 等）都已加载完 —— 这既是「导入 zmlx
#    完成」的准确时点，也保证这个动作不会插进任何一个子包的导入过程。
# ⚠️ 这段原先在 ``zmlx/exts/__init__.py`` 的导入期执行（2026-10-17 移来）。exts 是
#    DLL 绑定层（第 1 层），不该在导入时做「读日志文件 + 联网提交」这类应用级副作用；
#    包入口的底部才是它该待的地方。
# 行为：只提交 **非当天** + **最近 `_FEEDBACK_MONTHS` 个月内** + 没反馈过的日志；
# 开关仍是 ``disable_auto_feedback=Yes``（界面：设置 → 不向开发者反馈）。
#
# ⚠️ 过期不再补发（2026-10-17 用户要求）：超过两个月的日志，**即便从未反馈过也不再
#    尝试** —— 隔了那么久的运行环境已经对不上，发上去只会给排查添噪音。
#    这些老文件**不打标记**（``logs_feedback/`` 里不会多出空文件）：标记的语义是
#    「这条已经发过」，没发过就不该有标记；代价只是每次 import 多几次文件名比较。

#: 只反馈最近这么多个月内的日志（按**日历月**算，不是 30 天 × N）
_FEEDBACK_MONTHS = 2


def _feedback_cutoff(months: int = _FEEDBACK_MONTHS, today=None):
    """返回「最近 months 个月」的起点日期（**含**当天）。

    ⚠️ 按**日历月**而不是「60 天」：用户说的是「两个月」—— 2026-08-17 那份日志在
       2026-10-17 刚好满两个月，按 60 天算会多留 1~2 天，把「刚好过期」的又发出去。
    ⚠️ 月底要夹到目标月的最后一天：3-31 往前两个月是 1-31，那天不存在。

    Args:
        months: 往前推多少个月（默认 :data:`_FEEDBACK_MONTHS`）。
        today: 起算日（``datetime.date``）；``None`` 表示今天。仅供自测传入。
    """
    import calendar
    import datetime

    if today is None:
        today = datetime.date.today()
    year, month = today.year, today.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(today.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def _log_date(name: str):
    """从 ``YYYY-MM-DD.log`` 里取日期；名字不合规返回 ``None``（跳过，不去猜）。"""
    import datetime

    try:
        return datetime.datetime.strptime(name, "%Y-%m-%d.log").date()
    except Exception:
        return None


def _feedback_logs():
    """自动收集并反馈历史日志文件。

    检查 ``app_data.root('logs')`` 下的日志，把**非当天**、**最近两个月内**、且没反馈
    过的那些提交给作者；提交成功的（含服务端答「刚发过」的）在 ``logs_feedback/`` 写
    一个同名空文件作标记，避免重复发送。

    ⚠️ 超过两个月的日志**直接跳过、也不打标记**：时间太久，环境已对不上，发上去没用。

    本函数**不抛异常**：它是导入期的副作用，任何失败都必须静默 —— 否则一次网络问题
    就会让 ``import zmlx`` 直接失败。
    """
    try:
        import datetime
        import os

        from zmlx.exts import feedback
        from zmlx.system import make_dirs

        folder_logs = app_data.root("logs")
        if not os.path.isdir(folder_logs):
            return
        folder_logs_feedback = app_data.root("logs_feedback")
        make_dirs(folder_logs_feedback)
        has_feedback = set(os.listdir(folder_logs_feedback))
        date = datetime.datetime.now().strftime("%Y-%m-%d.log")
        cutoff = _feedback_cutoff()
        city = None
        for name in os.listdir(folder_logs):
            if name == date or name in has_feedback:
                continue
            day = _log_date(name)
            if day is None or day < cutoff:
                continue
            with open(os.path.join(folder_logs, name), "r", encoding="utf-8") as f1:
                text = f1.read()
            if city is None:
                try:
                    from zmlx.algs.sys import get_city

                    city = f" from {get_city()}"
                except Exception:
                    city = ""
            if feedback(text=text[0:100000], subject=f"log <{name}>{city}"):
                with open(os.path.join(folder_logs_feedback, name), "w") as f2:
                    f2.write("\n")
    except Exception:  # noqa: BLE001
        pass


try:
    if (
        app_data.getenv("disable_auto_feedback", default="No", ignore_empty=True)
        != "Yes"
    ):
        _feedback_logs()
except Exception:  # noqa: BLE001
    pass


def __getattr__(name):
    """模块级惰性属性（PEP 562）：仅为兼容而保留的 ``version``。

    2026-10-29 弃用，**2027-10-29 删除** —— 内核编译日期（六位整数 ``yymmdd``，
    例如 ``261021``）请直接读 ``core.version``。

    ⚠️ **为什么只剩 ``version`` 一条**：``_DEPRECATED`` 里另外 25 个名字在本模块
    都已有**显式导入**（``from zmlx.algs import ...`` 等），属性查找根本不会走到这里
    —— 它们已经是真实的新位置，不需要「转发 + 警告」。``version`` 是唯一没有显式
    导入、只能靠本函数提供的名字。

    ⚠️ **实现只有 ``zmlx.exts`` 那一份**：取值、警告、去重、以及「警告落点与文案前缀」
    全部由 ``zmlx.exts.__getattr__`` 负责，本函数只做转发。⚠️ 用 ``getattr`` 走正常
    属性查找，**不**直接调用 ``zmlx.exts.__getattr__`` —— 后者是解释器在属性查找失败
    时回调的**钩子**，绕过查找就绕过了「exts 里确实没有该名字」这个前提。

    Args:
        name (str): 要取的属性名。

    Returns:
        已弃用的 ``version``，即内核的编译日期（``core.version``）；
        核心库没加载成时是 ``None``。

    Raises:
        AttributeError: ``name`` 不是 ``version``（其余名字照常报错）。

    Note:
        - ⚠️ 与 ``zmlx.__version__``（**包**版本，如 ``'1.9.6'``）**不是一个东西**。
        - ⚠️ 必须放在**文件末尾**：``__getattr__`` 只在「模块里找不到该名字」时才被
          调用，放在前面会被后面的 ``import *`` 与赋值抢先生效。
    """
    if name == "version":
        import zmlx.exts

        return getattr(zmlx.exts, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

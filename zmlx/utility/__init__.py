"""旧工具包名（**兼容垫片，已弃用**）：``zmlx.utility`` -> :mod:`zmlx.utils`.

⚠️⚠️ **本包整个是一层兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块**都会发出 :class:`DeprecationWarning`。

**新代码请写** ``from zmlx.utils import GuiIterator`` ——（子模块路径
``from zmlx.utils.gui_iterator import GuiIterator`` 同样可以）。

为什么改名为 ``utils``
----------------------

与 ``zmlx/ui/utils`` 统一拼写：``utility`` 只是 ``utils`` 的同义词，
两种写法在同一棵树里并存，只会让人犹豫该用哪个。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.utility`` 就不是一个包，
``from zmlx.utility import GuiIterator`` 与下面那些子模块 shim 全都失效 ——
垫片的价值正在于「老路径一条都不断」。

⚠️ **别与 ``zmlx.ui.utils`` 搞混**（两个都叫 utils）：

======================  ==========================================================
包                       内容
======================  ==========================================================
``zmlx.utils``           通用工具：字段 / 插值 / 存盘 / 迭代器控制 / 物性……
                         （**与界面无关**，纯计算与 IO）
``zmlx.ui.utils``        界面工具：``GuiApi`` / ``BreakPoint`` / ``TaskProc`` /
                         ``FileHandler`` / ``BackgroundTask`` / 许可答复解析
======================  ==========================================================

为什么留着而不删
----------------

``from zmlx.utility.<模块> import <类>`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史脚本 / 笔记里的 import；
③ 更早的兼容层（本包内部那些大写模块名，如 ``GuiIterator``）。

⚠️ 本包的**子模块**（``gui_iterator.py`` / ``AttrKeys.py`` / …）也是一样的垫片，
各自转发到 ``zmlx.utils`` 下的同名模块。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.utility`` 改为 ``zmlx.utils``（本包成了垫片）.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.utility`` 已弃用（2026-10-16）：工具包已改名为 ``zmlx.utils``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.utils import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.utils 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是在这里静态 import：
#    zmlx.utils 里某些模块（gui_iterator 等）会 import zmlx.ui / zmlx.tfc，
#    静态导入有可能在导入期打结（2026-10-16 在 widget 那次重构里实测踩过
#    ``partially initialized module``）。惰性转发在导入期一个子模块都不碰，
#    对使用者完全无感：``from zmlx.utility import GuiIterator`` 照常可用。
# ---------------------------------------------------------------------------

#: 名字 -> 所属的 ``zmlx.utils`` 模块名。
#:
#: ⚠️ 只收**当年 ``utility/__init__.py`` 就导出过**的那些名字，**不扩大 API 面**。
_NAMES = {
    'AttrKeys': 'attr_keys',
    'add_keys': 'attr_keys',
    'CapillaryEffect': 'capillary_effect',
    'Field': 'fields',
    'LinearField': 'fields',
    'FrameRateCtrl': 'frame_rate_ctrl',
    'GuiIterator': 'gui_iterator',
    'get_gui_iter': 'gui_iterator',
    'HeatInjector': 'heat_injector',
    'load_field3': 'interp',
    'Interp2': 'interp',
    'Interp3': 'interp',
    'PressureController': 'pressure_controller',
    'RuntimeFunc': 'runtime_fn',
    'SaveManager': 'save_manager',
    'SeepageCellMonitor': 'seepage_cell_monitor',
}

# ⚠️ ``SelfPath`` 当年也是本包**包级导出**之一（旧 __init__ 里 ``from zmlx.exts import
#    SelfPath``）。它不在 zmlx.utils 里，所以单独转接一次 —— 否则
#    ``from zmlx.utility import SelfPath`` 会断（实测验收脚本抓到过这一条）。
from zmlx.exts import SelfPath  # noqa: F401

# ⚠️ 旧 __init__ 末尾的 ``get_path = SelfPath(__file__)`` 同样是**包级导出**，漏掉就会断
#    ``from zmlx.utility import get_path``（全量审计抓到的真缺口）。
#    指向**新包**的 get_path —— 那才是「这一份代码在哪」的正确答案。
from zmlx.utils import get_path  # noqa: F401


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.utils` 的名字转发过来（理由见上面那段 ⚠️）.

    ⚠️ **本转发已弃用**（2026-10-16 起，**2027-10-16** 删除）。
    新代码请用 ``from zmlx.utils import X``。
    """
    mod = _NAMES.get(name)
    if mod is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    return getattr(importlib.import_module(f'zmlx.utils.{mod}'), name)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))

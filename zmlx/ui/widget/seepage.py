"""旧模块名（兼容层，**已弃用**）：``seepage`` -> :mod:`zmlx.ui.widgets.editors.seepage_edit`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/widgets/editors/seepage_edit.py`` 与
``zmlx/ui/widgets/editors/field_edit.py`` 里 —— 本文件除了下面那几行 import / 别名不该再有
任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.widgets.editors.seepage_edit import SeepageEdit, FludefEdit``。

⚠️ **中间那一跳 ``widgets/seepage.py`` 自己也已弃用**（2027-10-21 删除），所以导入本
模块会发**两条**警告：本文件的一条 + ``widgets/seepage.py`` 的一条。这符合预期 ——
越老的路径，提示越多。

为什么留着而不删
----------------

2026-10-16 把包名由单数 ``widget`` 改为复数 ``widgets``（单数与 Qt 自己的
``QtWidgets`` 太像，读代码时极易看错）。但 ``from zmlx.ui.widget.seepage import ...``
这条路径仍被三类来源用着，故留一年过渡：① 外部脚本与用户在控制台敲的命令；
② 历史标签页的 ``gui_restore``（重启时按存下来的字符串重放）；③ 更早的兼容层。

⚠️ 完整的兼容策略见 ``zmlx/ui/widget/__init__.py`` 与 ``widgets/AGENTS.md``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 目标改为 ``zmlx.ui.widgets.editors``；去掉 ``setup_ui``
    （已合并进 ``editors.setup_ui``），转发链多一跳弃用垫片
Modified by DeepSeek, 2026-10-22: ``setup_ui`` 最终落在插件
    ``zmlx/ui/plugins/builtin/editors.py``
Modified by DeepSeek, 2026-10-22: 目标一度改为 ``zmlx.scen.editors``，同日插件包取消、
    目标改回 ``zmlx.ui.widgets.editors``
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widget.seepage`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.ui.widgets.editors.seepage_edit``（``SeepageEdit`` / ``FludefEdit`` 等）；'
    '本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.widgets.seepage import *  # noqa: F401,F403
from zmlx.ui.widgets.seepage import (  # noqa: F401
    FludefEdit,
    FloatFieldEdit,
    IntFieldEdit,
    SeepageEdit,
    SeepageFormEdit,
    SeepageInterp1Edit,
    SeepageKrEdit,
    SeepageSummary,
    SeepageTabEdit,
    TextFieldEdit,
)

# ---- 旧类名兼容（2026-10-22 ``SeepageXxxEdit`` → ``XxxFieldEdit``）----
# ⚠️ 不能用 ``from zmlx.ui.widgets.seepage import *`` 拿到它们：旧名不在 ``__all__`` 里
#    （``__all__`` 只列新名）。所以这里用模块级 ``__getattr__``（PEP 562）显式转发，
#    与 ``widgets/seepage.py`` 保持同样的行为：只在真有人取旧名时才发警告。
_FIELD_OLD_NAMES = {
    'SeepageTextEdit': 'TextFieldEdit',
    'SeepageIntEdit': 'IntFieldEdit',
    'SeepageFloatEdit': 'FloatFieldEdit',
}


def __getattr__(name):
    """旧类名转发 + :class:`DeprecationWarning`（未知名字照常 ``AttributeError``）。"""
    new_name = _FIELD_OLD_NAMES.get(name)
    if new_name is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    from zmlx.system import warn

    warn(
        f'``{__name__}.{name}`` 的类已改名（2026-10-22）：请改用 '
        f'``zmlx.ui.widgets.editors.field_edit.{new_name}``；旧名将于 **2027-10-22** 删除'
        '（本转发层本身也在 2027-10-16 删除）。',
        DeprecationWarning,
        stacklevel=2,
    )
    from zmlx.ui.widgets.editors import field_edit

    return getattr(field_edit, new_name)

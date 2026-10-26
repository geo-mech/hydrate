"""旧模块（**已弃用**）：``widgets/seepage.py`` -> :mod:`zmlx.ui.widgets.editors.seepage_edit`.

⚠️ **本模块只是一层转发**，真正的实现在 :mod:`zmlx.ui.widgets.editors.seepage_edit` 与
:mod:`zmlx.ui.widgets.editors.field_edit` 里 —— 本文件除了下面那几行 import / 别名不该
再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-21 删除**（2026-10-21 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.widgets.editors.seepage_edit import SeepageEdit, FludefEdit``。

为什么搬来搬去
--------------

``seepage.py`` 里的 10 个类**全部**成对实现了 ``set_data()`` / ``get_data()`` ——
按本仓的定义（给数据 → 编辑 → 取回）它们就是**编辑器**，与 ``editors/`` 里的
``ArrayEdit`` / ``Interp1Edit`` 是同一类东西，只是面向的模型不同。2026-10-21 先搬进
``widgets/editors/``（与其它编辑器同处），2026-10-22 曾连同装配代码搬进插件包
``zmlx/scen/editors/``，同一天那个插件包又整体取消：**控件回到本子包**（它们本就属于
编辑器子包），装配代码合成 ``plugins/builtin/editors.py`` 一个插件文件。

⚠️ **本模块不再提供 ``setup_ui``**：它原来注册的 ``gui.open_seepage`` / ``gui.open_fludef``
现在由插件 ``zmlx/ui/plugins/builtin/editors.py`` 的 ``setup_file_types()`` 注册。

为什么留一年
------------

历史标签页的 ``gui_restore`` 会把命令字符串存下来、重启时按原文重放；外部脚本也可能
直接 ``from zmlx.ui.widgets.seepage import SeepageEdit``。所以老路径必须继续可用 ——
本文件得指向新位置。⚠️ 新位置在**同层**（``ui/widgets/editors/``），所以这里不再有
``ui`` → ``scen`` 那种倒置分层的 import。

⚠️ 更老的 ``zmlx.ui.widget.seepage`` 仍然可用（它转发到**本模块**，导入时两条
``DeprecationWarning`` 都会发），2027-10-16 先于本模块删除。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-21: 控件全部搬进 ``widgets/editors/seepage_edit.py`` 与
    ``field_edit.py``，本文件退化为弃用垫片
Modified by DeepSeek, 2026-10-22: 注册入口移进插件（当时的 ``zmlx/scen/editors/``）
Modified by DeepSeek, 2026-10-22: 目标一度改为 ``zmlx.scen.editors``（控件随插件搬进 ``scen/``）
Modified by DeepSeek, 2026-10-22: 插件包取消，目标改回 ``zmlx.ui.widgets.editors``
"""
from zmlx.system import warn

warn(
    '``zmlx.ui.widgets.seepage`` 已弃用（2026-10-21）：控件在 '
    '``zmlx.ui.widgets.editors``（``seepage_edit`` / ``field_edit``）；'
    '``gui.open_seepage`` 等命令由插件 ``zmlx/ui/plugins/builtin/editors.py`` 注册；'
    '本转发层将于 **2027-10-21** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.widgets.editors.field_edit import (  # noqa: F401
    FloatFieldEdit, IntFieldEdit, TextFieldEdit)
from zmlx.ui.widgets.editors.seepage_edit import (  # noqa: F401
    FludefEdit,
    SeepageEdit,
    SeepageFormEdit,
    SeepageInterp1Edit,
    SeepageKrEdit,
    SeepageSummary,
    SeepageTabEdit,
)

# ---- 旧类名兼容（2026-10-22 ``SeepageXxxEdit`` → ``XxxFieldEdit``）----
# 本模块是老路径的转发层，当年导出的正是旧名，所以旧名必须在这里继续可用。
# ⚠️ 用模块级 ``__getattr__``（PEP 562）而不是 ``SeepageTextEdit = TextFieldEdit``：
#    只在**有人真正取这个名字**时才发警告，导入本模块本身不再多出一条。
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
    warn(
        f'``{__name__}.{name}`` 的类已改名（2026-10-22）：请改用 '
        f'``zmlx.ui.widgets.editors.field_edit.{new_name}``；旧名将于 **2027-10-22** 删除'
        '（本转发层本身也在 2027-10-21 删除）。',
        DeprecationWarning,
        stacklevel=2,
    )
    return globals()[new_name]

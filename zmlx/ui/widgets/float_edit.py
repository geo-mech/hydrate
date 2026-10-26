"""旧模块（**已弃用**）：``widgets/float_edit.py`` -> :mod:`zmlx.ui.widgets.editors`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/widgets/editors/float_edit.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-21 删除**（2026-10-21 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.widgets.editors import Slider, Dial``。

为什么搬走
----------

``Slider`` / ``Dial`` 都成对实现了 ``set_data(value)`` / ``get_data()`` —— 按本仓的定义
（给数据 → 编辑 → 取回）它们就是**编辑器**，与 ``editors/`` 里的 ``ArrayEdit`` /
``SeepageIntEdit`` 是同一类东西。搬到 ``editors/float_edit.py`` 之后，``widgets/`` 根目录
只剩**纯控件**（``CodeEdit`` / ``TextBrowser`` / ``MatplotWidget`` / ``Label`` ……），
「编辑器」全部集中在 ``editors/`` 一个地方。

⚠️ 与 ``widgets/seepage.py`` 垫片的差别：本模块**没有** ``setup_ui``（``Slider`` /
``Dial`` 从不注册文件类型），所以不需要合并任何注册逻辑 —— 这也意味着导入本模块
**只**发出上面那一条警告，不会再带出第二条。

为什么留一年
------------

外部脚本可能还写着 ``from zmlx.ui.widgets.float_edit import Slider``。

⚠️ 更老的 ``zmlx.ui.widget.float_edit`` 仍然可用（它转发到**本模块**，2027-10-16 删除）。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-21: ``Slider`` / ``Dial`` 搬进 ``widgets/editors/float_edit.py``，
    本文件退化为弃用垫片
"""
from zmlx.system import warn

warn(
    '``zmlx.ui.widgets.float_edit`` 已弃用（2026-10-21）：请改用 '
    '``zmlx.ui.widgets.editors``（``Slider`` / ``Dial``）；'
    '本转发层将于 **2027-10-21** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.widgets.editors import Dial, Slider  # noqa: F401
from zmlx.ui.widgets.editors.float_edit import (  # noqa: F401
    test_dial,
    test_slider,
)

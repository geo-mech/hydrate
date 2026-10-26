"""旧模块名（兼容层，**已弃用**）：``img`` -> :mod:`zmlx.ui.plugins.builtin.image_browser`.

⚠️ **本模块只是一层转发**，真正的实现（``ImageView``）现在在插件
``zmlx/ui/plugins/builtin/image_browser.py`` 里 —— 本文件除了下面那几行 import / 别名
不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.plugins.builtin.image_browser import ImageView``
（⚠️ 那是**插件内部**的路径，正常业务代码根本不需要直接造 ``ImageView`` ——
开图片请调 ``gui.open_image(...)``）。

搬了几次 / 为什么留着
--------------------

2026-10-16 把「**顶层控件**」（只被装配层打开成一个标签页、**不会被任何控件当组件
（子控件）用**）集中迁到 ``zmlx/ui/tabs/``；2026-10-22 又把 ``ImageView`` 连同
``open_image`` 一起并入插件「图片浏览」（搬走后它只剩那个插件在用 —— 「可关掉的功能，
它的代码也应当能一起关掉」）。本垫片随之改指新位置，老路径继续可用。

⚠️ 这条路径仍被三类来源用着，故留一年过渡：① 外部脚本与用户在控制台敲的命令；
② 历史标签页的 ``gui_restore``（重启时按存下来的字符串重放）；③ 更早的兼容层
（``license_count`` / ``license_feedback``）。

⚠️ **本模块现在是** ``ui`` → ``plugins`` 的**逆向 import**（同 ``widget/demo_view.py``）：
只允许出现在兼容层，正常代码不要效仿。

⚠️ 判据与依赖方向见 ``zmlx/ui/tabs/AGENTS.md``。

Created by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-22: 目标改为插件 ``plugins/builtin/image_browser.py`` ——
    ``ImageView`` 随 ``open_image`` 并入了「图片浏览」插件
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widgets.img`` 已弃用（2026-10-16）：控件 ``ImageView`` 已迁至插件 '
    '``zmlx.ui.tabs.img``（2026-10-22 起）；本转发层将于 '
    '**2027-10-16** 删除。开图片请用 ``gui.open_image(...)``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.tabs.img import ImageView  # noqa: F401

__all__ = ['ImageView']

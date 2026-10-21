"""控件包（``zmlx.ui.widgets``）：本目录收「**底层控件**」等可复用控件.

⚠️ **目录名是 ``widgets``（复数）**。2026-10-16 起，旧的单数包名 ``zmlx.ui.widget``
保留为**兼容垫片**（转发到本包与 :mod:`zmlx.ui.tabs`，导入即发
:class:`DeprecationWarning`，**2027-10-16 删除**）；zmlx 内部代码一律只用
``zmlx.ui.widgets``。

本目录收什么
------------

**底层控件**（会被别的控件 ``addWidget()`` 进去、或被继承的）、
**宿主不是标签页的常驻控件**（状态栏按钮 / 右侧栏面板 / 标签容器）、
**对话框 / 表单组件集**。

⚠️ 「**顶层控件**」（只被装配层打开成一个标签页、不被任何控件复用）在
:mod:`zmlx.ui.tabs` —— 判据与依赖方向见 ``widgets/AGENTS.md`` 与 ``tabs/AGENTS.md``。

⚠️ 依赖方向单向：``tabs/`` 可复用 ``widgets/``，``widgets/`` **不得**依赖 ``tabs/``
（一旦有人这么做，就说明那个控件正被别人当组件用 —— 它该搬回本目录）。

⚠️ **本目录 2026-10-16 由 ``zmlx.ui/widget`` 改名为 ``zmlx.widgets``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``底层控件 + 宿主非标签页的常驻控件 + 对话框组件集``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.ui/widget`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.ui/widget`` 改为 ``zmlx.widgets``.
"""

# 底层控件：会被别的控件 ``addWidget()`` 进去、或被继承的。
from zmlx.ui.widgets.code_edit import CodeEdit
from zmlx.ui.widgets.label import Label
from zmlx.ui.widgets.license_button import LicenseButton
from zmlx.ui.widgets.md_view import MarkdownView
from zmlx.ui.widgets.output_widget import OutputWidget
from zmlx.ui.widgets.plt import MatplotWidget
from zmlx.ui.widgets.tab_widget import TabWidget
from zmlx.ui.widgets.text_browser import TextBrowser
from zmlx.ui.widgets.version_button import VersionButton

"""顶层控件包（``zmlx.ui.tabs``）.

本包收纳**顶层控件** —— 它们只被装配层（``ui/main.py`` / ``ui/extra_setups/`` /
``zmlx/utility/`` 等）打开成一个标签页，**不会被任何控件当组件（子控件）用**。
归属判据、与 ``zmlx/ui/widget/`` 的分工见同目录的 ``AGENTS.md``。

⚠️ 两条硬约束：

1. **依赖单向**：``tabs/`` 可以复用 ``widget/``，**反之不行** —— ``widget/`` 一旦 import 了
   本包的东西，就说明那个控件正在被别人当组件用，那它该搬回 ``widget/``。
2. **本包内控件相互独立**：顶层控件之间不得互相依赖（连"借用对方一个函数"也不行），
   共用的逻辑请**下沉**到 ``zmlx.ui.utils.lic_utils`` 之类的底层模块。

⚠️ **底层控件**（编辑器、浏览器、属性表……）与**宿主不是标签页的常驻控件**（状态栏按钮 /
右侧栏面板 / 标签容器 / 对话框组件集）**不在这里**，仍在 ``zmlx/ui/widget/``。

⚠️ 老路径 ``from zmlx.ui.widget.<模块> import <类>`` 仍然可用 —— 整个 ``widget/`` 现在是
一层**兼容垫片**（导入即发 ``DeprecationWarning``，2027-10-16 删除），见该包的模块文档。
"""

from zmlx.ui.tabs.about import About
from zmlx.ui.tabs.app_path_edit import AppPathEdit
from zmlx.ui.tabs.check_count_view import CheckCountView
from zmlx.ui.tabs.code_history_view import CodeHistoryView
from zmlx.ui.tabs.cwd_view import CwdView
from zmlx.ui.tabs.demo_view import DemoView
from zmlx.ui.tabs.env_edit import EnvEdit
from zmlx.ui.tabs.feedback_tool import FeedbackTool
from zmlx.ui.tabs.feedbacks_view import FeedbacksView
from zmlx.ui.tabs.fn2 import Fn2Widget
from zmlx.ui.tabs.gui_iter_edit import GuiIteratorEdit
from zmlx.ui.tabs.img import ImageView
from zmlx.ui.tabs.license_register import LicenseRegister
from zmlx.ui.tabs.mem_view import MemView
from zmlx.ui.tabs.message import MessageEdit
from zmlx.ui.tabs.output_history_view import OutputHistoryView
from zmlx.ui.tabs.pg import PgConsole
from zmlx.ui.tabs.plugin_list_edit import PluginListEdit
from zmlx.ui.tabs.readme_browser import ReadMeBrowser
from zmlx.ui.tabs.reg_tool import RegTool
from zmlx.ui.tabs.solver_selector import SolverSelector
from zmlx.ui.tabs.string_table import StringTable
from zmlx.ui.tabs.style_sheet_edit import StyleSheetEdit
from zmlx.ui.tabs.tab_detail_view import TabDetailView
from zmlx.ui.tabs.text_file_edit import TextFileEdit
from zmlx.ui.tabs.timer_view import TimerView

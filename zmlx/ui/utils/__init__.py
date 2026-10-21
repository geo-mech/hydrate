"""界面工具包（``zmlx.ui.utils``）：服务于 ``zmlx.ui`` 的工具集合.

**定位**：这里是「给界面层用的工具箱」。判据只有一条 —— **它服务于 ``zmlx.ui``**，
而**不要求它依赖 Qt**。于是本包里既有必须用 Qt 的东西（线程桥接、断点、任务队列
都要 ``QObject`` / ``QMutex``），也有纯 stdlib 的文本解析工具（:mod:`.lic_utils`）。
是否依赖 Qt 由**各子模块自己的需要**决定，不是入选的门槛。

⚠️ **本包 2026-10-16 由模块 ``zmlx/ui/utils.py`` 改成包**（原文件 687 行按主题拆分），
目的是给「界面工具」一个能放东西的地方 —— 新加入的后台循环任务
（:class:`~zmlx.ui.utils.background_task.BackgroundTask`）与原先游离在 ``ui/`` 根目录的
:mod:`.lic_utils` 都归到这里，``ui/`` 根目录因此只剩下真正的「层」（``main`` /
``gui_buffer`` / ``console`` / ``pyqt`` …）。

**老路径完全不变**：``from zmlx.ui.utils import GuiApi`` 照旧可用 —— 本
``__init__`` 把下面各子模块的公开名字**逐个转发**上来，所以
``zmlx.ui.utils`` 这个名字空间与拆分之前**逐名等价**。⚠️ 这里**不发**
``DeprecationWarning``：它不是「旧写法」而是本包的正门，内部代码
（``main.py`` / ``console.py`` / ``widget/tab_widget.py``）都走这条路径。

子模块分工
----------

========================  ==========  ==============================================
子模块                     依赖 Qt     内容
========================  ==========  ==============================================
``shared.py``             是          ``SharedValue`` / ``SharedList`` / ``SharedDict``
                                      （跨线程共享容器，只依赖 ``QtCore``）
``gui_api.py``            是          ``GuiApi``（把非 GUI 线程的调用派发到主线程）
``break_point.py``        是          ``BreakPoint``（暂停 / 继续，GUI 线程永不阻塞）
``task_proc.py``          是          ``TaskProc``（信号驱动的异步任务队列）
``file_handler.py``       是          ``FileHandler`` / ``CodeFile``（按扩展名分发文件）
``background_task.py``    是          ``BackgroundTask``（最低优先级线程里反复执行回调）
``lic_utils.py``          **否**     许可答复的解析与查询（纯文本，任何层都可导入）
========================  ==========  ==============================================

转发的「三条」与不转发的「两条」
--------------------------------

本 ``__init__`` 只转发**需要 Qt 的 GUI 基础设施**（上表前五行）；下面两个
**刻意不转发**，都必须按子模块路径单独导入：

- :mod:`.background_task` —— 它在模块级**主动抛 ``ImportError``**（无头模式下没有
  Qt 线程原语），转发它会让 ``import zmlx.ui.utils`` 本身失败。
  用 ``from zmlx.ui.utils.background_task import BackgroundTask``。
- :mod:`.lic_utils` —— 本包里**唯一不依赖 Qt** 的模块，且它 import 了
  :mod:`zmlx.exts.web_license`（扩展层）；转发它等于让每一次
  ``import zmlx.ui.utils`` 都连带拉起扩展层。
  用 ``from zmlx.ui.utils.lic_utils import ...``。

⚠️ 两个「不转发」的理由不同：前者是**会炸**（正确性），后者是**不想白拉依赖**
（克制）。两者都保持按需导入。

Modified by DeepSeek, 2026-10-16: 由 ``zmlx/ui/utils.py`` 改为包（原内容按主题拆分，
并收编 ``lic_utils.py`` 与 ``background_task.py``）.
"""

from zmlx.ui.utils.shared import SharedValue, SharedList, SharedDict
from zmlx.ui.utils.gui_api import GuiApi
from zmlx.ui.utils.break_point import BreakPoint
from zmlx.ui.utils.task_proc import TaskProc
from zmlx.ui.utils.file_handler import FileHandler, CodeFile

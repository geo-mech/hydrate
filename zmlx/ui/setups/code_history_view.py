"""脚本执行历史浏览器（``CodeHistoryView``）+ 命令 ``gui.show_code_history``.

**本文件自含**：控件 :class:`CodeHistoryView` 与「开标签页」的入口 :func:`show_code_history`
都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/code_history_view.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把 `MainWindow.show_code_history` 的方法体原样搬成模块级函数。

为什么在 ``setups/`` 而不是 ``tabs/``
------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- 它由**两处通用控件**调用 —— 控制台的右键菜单「脚本运行历史」
  （``widgets/output_widget.py``）与代码编辑器的右键菜单「编辑历史」
  （``widgets/code_edit.py``），靠的都是**命令** ``gui.show_code_history(...)``。
  做成插件，用户关掉它之后这两个菜单项就会变成一句「找不到命令」。
- 也不该只算「一个标签页控件」：``tabs/`` 收的是「只被装配层打开成页面的顶层控件」，
  而这个入口带**参数**（``folder`` / ``caption``）、要写 ``gui_restore``，
  且被上面的通用控件按命令名调用。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

命令与参数（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
命令                        ``gui.show_code_history(folder, caption=None)``
``gui_restore``             ``gui.show_code_history(**{'folder': …, 'caption': …})``
菜单项                      无（只由上面两处控件的右键菜单调用）
=========================  ==================================================

⚠️ **命令名与签名都不能改**：

1. 历史标签页的 ``gui_restore`` 存的就是那串 ``f"gui.show_code_history(**{kwds})"``，
   重启时按原文重放；
2. 两处通用控件按**名字**调它（``gui.show_code_history(folder=…)``）。

⚠️ ``folder`` 不是字符串、或目录不存在时**静默 return**（原实现如此）：调用方传的是
「历史目录」，它可能还没被创建 —— 那种情况什么都不做比弹错误框更合适。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-31: 由 ``zmlx/ui/tabs/code_history_view.py`` 搬到
    ``setups/``（原模块删除、**不留垫片**），并接管 ``MainWindow.show_code_history``；
    命令名与签名均未变。
"""

import glob
import os

from zmlx.system import execute_once, read_text
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.code_edit import CodeEdit


class CodeHistoryView(QtWidgets.QWidget):
    def __init__(self, parent=None, count_max=100):
        super().__init__(parent)
        self.__current_folder = None
        self.count_max = count_max

        layout = QtWidgets.QHBoxLayout(self)

        # 左侧文件列表（保持与之前相同）
        self._list = QtWidgets.QListWidget()
        self._list.itemClicked.connect(self.__show_content)
        layout.addWidget(self._list, stretch=2)

        # 右侧代码编辑器
        self._edit = CodeEdit()
        layout.addWidget(self._edit, stretch=5)

        self._list.clear()
        self._edit.clear()

    def set_folder(self, folder, count_max=None):
        """
        设置目标文件夹，自动过滤.py文件
        """
        if count_max is not None:
            self.count_max = count_max

        self.__current_folder = os.path.abspath(folder)
        self.__refresh_list()

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
            self.__show_content(self._list.currentItem())

    def console_exec(self):
        self._edit.console_exec()

    def __refresh_list(self):
        """
        刷新.py文件列表
        """
        self._list.clear()

        if not self.__current_folder or not os.path.isdir(
                self.__current_folder):
            return

        pattern = os.path.join(self.__current_folder, "*.py")
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            if idx > self.count_max:
                break
            time_str = QtCore.QDateTime.toString(
                mtime, "yyyy-MM-dd hh:mm")
            text = read_text(file_path, encoding='utf-8')
            text = text[:300]
            item = QtWidgets.QListWidgetItem(
                f"\n{idx:02d}.\t{time_str}\n\n{text}\n--------------\n\n")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, file_path)
            self._list.addItem(item)

    def __show_content(self, item):
        """
        使用CodeEdit打开文件
        """
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._edit.open(file_path)  # 依赖CodeEdit自身的错误处理


def show_code_history(folder, caption=None):
    """打开（或切到）一个「脚本执行历史」标签页；同时也是 GUI 命令 ``gui.show_code_history``.

    Args:
        folder: 要浏览的历史目录（里面放 ``*.py``）。**不是字符串、或目录不存在时静默 return**
            —— 调用方传的多半是「历史目录」，它可能还没被创建。
        caption: 标签页标题；不给时用 ``folder`` 的目录名。

    ⚠️ 由 ``MainWindow.show_code_history`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_code_history', show_code_history)`` **显式补上**。

    ⚠️ **标签页按「控件类型 + 标题」复用**：同一个目录（同样的 caption）再点一次只会切过去；
    不同目录会各开一个（标题就是目录名）—— 这正是原来 `get_widget(... caption=caption ...)`
    的行为，不要改成固定标题。

    ⚠️ ``gui_restore`` 里存的是 ``folder`` 与 ``caption`` 的 **repr**：重启时按原文重放，
    所以这两个参数的**名字**也不能改（``folder`` / ``caption``）。
    """
    if not isinstance(folder, str):
        return

    if os.path.isdir(folder):
        kwds = dict(folder=folder, caption=caption)

        if caption is None:
            caption = os.path.basename(folder)

        def oper(widget):
            widget.set_folder(folder=folder)
            widget.gui_restore = f"""gui.show_code_history(**{kwds})"""

        gui.get_widget(
            CodeHistoryView,
            caption=caption,
            on_top=True,
            oper=oper,
            icon="python",
        )


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.show_code_history``（由 ``setups/__init__.py`` 调用）.

    ⚠️ 本文件**不挂菜单项**：它只被控制台与代码编辑器的**右键菜单**调用
    （``widgets/output_widget.py`` / ``widgets/code_edit.py``），那两处按命令名调用，
    所以这里只要有 ``add_func`` 就够了。

    ``@execute_once`` 是双保险：重复调用不会把命令注册两遍。
    """
    gui.add_func('show_code_history', show_code_history)

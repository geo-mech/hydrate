"""控制台输出历史浏览器（``OutputHistoryView``）+ 命令 ``gui.show_output_history``.

**本文件自含**：控件 :class:`OutputHistoryView` 与「开标签页」的入口 :func:`show_output_history`
都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/output_history_view.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把 `MainWindow.show_output_history` 的方法体原样搬成模块级函数。

为什么在 ``setups/`` 而不是 ``tabs/``
------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- 它与 :mod:`zmlx.ui.setups.code_history_view` 是**同一条链**：控制台的右键菜单
  （``widgets/output_widget.py``）里「脚本运行历史 / 输出历史」两项并列、都按**命令名**调用。
  做成插件的话，关掉它那个菜单项就变成「找不到命令」。
- 也不该只算「一个标签页控件」：``tabs/`` 收的是「只被装配层打开成页面的顶层控件」，
  而它被上面的通用控件按命令名调用，且要写 ``gui_restore``。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

命令与参数（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
命令                        ``gui.show_output_history()``
标签页标题                  「输出历史」
``gui_restore``             ``gui.show_output_history()``
=========================  ==================================================

⚠️ **命令名不能改**：历史标签页的 ``gui_restore`` 存的就是 ``gui.show_output_history()``，
重启时按原文重放；控制台的右键菜单也按这个名字调它。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-31: 由 ``zmlx/ui/tabs/output_history_view.py`` 搬到
    ``setups/``（原模块删除、**不留垫片**），并接管 ``MainWindow.show_output_history``；
    命令名与行为均未变。
"""

import glob
import os

from zmlx.system import app_data, execute_once
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.text_browser import TextBrowser


class OutputHistoryView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder = None
        self.current_ext = None
        self.main_layout = QtWidgets.QHBoxLayout(self)

        # 左侧文件列表
        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemClicked.connect(self.show_file_content)
        self.main_layout.addWidget(self.file_list, stretch=2)

        # 右侧文本显示
        self.text_view = TextBrowser(self)
        self.main_layout.addWidget(self.text_view, stretch=5)

        self.clear_display()
        self.set_folder()

    def clear_display(self):
        self.file_list.clear()
        self.text_view.clear()

    def set_folder(self, folder=None):
        if folder is None:
            folder = app_data.root('output_history')

        if folder is not None:
            self.current_folder = folder
            # ⚠️ 扩展名取 OutputWidget.SUFFIX（.html）：历史自 2026-10-26 起存成富文本，
            #    写死 'txt' 会让这一页**列不出任何新文件**（旧 .txt 仍会一起列出，见
            #    refresh_file_list）。少一个依赖反向耦合：这里只导入 SUFFIX 常量。
            from zmlx.ui.widgets.output_widget import OutputWidget
            self.current_ext = OutputWidget.SUFFIX
            self.refresh_file_list()

            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(0)
                self.show_file_content(self.file_list.currentItem())

    def refresh_file_list(self):
        self.file_list.clear()

        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        # 同一目录里既有旧版 .txt 也有新版 .html，两种都要列出（按修改时间倒序混排）
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(os.path.join(self.current_folder, '*.txt'))]
        files += [(f, QtCore.QFileInfo(f).lastModified()) for f in
                  glob.glob(os.path.join(self.current_folder, f'*{self.current_ext}'))]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            filename = os.path.basename(file_path)
            time_str = QtCore.QDateTime.toString(
                mtime,
                "yyyy-MM-dd hh:mm")  # 时间格式保持兼容

            item = QtWidgets.QListWidgetItem(
                f"{idx:02d}. {time_str}: \n\t{filename}\n")
            item.setData(QtCore.Qt.ItemDataRole.UserRole,
                         file_path)  # 使用兼容的角色类型
            self.file_list.addItem(item)

    def show_file_content(self, item):
        file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        try:
            # ⚠️ 必须显式 encoding='utf-8'（默认取系统编码，中文 Windows 上是 GBK）
            with open(file_path, "r", encoding='utf-8') as f:
                text = f.read()
            if str(file_path).lower().endswith('.html'):
                # 新版历史：HTML 富文本，保留颜色 / 粗体
                self.text_view.setHtml(text)
            else:
                # 旧版历史：纯文本
                self.text_view.setText(text)
        except Exception as err:
            self.text_view.setText(
                f"读取文件错误：{str(err)}. file_path={file_path}")


def show_output_history():
    """打开（或切到）「输出历史」标签页；同时也是 GUI 命令 ``gui.show_output_history()``.

    ⚠️ 由 ``MainWindow.show_output_history`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_output_history', show_output_history)`` **显式补上**。

    ⚠️ 目录由控件自己决定（:meth:`OutputHistoryView.set_folder` 的缺省值
    ``app_data.root('output_history')``）—— 这里**不要**传 folder：``oper`` 每次打开都会跑，
    传死一个目录会让「换工作路径后再打开还看旧目录」。

    ⚠️ 标签页按「控件类型 + 标题」复用：重复调用只会切到那一页。
    """
    def oper(w):
        w.gui_restore = """gui.show_output_history()"""
        w.set_folder()

    gui.get_widget(
        OutputHistoryView, caption="输出历史", on_top=True, oper=oper
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.show_output_history``（由 ``setups/__init__.py`` 调用）.

    ⚠️ 本文件**不挂菜单项**：它只被控制台的**右键菜单**「输出历史」调用
    （``widgets/output_widget.py``），那处按命令名调用，所以这里只要有 ``add_func`` 就够了。
    """
    gui.add_func('show_output_history', show_output_history)

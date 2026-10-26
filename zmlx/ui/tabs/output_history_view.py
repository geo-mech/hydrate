"""控制台输出历史浏览器.

Modified by Claude, 2026-08-12
"""

import glob
import os

from zmlx.system import app_data
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

import os

from zmlx.io.text import read_text
from zmlx.ui.CodeEdit import CodeEdit
from zmlx.ui.Qt import is_PyQt6

if is_PyQt6:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QListWidget, QListWidgetItem
    )
    from PyQt6.QtCore import Qt, QFileInfo, QDateTime
else:
    from PyQt5.QtWidgets import (
        QWidget, QHBoxLayout, QListWidget, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, QFileInfo, QDateTime

import glob

ITEM_DATA_ROLE = Qt.ItemDataRole.UserRole if is_PyQt6 else Qt.UserRole


class CodeHistoryViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)

        # 左侧文件列表（保持与之前相同）
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.show_file_content)
        self.main_layout.addWidget(self.file_list, stretch=2)

        # 右侧代码编辑器
        self.code_edit = CodeEdit()
        self.main_layout.addWidget(self.code_edit, stretch=5)

        self.clear_display()

    def clear_display(self):
        self.file_list.clear()
        self.code_edit.clear()

    def set_folder(self, folder):
        """设置目标文件夹，自动过滤.py文件"""
        self.current_folder = os.path.abspath(folder)
        self.refresh_file_list()

        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.show_file_content(self.file_list.currentItem())

    def refresh_file_list(self):
        """刷新.py文件列表"""
        self.file_list.clear()

        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        pattern = os.path.join(self.current_folder, "*.py")
        files = [(f, QFileInfo(f).lastModified()) for f in glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            time_str = QDateTime.toString(mtime, "yyyy-MM-dd hh:mm")
            text = read_text(file_path, encoding='utf-8')
            text = text[:300]
            item = QListWidgetItem(
                f"\n{idx:02d}.\t{time_str}\n\n{text}\n--------------\n\n")
            item.setData(ITEM_DATA_ROLE, file_path)
            self.file_list.addItem(item)

    def show_file_content(self, item):
        """使用CodeEdit打开文件"""
        file_path = item.data(ITEM_DATA_ROLE)
        self.code_edit.open(file_path)  # 依赖CodeEdit自身的错误处理

    def console_exec(self):
        self.code_edit.console_exec()

    def get_start_code(self):
        return f"""gui.show_code_history(r'{self.current_folder}')"""

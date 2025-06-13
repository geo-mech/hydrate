import os
import sys

from zml import app_data
from zmlx.ui.pyqt import is_pyqt6
from zmlx.ui.widget.console import ConsoleOutput

if is_pyqt6:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QListWidget, QListWidgetItem
    )
    from PyQt6.QtCore import Qt, QFileInfo, QDateTime
else:
    from PyQt5.QtWidgets import (
        QWidget, QHBoxLayout, QListWidget, QTextEdit, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, QFileInfo, QDateTime

import glob

ITEM_DATA_ROLE = Qt.ItemDataRole.UserRole if is_pyqt6 else Qt.UserRole


class OutputHistoryViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder = None
        self.current_ext = None
        self.init_ui()
        self.set_folder()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)

        # 左侧文件列表
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.show_file_content)
        self.main_layout.addWidget(self.file_list, stretch=2)

        # 右侧文本显示
        self.text_view = ConsoleOutput(self)
        self.main_layout.addWidget(self.text_view, stretch=5)

        self.clear_display()

    def clear_display(self):
        self.file_list.clear()
        self.text_view.load_text('')

    def set_folder(self, folder=None):
        if folder is None:
            folder = app_data.root('output_history')

        if folder is not None:
            self.current_folder = folder
            self.current_ext = 'txt'
            self.refresh_file_list()

            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(0)
                self.show_file_content(self.file_list.currentItem())

    def refresh_file_list(self):
        self.file_list.clear()

        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        pattern = os.path.join(self.current_folder, f"*.{self.current_ext}")
        files = [(f, QFileInfo(f).lastModified()) for f in glob.glob(pattern)]
        sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

        for idx, (file_path, mtime) in enumerate(sorted_files, 1):
            filename = os.path.basename(file_path)
            time_str = QDateTime.toString(mtime, "yyyy-MM-dd hh:mm")  # 时间格式保持兼容

            item = QListWidgetItem(f"{idx:02d}. {time_str}: \n\t{filename}\n")
            item.setData(ITEM_DATA_ROLE, file_path)  # 使用兼容的角色类型
            self.file_list.addItem(item)

    def show_file_content(self, item):
        file_path = item.data(ITEM_DATA_ROLE)
        try:
            self.text_view.load_text(file_path)
        except Exception as e:
            self.text_view.setText(
                f"读取文件错误：{str(e)}. file_path={file_path}")

    @staticmethod
    def get_start_code():
        return """gui.trigger('show_output_history')"""


# 使用示例
if __name__ == '__main__':
    if is_pyqt6:
        from PyQt6.QtWidgets import QApplication
    else:
        from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    viewer = OutputHistoryViewer()
    viewer.show()
    sys.exit(app.exec())

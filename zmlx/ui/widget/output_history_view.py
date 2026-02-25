import glob
import os

from zml import app_data
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widget.text_browser import TextBrowser


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
        files = [(f, QtCore.QFileInfo(f).lastModified()) for f in
                 glob.glob(pattern)]
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
            with open(file_path, "r") as f:
                text = f.read()
                self.text_view.setText(text)
        except Exception as err:
            self.text_view.setText(
                f"读取文件错误：{str(err)}. file_path={file_path}")

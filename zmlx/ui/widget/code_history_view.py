import glob
import os

from zml import read_text
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widget.code_edit import CodeEdit


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

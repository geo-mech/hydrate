import os

from zml import app_data
from zmlx import get_path
from zmlx.ui.Qt import QtWidgets
from zmlx.ui.alg.code_config import code_config


class DemoWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(DemoWidget, self).__init__(parent)
        self.__data = []
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_clicked)
        self.refresh()

    def refresh(self):
        folder = get_path('demo')
        if not os.path.isdir(folder):
            self.clear()
            return

        self.__data = [['关于', folder,
                        f'注意，请单击以下项目以打开，之后点击任务栏上的<运行>按钮来运行. 可以在文件夹<{folder}>找到这些示例'], ]
        for name in os.listdir(folder):
            if name == '__init__.py':
                continue

            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue

            ext = os.path.splitext(path)[-1]
            if ext != '.py':
                continue

            cfg = code_config(path=path, encoding='utf-8')
            desc = cfg.get('desc', '')

            if len(desc) > 0:
                self.__data.append([name, path, desc])

        if len(self.__data) == 0:
            self.clear()
            return

        self.setRowCount(len(self.__data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '说明'])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for row_id in range(len(self.__data)):
            try:
                name, path, desc = self.__data[row_id]
                self.setItem(row_id, 0, QtWidgets.QTableWidgetItem(name))
                self.setItem(row_id, 1, QtWidgets.QTableWidgetItem(desc))
            except:
                for col_id in range(2):
                    self.setItem(row_id, col_id, QtWidgets.QTableWidgetItem(''))

    def item_clicked(self, index):
        row_id = index.row()
        if row_id >= len(self.__data):
            return

        try:
            name, path, desc = self.__data[row_id]
            if os.path.isfile(path):
                ext = os.path.splitext(path)[-1]
                if ext is not None:
                    if ext.lower() == '.py' or ext.lower() == '.pyw':
                        window = app_data.get('main_window')
                        if window is not None:
                            window.open_code(path)

            if os.path.isdir(path):
                os.startfile(path)
        except:
            pass

    @staticmethod
    def get_start_code():
        return """gui.trigger('demo')"""

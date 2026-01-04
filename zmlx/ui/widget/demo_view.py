import os

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets


class DemoView(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(DemoView, self).__init__(parent)
        self.__data = []
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_clicked)
        self.refresh()

    def refresh(self):
        from zmlx.demo.list_demo_files import list_demo_files
        from zmlx.demo.path import get_path
        folder = get_path()
        self.__data = [['demo根目录', folder, folder], ]
        for path, desc in list_demo_files():
            self.__data.append([os.path.relpath(path, folder), path, desc])

        if len(self.__data) == 0:
            self.clear()
            return

        self.setRowCount(len(self.__data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目 (点击打开)', '说明 (点击运行)'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for row_id in range(len(self.__data)):
            try:
                name, path, desc = self.__data[row_id]
                self.setItem(
                    row_id, 0, QtWidgets.QTableWidgetItem(name))
                self.setItem(
                    row_id, 1, QtWidgets.QTableWidgetItem(desc))
            except Exception as err:
                print(err)
                for col_id in range(2):
                    self.setItem(
                        row_id, col_id, QtWidgets.QTableWidgetItem(''))

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
                        if index.column() == 0:
                            gui.open_code(path)
                        else:
                            gui.exec_file(path)
            if os.path.isdir(path):
                os.startfile(path)
        except Exception as err:
            print(err)

import os
import sys
import time

from zmlx.alg.fsize2str import fsize2str
from zmlx.ui.Qt import QtWidgets


class FileViewer(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(FileViewer, self).__init__(parent)
        self.__data = []
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.clicked.connect(self.item_clicked)
        self.doubleClicked.connect(self.item_double_clicked)
        self.refresh()

    def get_data(self):
        return self.__data

    def set_data(self, value):
        assert isinstance(value, list) or isinstance(value, tuple)
        self.__data = value
        self.refresh()

    def refresh(self):
        self.setRowCount(len(self.__data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])

        for irow in range(len(self.__data)):
            try:
                name, path = self.__data[irow]
                ty = ''
                sz = ''
                mt = ''
                if os.path.isfile(path):
                    ty = '文件'
                    sz = f'{fsize2str(os.path.getsize(path))}'
                    mt = f'{time.ctime(os.path.getmtime(path))}'
                if os.path.isdir(path):
                    ty = '文件夹'
                items = [name, ty, sz, mt]
                for icol in range(4):
                    self.setItem(irow, icol, QtWidgets.QTableWidgetItem(items[icol]))
            except:
                for icol in range(4):
                    self.setItem(irow, icol, QtWidgets.QTableWidgetItem(''))

    def item_clicked(self, index):
        if index.column() != 0:
            return

        irow = index.row()
        if irow >= len(self.__data):
            return

        try:
            name, path = self.__data[irow]
            if os.path.isfile(path):
                ext = os.path.splitext(path)[-1]
                if ext is not None:
                    if ext.lower() == '.py' or ext.lower() == '.pyw':
                        from zmlx.ui.GuiBuffer import gui
                        gui.open_code(path)
        except:
            pass

    def item_double_clicked(self, index):
        if index.column() != 0:
            return

        irow = index.row()
        if irow >= len(self.__data):
            return

        try:
            name, path = self.__data[irow]
            from zmlx.ui.GuiBuffer import gui
            gui.open_file(path)
        except:
            pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = FileViewer()
    w.show()
    sys.exit(app.exec_())

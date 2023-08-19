import os
import sys

from PyQt5 import QtWidgets, QtCore
from zmlx.alg.fsize2str import fsize2str
from zmlx.alg.clamp import clamp
from zml import gui
import time
import timeit


class FileWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(FileWidget, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.folder = None
        self.clicked.connect(self.item_clicked)
        self.doubleClicked.connect(self.item_double_clicked)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def set_dir(self, folder=None):
        if folder is None:
            folder = os.getcwd()
        self.clear()
        self.folder = folder
        assert isinstance(self.folder, str)

        if os.path.isdir(self.folder):
            data = [['..', '文件夹', '', ''], ]
            for name in os.listdir(self.folder):

                path = os.path.join(self.folder, name)
                if os.path.isfile(path):
                    data.append([name, '文件', fsize2str(os.path.getsize(path)),
                                 f'{time.ctime(os.path.getmtime(path))}'])
                    continue

                if os.path.isdir(path):
                    data.append([name, '文件夹', '', ''])
                    continue

            self.setRowCount(len(data))
            self.setColumnCount(4)
            self.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])

            for irow in range(len(data)):
                for icol in range(4):
                    self.setItem(irow, icol, QtWidgets.QTableWidgetItem(data[irow][icol]))

    def refresh(self):
        cpu_t = timeit.default_timer()
        self.set_dir(self.folder)
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

    def item_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(self.folder)
        else:
            fpath = os.path.join(self.folder, text)

        if os.path.isfile(fpath):
            ext = os.path.splitext(fpath)[-1]
            if ext is not None:
                if ext.lower() == '.py' or ext.lower() == '.pyw':
                    gui.open_code(fpath, False)

    def item_double_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(self.folder)
        else:
            fpath = os.path.join(self.folder, text)
        gui.open_file(fpath)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = FileWidget()
    w.show()
    sys.exit(app.exec_())

import os
import time
import timeit

from zml import app_data
from zmlx.alg.base import fsize2str, clamp
from zmlx.ui.pyqt import QtWidgets, QtCore


class CwdViewer(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(CwdViewer, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.clicked.connect(self.item_clicked)
        self.doubleClicked.connect(self.item_double_clicked)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def __refresh(self):
        folder = os.getcwd()
        data = [['..', '文件夹', '', ''], ]
        try:
            names = os.listdir(folder)
        except:
            names = []
        for name in names:
            path = os.path.join(folder, name)
            try:
                if os.path.isfile(path):
                    data.append([name, '文件', fsize2str(os.path.getsize(path)),
                                 f'{time.ctime(os.path.getmtime(path))}'])
                    continue

                if os.path.isdir(path):
                    data.append([name, '文件夹', '', ''])
                    continue
            except:
                pass
        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for irow in range(len(data)):
            for icol in range(4):
                self.setItem(irow, icol,
                             QtWidgets.QTableWidgetItem(data[irow][icol]))

    def refresh(self):
        cpu_t = timeit.default_timer()
        #
        try:
            self.__refresh()
        except:
            self.clear()
        #
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

    def item_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)

        if os.path.isfile(fpath):
            ext = os.path.splitext(fpath)[-1]
            if ext is not None:
                if ext.lower() == '.py' or ext.lower() == '.pyw':
                    window = app_data.get('main_window')
                    if window is not None:
                        window.open_code(fpath)

    def item_double_clicked(self, index):
        if index.column() != 0:
            return
        item = self.item(index.row(), index.column())
        text = item.text()
        if text == '..':
            fpath = os.path.dirname(os.getcwd())
        else:
            fpath = os.path.join(os.getcwd(), text)
        window = app_data.get('main_window')
        if window is not None:
            window.open_file(fpath)

    @staticmethod
    def get_start_code():
        return """gui.trigger('view_cwd')"""

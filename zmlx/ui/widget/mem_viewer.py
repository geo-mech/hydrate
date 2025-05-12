import timeit

from zml import app_data
from zmlx.alg.utils import clamp
from zmlx.ui.pyqt import QtWidgets, QtCore


class MemViewer(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # 添加需要忽略的键值(都显示出来会使得太乱了)
        try:
            space = {}
            exec('from zmlx import *', space)
            self.names_ignore = set(space.keys())
        except:
            self.names_ignore = set()

        for item in ['MemViewer', 'PgConsole', 'main_window', 'qt_widget',
                     'set_md', 'widget', 'DemoWidget']:
            self.names_ignore.add(item)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def __refresh(self):
        data = []
        for key, value in app_data.space.items():
            if len(key) > 2:
                if key[0:2] == '__':
                    continue
            if key in self.names_ignore:
                continue
            data.append([key, f'{value}', f'{type(value)}'])

        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['名称', '值', '类型'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for irow in range(len(data)):
            for icol in range(3):
                self.setItem(irow, icol,
                             QtWidgets.QTableWidgetItem(data[irow][icol]))

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return
        cpu_t = timeit.default_timer()
        try:
            self.__refresh()
        except:
            self.clear()
        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

    @staticmethod
    def get_start_code():
        return """gui.trigger('memory')"""

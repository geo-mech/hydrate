from PyQt5 import QtWidgets, QtCore
from zml import app_data
from zmlx.alg.clamp import clamp
import timeit


class MemViewer(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return

        cpu_t = timeit.default_timer()
        data = []
        for key, value in app_data.space.items():
            data.append([key, f'{value}', f'{type(value)}'])

        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['名称', '值', '类型'])

        for irow in range(len(data)):
            for icol in range(3):
                self.setItem(irow, icol, QtWidgets.QTableWidgetItem(data[irow][icol]))

        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

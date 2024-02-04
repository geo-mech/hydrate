import timeit

from zmlx.alg.clamp import clamp
from zmlx.alg.time2str import time2str
from zmlx.filesys.make_parent import make_parent
from zmlx.ui.Qt import QtWidgets, QtCore
from zmlx.utility.Timer import timer


class TimerViewer(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self, '导出Timer',
                                                         '', f'Text File(*.txt)')
        with open(make_parent(fpath), 'w', encoding='utf-8') as file:
            for key, val in timer.key2nt.items():
                n, t = val
                file.write(f'{key}\t{n}\t{t}\n')

    def refresh(self):
        """
        更新
        """
        if not self.isVisible():
            return

        cpu_t = timeit.default_timer()

        data = []
        for key, nt in timer.key2nt.items():
            n, t = nt
            data.append([f'{key}', f'{n}', time2str(t), time2str(t / n)])

        self.setRowCount(len(data))
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['名称', '调用次数', '总耗时', '单次耗时'])

        for irow in range(len(data)):
            for icol in range(4):
                self.setItem(irow, icol, QtWidgets.QTableWidgetItem(data[irow][icol]))

        cpu_t = timeit.default_timer() - cpu_t
        msec = clamp(int(cpu_t * 200 / 0.001), 200, 8000)
        self.timer.setInterval(msec)

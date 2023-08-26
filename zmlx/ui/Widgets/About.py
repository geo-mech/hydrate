import sys
from PyQt5 import QtWidgets, QtCore
from zml import *
from zmlx.alg.sys import get_latest_version


class About(QtWidgets.QTableWidget):

    sigRefresh = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(About, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.sigRefresh.connect(self.refresh)
        self.sigRefresh.emit()

    def refresh(self):
        while core.has_log():
            core.pop_log()
        latest_version = get_latest_version()
        summary = lic.summary
        if summary is None:
            while core.has_log():
                print(core.pop_log())
            print('\n\n')
        data = [['About', about()],
                ['当前版本', f'{version}'],
                ['最新版本', f'{latest_version}'],
                ['是否需要更新', '是' if version < latest_version else '否'],
                ['网址', 'https://gitee.com/geomech/hydrate'],
                ['作者', 'Zhang Zhaobin'],
                ['单位', '中国科学院地质与地球物理研究所'],
                ['授权情况', f'{summary}'],
                ]
        self.setRowCount(len(data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '值'])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

        for irow in range(len(data)):
            for icol in range(2):
                self.setItem(irow, icol, QtWidgets.QTableWidgetItem(data[irow][icol]))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = About()
    w.show()
    sys.exit(app.exec_())




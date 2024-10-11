import sys

from zml import core, lic, get_dir
from zmlx.ui.Qt import QtWidgets, QtCore


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
        summary = lic.summary
        if summary is None:
            while core.has_log():
                print(core.pop_log())
            print('\n\n')
        data = [['安装路径', f'{get_dir()}'],
                ['运行环境', f'Python {sys.version}'],
                ['当前版本', f'{core.time_compile}; {core.compiler}'],
                ['网址', 'https://gitee.com/geomech/hydrate'],
                ['作者', 'Zhang Zhaobin'],
                ['单位', '中国科学院地质与地球物理研究所'],
                ['联系邮箱', 'zhangzhaobin@mail.iggcas.ac.cn'],
                ['本机授权情况', f'{summary}'],
                ]
        self.setRowCount(len(data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '值'])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(2):
                self.setItem(i_row, i_col, QtWidgets.QTableWidgetItem(data[i_row][i_col]))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = About()
    w.show()
    sys.exit(app.exec_())

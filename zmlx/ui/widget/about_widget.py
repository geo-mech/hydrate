import sys

from zml import core, lic, get_dir
from zmlx.ui.pyqt import QtWidgets, qt_name, QWebEngineView


class About(QtWidgets.QTableWidget):

    def __init__(self, parent=None, lic_desc=None):
        super(About, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)

        data = [['安装路径', f'{get_dir()}'],
                ['当前版本', f'{core.time_compile}; {core.compiler}'],
                ['授权情况', f'{lic_desc}'],
                ['Python解释器', sys.executable],
                ['Python版本', sys.version],
                ['Qt版本', qt_name],
                ['QWebEngineView已安装',
                 'Yes' if QWebEngineView is not None else 'No'],
                ['网址', 'https://gitee.com/geomech/hydrate'],
                ['通讯作者', '张召彬'],
                ['单位', '中国科学院地质与地球物理研究所'],
                ['联系邮箱', 'zhangzhaobin@mail.iggcas.ac.cn'],
                ['管理员权限', 'Yes' if lic.is_admin else 'No'],
                ['硬件码', f'{lic.usb_serial}'],
                ]
        self.setRowCount(len(data))
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['项目', '值'])
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        for i_row in range(len(data)):
            for i_col in range(2):
                self.setItem(
                    i_row, i_col,
                    QtWidgets.QTableWidgetItem(data[i_row][i_col]))

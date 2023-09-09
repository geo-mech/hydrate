# 导入matplotlib模块并使用Qt5Agg
import os

import matplotlib

matplotlib.use('Qt5Agg')
# 使用 matplotlib中的FigureCanvas (在使用 Qt5 Backends中 FigureCanvas继承自QtWidgets.QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from zmlx.ui.Qt import QtWidgets, QtCore, QtGui
import matplotlib.pyplot as plt


# 关于matplotlib中的Figure和Axis的概念，参考：
# https://blog.csdn.net/u010916338/article/details/105645599

class MatplotWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MatplotWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.__figure = plt.figure()
        self.__canvas = FigureCanvas(self.__figure)
        layout.addWidget(self.__canvas)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.create_rightmenu)

    def draw(self):
        self.__canvas.draw()

    def savefig(self, *args, **kwargs):
        self.__figure.savefig(*args, **kwargs)

    def savefig_by_dlg(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption="请选择保存路径",
                                                         directory=os.getcwd(),
                                                         filter='jpg图片(*.jpg);;所有文件(*.*)')
        if fpath is not None and len(fpath) > 0:
            self.savefig(fname=fpath, dpi=300)

    def export_data(self):
        self.savefig_by_dlg()

    @property
    def figure(self):
        return self.__figure

    @property
    def canvas(self):
        return self.__canvas

    def create_rightmenu(self):
        self.rightmenu = QtWidgets.QMenu(self)

        action = QtWidgets.QAction(self)
        action.setText('保存图片')
        action.triggered.connect(self.savefig_by_dlg)
        self.rightmenu.addAction(action)

        self.rightmenu.popup(QtGui.QCursor.pos())

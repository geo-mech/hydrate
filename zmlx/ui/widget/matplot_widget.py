# 导入matplotlib模块并使用Qt5Agg
import os

import matplotlib

has_Agg = False

try:
    if not has_Agg:
        matplotlib.use('QtAgg')
        has_Agg = True
except:
    pass

try:
    if not has_Agg:
        matplotlib.use('Qt5Agg')
        has_Agg = True
except:
    pass

# 使用 matplotlib中的FigureCanvas (在使用 Qt5 Backends中 FigureCanvas继承自QtWidgets.QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from zmlx.ui.pyqt import QtWidgets
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
        self.__right_menu = None
        layout.addWidget(self.__canvas)

    def draw(self):
        self.__canvas.draw()

    def savefig(self, *args, **kwargs):
        self.__figure.savefig(*args, **kwargs)

    def savefig_by_dlg(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                         caption="请选择保存路径",
                                                         directory=os.getcwd(),
                                                         filter='jpg图片(*.jpg);;所有文件(*.*)')
        if fpath is not None and len(fpath) > 0:
            from zmlx.io.env import plt_export_dpi
            self.savefig(fname=fpath, dpi=plt_export_dpi.get_value())

    def export_plt_figure(self):  # 接菜单命令
        self.savefig_by_dlg()

    @property
    def figure(self):
        return self.__figure

    @property
    def canvas(self):
        return self.__canvas

    def contextMenuEvent(self, event):  # 右键菜单
        from zmlx.ui.main_window import get_window
        window = get_window()
        menu = QtWidgets.QMenu(self)
        menu.addAction(window.get_action('export_plt_figure'))
        menu.addAction(window.get_action('set_plt_export_dpi'))
        menu.exec(event.globalPos())

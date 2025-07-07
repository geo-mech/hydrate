import os
import sys
import warnings

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets

try:
    import matplotlib
    import matplotlib.pyplot as plt

    # 设置Matplotlib支持中文显示
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei',
                                              'SimSun']  # 指定字体
    matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except ImportError:
    matplotlib = None
    plt = None
    print(f'Error when import matplotlib')

for backend in ['QtAgg', 'Qt5Agg']:
    try:
        matplotlib.use(backend)
        break
    except Exception as err:
        print(f'Error (when use backend {backend}): {err}')


class MatplotWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        """
        初始化
        """
        super(MatplotWidget, self).__init__(parent)
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 2025-7-5
        self.setLayout(layout)
        self.__figure = plt.figure()
        self.__canvas = FigureCanvasQTAgg(self.__figure)
        self.__right_menu = None
        layout.addWidget(self.__canvas)

    def draw(self):
        """
        绘图
        """
        self.__canvas.draw()

    def savefig(self, *args, **kwargs):
        """
        保存图片
        """
        self.__figure.savefig(*args, **kwargs)

    def savefig_by_dlg(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
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
        if gui.exists():
            menu = QtWidgets.QMenu(self)
            menu.addAction(gui.get_action('set_plt_export_dpi'))
            menu.addAction(gui.get_action('export_plt_figure'))
            menu.exec(event.globalPos())

    def plot_on_figure(self, on_figure):
        """
        在控件上面绘图。其中on_figure是回调函数，接受一个Figure类型的参数。
        注意：
            如果多次绘图，建议在绘图之前先调用 figure.clear()
        """
        try:
            on_figure(self.figure)
            self.draw()
        except Exception as e:
            warnings.warn(f'meet exception <{e}> when run <{on_figure}>')


def test():
    app = QtWidgets.QApplication(sys.argv)
    w = MatplotWidget()

    def on_figure(fig):
        ax = fig.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        ax.plot([1, 2, 3], [1, 3, 8])

    w.plot_on_figure(on_figure)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()

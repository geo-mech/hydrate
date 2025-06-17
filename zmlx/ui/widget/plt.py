# 导入matplotlib模块并使用Qt5Agg
import os
import sys
import warnings

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

from zmlx.ui.pyqt import QtWidgets, QAction
from zmlx.ui.settings import load_icon
import matplotlib.pyplot as plt


# 关于matplotlib中的Figure和Axis的概念，参考：
# https://blog.csdn.net/u010916338/article/details/105645599

class MatplotWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MatplotWidget, self).__init__(parent)
        # 使用 matplotlib中的FigureCanvas (在使用 Qt5 Backends中 FigureCanvas继承自QtWidgets.QWidget)
        from matplotlib.backends.backend_qt5agg import \
            FigureCanvasQTAgg as FigureCanvas
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
        from zmlx.ui.main_window import get_window
        window = get_window()
        menu = QtWidgets.QMenu(self)
        action = QAction(self)
        action.setText('导出')
        action.setIcon(load_icon('matplotlib'))
        action.triggered.connect(self.export_plt_figure)
        menu.addAction(action)
        if window is not None:
            action = window.get_action('set_plt_export_dpi')
            if action is not None:
                menu.addAction(action)
        menu.exec(event.globalPos())

    def del_all_axes(self):
        """
        删除所有的axes
        """
        fig = self.figure
        for ax in fig.get_axes():
            fig.delaxes(ax)

    def plot_on_figure(self, on_figure):
        """
        在控件上面绘图
        """
        try:
            on_figure(self.figure)
            self.draw()
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when run <{on_figure}>')

    def plot_on_axes(
            self, on_axes, dim=2, xlabel=None, ylabel=None, zlabel=None,
            title=None, aspect=None,
            xlim=None, ylim=None, zlim=None,
            show_legend=False, grid=None, axis=None,
            clear=True):
        """
        绘制图形。使用在坐标轴上绘图的回调函数.

        Args:
            clear: 是否清除现有的坐标轴
            on_axes: 在坐标轴上ax上绘图的回调函数，函数的原型为:
                def on_axes(ax):
                    ...
                    其中ax为matplotlib的axes实例，会根据dim的取值而创建并传递给on_axes。
            dim: 维度，2或者3 (创建的Axes的类型会不同)
            xlabel: x轴标签，当非None的时候，会设置axes.set_xlabel(xlabel) (默认为None)
            ylabel: y轴标签，当非None的时候，会设置axes.set_ylabel(ylabel) (默认为None)
            zlabel: z轴标签，当非None的时候，会设置axes.set_zlabel(zlabel) (默认为None)
            title: 标题，当非None的时候，会设置axes.set_title(title) (默认为None)
            aspect: 坐标的比例，当非None的时候，会设置axes.set_aspect(aspect) (默认为None)
            zlim: z轴的范围，当非None的时候，会设置axes.set_zlim(zlim) (默认为None)
            ylim: y轴的范围，当非None的时候，会设置axes.set_ylim(ylim) (默认为None)
            xlim: x轴的范围，当非None的时候，会设置axes.set_xlim(xlim) (默认为None)
            axis: 设置axis
            grid: 是否显示网格线
            show_legend: 是否显示图例
        Returns:
            None
        """

        def on_figure(fig):
            assert dim == 2 or dim == 3, f'The dim must be 2 or 3 while got {dim}'
            if dim == 2:
                ax = fig.subplots()
            else:
                ax = fig.add_subplot(111, projection='3d')
            try:
                on_axes(ax)
            except Exception as e:
                print(e)

            if xlabel is not None:
                ax.set_xlabel(xlabel)
            if ylabel is not None:
                ax.set_ylabel(ylabel)
            if zlabel is not None and dim == 3:
                ax.set_zlabel(zlabel)
            if xlim is not None:
                ax.set_xlim(xlim)
            if ylim is not None:
                ax.set_ylim(ylim)
            if zlim is not None and dim == 3:
                ax.set_zlim(zlim)
            if title is not None:
                ax.set_title(title)
            if aspect is not None:
                ax.set_aspect(aspect)
            if show_legend:
                ax.legend()
            if grid is not None:
                ax.grid(grid)
            if axis is not None:
                ax.axis(axis)

        if clear:
            self.del_all_axes()
        self.plot_on_figure(on_figure)


def main():
    app = QtWidgets.QApplication(sys.argv)
    editor = MatplotWidget()
    def on_axes(ax):
        ax.plot([1, 2, 3], [4, 5, 6])
    editor.plot_on_axes(on_axes, xlabel='x', ylabel='y',
                 title='title', clear=True)
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

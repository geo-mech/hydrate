import datetime
import os
import sys
import warnings

from zml import in_windows, in_linux, in_macos, make_parent
from zmlx.io import opath
from zmlx.io.env import plt_export_dpi
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtWidgets, QtGui


def set_chinese_font():
    try:  # 设置Matplotlib支持中文显示
        import matplotlib
        if in_windows():
            matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei',
                                                      'SimSun']  # 指定字体
            matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        elif in_linux():
            # 使用文泉驿字体作为首选
            matplotlib.rcParams['font.sans-serif'] = [
                'WenQuanYi Micro Hei',
                'Noto Sans CJK SC',
                'Droid Sans Fallback',
                'AR PL UMing CN',
                'sans-serif'
            ]
            matplotlib.rcParams['axes.unicode_minus'] = False
            cache_dir = matplotlib.get_cachedir()
            cache_files = ['fontlist-v330.json', 'fontlist-v310.json']

            for cf in cache_files:
                cache_path = os.path.join(cache_dir, cf)
                if os.path.exists(cache_path):
                    try:
                        os.unlink(cache_path)
                    except:
                        print(f'无法删除字体缓存 {cache_path}')
                        pass
        elif in_macos():
            # macOS 通常使用 .ttc 字体文件
            matplotlib.rcParams['font.sans-serif'] = [
                'PingFang SC',  # 苹方
                'Hiragino Sans GB',  # 冬青黑体
                'STHeiti',  # 华文黑体
                'Apple SD Gothic Neo'
            ]
            matplotlib.rcParams['axes.unicode_minus'] = False
    except Exception as font_err:
        print(f'Error when set font: {font_err}')


class MatplotWidget(QtWidgets.QWidget):
    support_sub_menu = True  # 支持子菜单(since 2026-1-5)

    def __init__(self, parent=None):
        """
        初始化
        """
        super(MatplotWidget, self).__init__(parent)
        set_chinese_font()
        for backend in ['QtAgg', 'Qt5Agg']:
            try:
                import matplotlib
                matplotlib.use(backend)
                break
            except Exception as err:
                print(f'Error (when use backend {backend}): {err}')
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        import matplotlib.pyplot as plt

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 2025-7-5
        self.setLayout(layout)
        self.__figure = plt.figure()
        self.__canvas = FigureCanvasQTAgg(self.__figure)
        self.context_actions = []  # 额外的右键菜单
        layout.addWidget(self.__canvas)

        now = datetime.datetime.now()
        name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}"
        self.__folder_save = opath('matplotlib', name)
        self.__time_save = None

        # 设置主题
        bg_color = self.palette().color(QtGui.QPalette.ColorRole.Window)
        if bg_color.lightness() < 128:  # 处于暗色主题
            # 应用暗色主题
            plt.style.use('dark_background')
            # 额外设置，确保所有元素适配暗色
            self.figure.patch.set_facecolor('#1e1e1e')  # 设置画布背景色

    def set_save_folder(self, folder):
        self.__folder_save = folder

    def draw(self):
        """
        绘图
        """
        self.__canvas.draw()
        if self.__folder_save is not None:  # 尝试将绘图保存为图片(使用当前的时间)
            now = datetime.datetime.now()
            if self.__time_save is not None:
                if abs(now - self.__time_save).total_seconds() < 5.0:
                    return
            name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}.png"
            path = make_parent(os.path.join(self.__folder_save, name))
            self.savefig(fname=path, dpi=plt_export_dpi.get_value())
            self.__time_save = now  # 记录时间

    def savefig(self, *args, **kwargs):
        """
        保存图片
        """
        try:
            self.__figure.savefig(*args, **kwargs)
        except Exception as e:
            print(f'Error when save figure: {e}')

    def savefig_by_dlg(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="请选择保存路径",
            directory=os.getcwd(),
            filter='Jpg图片(*.jpg);;Png图片(*.png);;所有文件(*.*)')
        if fpath is not None and len(fpath) > 0:
            self.savefig(
                fname=fpath, dpi=plt_export_dpi.get_value())

    def export_data(self):  # 接菜单命令
        self.savefig_by_dlg()

    @property
    def figure(self):
        return self.__figure

    @property
    def canvas(self):
        return self.__canvas

    @staticmethod
    def set_plt_export_dpi():
        warnings.warn(
            'set_plt_export_dpi is deprecated, use set_plt_export_dpi in zmlx.ui.alg',
            DeprecationWarning, stacklevel=2
        )
        from zmlx.ui.alg import set_plt_export_dpi as impl
        impl()

    def get_context_menu(self):
        from zmlx.ui.alg import set_plt_export_dpi
        menu = QtWidgets.QMenu(self)
        menu.addAction(
            create_action(
                self, '设置导出图的DPI', icon='set',
                slot=set_plt_export_dpi))
        menu.addAction(
            create_action(
                self, '导出图', icon='export',
                slot=self.savefig_by_dlg))

        if self.__folder_save is not None:  # 打开自动保存目录
            if isinstance(self.__folder_save, str):
                def open_dir():
                    os.startfile(self.__folder_save)

                menu.addAction(
                    create_action(
                        self, '打开图片保存目录',
                        slot=open_dir))

        # 尝试获得提前存储的额外的Action
        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                if isinstance(action, dict):
                    name = action.get('name', None)
                    if name is not None:
                        sub_menu = menu.addMenu(name)
                        assert isinstance(sub_menu, QtWidgets.QMenu)
                        for item in action.get('items', []):
                            sub_menu.addAction(item)
                elif isinstance(action, str):
                    if action == '':
                        menu.addSeparator()
                else:
                    menu.addAction(action)

        return menu

    def contextMenuEvent(self, event):  # 右键菜单
        self.get_context_menu().exec(event.globalPos())

    def plot_on_figure(self, on_figure):
        """
        在控件上面绘图。其中on_figure是回调函数，接受一个Figure类型的参数。
        注意：
            如果多次绘图，建议在绘图之前先调用 figure.clear()
        """
        try:
            on_figure(self.figure)
        except Exception as e:
            warnings.warn(f'meet exception <{e}> when run <{on_figure}>')
        try:
            self.draw()
        except Exception as e:
            warnings.warn(f'meet exception <{e}> when run <{self.draw}>')


def test():
    app = QtWidgets.QApplication(sys.argv)
    w = MatplotWidget()

    def on_figure(fig):
        ax = fig.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        ax.plot([1, 2, 3], [1, 3, 8])
        ax.set_xlabel('x坐标轴')
        ax.set_ylabel('y坐标轴')

    w.plot_on_figure(on_figure)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()

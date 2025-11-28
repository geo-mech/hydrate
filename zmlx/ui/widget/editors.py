import os

try:
    import numpy as np
except ImportError:
    np = None

from zml import Interp1, Interp2
from zmlx.alg.numpy_algs import text_to_numpy, numpy_to_text
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widget import MatplotWidget
from zmlx.plt.cmap import get_cm


class TextEdit(QtWidgets.QTextEdit):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setFontFamily("Courier New")  # 使用等宽字体
        self.textChanged.connect(self.sig_changed.emit)

    def set_data(self, data):
        self.setText(str(data))

    def get_data(self):
        return self.toPlainText()


class ArrayTextEdit(TextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_data(self):
        return text_to_numpy(self.toPlainText())

    def set_data(self, data):
        self.setText(numpy_to_text(data, fmt='%.05e'))


class NumpyAlgs:
    @staticmethod
    def modify_array_by_text(data, parent=None):
        """
        编辑矩阵文本表示
        """
        if data is None:
            return None
        text, ok = QtWidgets.QInputDialog.getMultiLineText(
            parent, "编辑数组文本", "请输入数组文本：",
            numpy_to_text(data, fmt='%.05e')
        )
        if ok:
            try:
                return text_to_numpy(text)
            except Exception as e:
                print(f"数据解析失败: {str(e)}")
        return None

    @staticmethod
    def save(data, filename):
        """保存到文件"""
        if filename.endswith('.npy'):
            np.save(filename, data)
            return
        if filename.endswith('.txt'):
            np.savetxt(filename, data)
            return

    @staticmethod
    def load(filename):
        """从文件加载"""
        if filename.endswith('.npy'):
            return np.load(filename)
        if filename.endswith('.txt'):
            return np.loadtxt(filename)
        else:
            return None


class ArrayEdit(QtWidgets.QTextBrowser):
    """
    Numpy矩阵的显示和编辑控件
    """
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setFontFamily("Courier New")  # 使用等宽字体
        self.data = None
        self.set_data(np.array([]))  # 初始化显示
        self.context_actions = [
            create_action(self, "使用文本编辑", slot=self._edit),
            create_action(self, "从文件(npy/txt)导入", slot=self._load),
        ]

    def set_data(self, data):
        """设置要显示的数据"""
        if isinstance(data, np.ndarray):
            self.data = data
            shape = data.shape
            text = f"Shape: {shape} | Dim: {len(shape)}D\n\n{self.data}"
            self.setPlainText(text)
        else:
            self.setPlainText(str(self.data))

    def get_data(self):
        return self.data

    def contextMenuEvent(self, event):
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = QtWidgets.QMenu(self)
        for action in self.context_actions:
            menu.addAction(action)
        return menu

    def _edit(self):
        def set_data(data):
            self.set_data(data)
            self.sig_changed.emit()

        gui.edit_in_tab(
            widget_type=ArrayTextEdit, set_data=set_data,
            get_data=self.get_data,
            caption=f'Edit: {id(self)}')

    def _load(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '选择numpy文件', os.getcwd(),
            'Numpy Array(*.npy *.txt)'
        )
        if fname:
            data = NumpyAlgs.load(fname)
            if data is not None:
                self.set_data(data)
                self.sig_changed.emit()

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            'Numpy矩阵', ['.npy', '.txt'], name='numpy_array',
            save=NumpyAlgs.save,
            load=NumpyAlgs.load,
            init=lambda: np.array([]),
            widget_type=ArrayEdit
        )

        def test_data1():
            data = np.random.uniform(0, 2, size=[10, 3])
            fname = os.path.abspath('ArrayExample.npy')
            NumpyAlgs.save(data, fname)
            gui.open_numpy_array(fname)

        gui.add_action(menu=['帮助', '生成测试数据'],
                       text='ArrayExample.npy', slot=test_data1)


class DataEdit(QtWidgets.QWidget):
    """
    特定格式的Numpy矩阵的显示和编辑
    """
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        from zmlx.ui.widget import MatplotWidget
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.view = MatplotWidget(self)
        layout.addWidget(self.view)
        self.edit = ArrayEdit(self)
        layout.addWidget(self.edit)
        layout.setStretch(0, 4)
        layout.setStretch(1, 1)
        self.edit.sig_changed.connect(self._show)
        self.edit.sig_changed.connect(self.sig_changed.emit)
        self.view.context_actions.extend(
            self.edit.context_actions)  # 在绘图界面，附加额外的右键菜单

    def on_figure(self, fig, data):
        pass

    def _show(self):
        self.view.plot_on_figure(lambda fig: self.on_figure(fig, self.get_data()))

    def set_data(self, data):
        self.edit.set_data(data)
        self._show()

    def get_data(self):
        return self.edit.get_data()


class XyEdit(DataEdit):
    """
    曲线数据的显示和编辑
    """

    def __init__(self, parent=None, **opts):
        super().__init__(parent)
        self.opts = dict(
            xlabel='x', ylabel='y', title='Xy数据')
        self.opts.update(opts)

    def on_figure(self, fig, data):
        from zmlx.plt.on_figure import add_axes2
        from zmlx.plt.curve2 import add_curve2
        fig.clear()
        add_axes2(fig, add_curve2, data[:, 0], data[:, 1], **self.opts)

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            'XY两列数据(numpy矩阵)', ['.npy', '.txt'],
            name='xy_data',
            save=NumpyAlgs.save,
            load=NumpyAlgs.load,
            init=lambda: np.array([]),
            widget_type=XyEdit
        )

        def test_data2():
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            data = np.column_stack([x, y])
            fname = os.path.abspath('XY数据.npy')
            np.save(fname, data)
            gui.open_xy_data(fname)

        gui.add_action(menu=['帮助', '生成测试数据'],
                       text='XY数据.npy', slot=test_data2)


class XyzEdit(DataEdit):
    """
    散点曲面数据的显示和编辑
    """

    def __init__(self, parent=None, **opts):
        super().__init__(parent)
        self.opts = dict(
            xlabel='x', ylabel='y', zlabel='z', title='Xyz数据', cmap='coolwarm',
            cbar=dict()
        )
        self.opts.update(opts)

    def on_figure(self, fig, data):
        from zmlx.plt.on_figure import add_axes3
        from zmlx.plt.trisurf import add_trisurf
        fig.clear()
        add_axes3(fig, add_trisurf, data[:, 0], data[:, 1], data[:, 2], **self.opts)

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            'XYZ数据(numpy矩阵)', ['.npy', '.txt'],
            name='xyz_data',
            save=NumpyAlgs.save,
            load=NumpyAlgs.load,
            init=lambda: np.array([]),
            widget_type=XyzEdit
        )

        def test_data3():
            x = np.linspace(-5, 5, 30)
            y = np.linspace(-5, 5, 30)
            x, y = np.meshgrid(x, y)
            z = np.sin(np.sqrt(x ** 2 + y ** 2))
            data = np.column_stack([x.flatten(), y.flatten(), z.flatten()])
            fname = os.path.abspath('XYZ数据.npy')
            np.save(fname, data)
            gui.open_xyz_data(fname)

        gui.add_action(menu=['帮助', '生成测试数据'],
                       text='XYZ数据.npy', slot=test_data3)


class Interp1Edit(MatplotWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, **opts):
        super().__init__(parent)
        self.data = Interp1()
        self.opts = dict(
            xlabel='x', ylabel='y', title='一维插值(右键编辑/导入)')
        self.opts.update(opts)
        self.context_actions.append(
            create_action(self, '导入数据', icon='import',
                          slot=self.import_data))
        self.context_actions.append(
            create_action(
                self, '编辑', slot=self._edit_text))
        self.context_actions.append(
            create_action(
                self, '转化为均匀间隔的数据',
                slot=lambda: self.data.to_evenly_spaced()))

    def on_figure(self, figure):
        from zmlx.plt.on_figure import add_axes2
        figure.clear()
        d = self._get_xy()

        def on_ax(ax):
            if d is None:
                ax.set_title('数据为空')
            else:
                ax.plot(d[:, 0], d[:, 1])

        add_axes2(figure, on_ax, **self.opts)

    def import_data(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '选择numpy文件', os.getcwd(),
            'Numpy Array(*.npy *.txt)'
        )
        if fname:
            self._set_xy(NumpyAlgs.load(fname))

    def _get_xy(self):
        if not isinstance(self.data, Interp1):
            return None
        if self.data.is_empty():
            return None
        x_min, x_max = self.data.xrange()
        if x_min >= x_max:
            return None
        x = np.linspace(x_min, x_max, 100).tolist()
        y = self.data.get(x)
        return np.column_stack((x, y))

    def _set_xy(self, data):
        shape = np.shape(data)
        if len(shape) == 2 and shape[0] >= 2 and shape[1] == 2:
            x = data[:, 0]
            y = data[:, 1]
            self.set_data(Interp1(x=x, y=y))
            self.sig_changed.emit()
            print('成功')
        else:
            print('错误')

    def set_data(self, data):
        if isinstance(data, Interp1):
            self.data = data
            self.plot_on_figure(lambda figure: self.on_figure(figure))

    def get_data(self):
        return self.data

    def _edit_text(self):
        gui.edit_in_tab(
            widget_type=ArrayTextEdit, set_data=self._set_xy,
            get_data=self._get_xy,
            caption=f'Edit: {id(self)}')

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            '一维插值 Interp1', ['.interp1', '.xml', '.txt'],
            name='interp1',
            init=Interp1,
            widget_type=Interp1Edit
        )

        def test_data():
            x = np.linspace(0, 5, 20)
            y = np.sin(x)
            data = Interp1(x=x, y=y)
            fname = os.path.abspath('Example.interp1')
            data.save(fname)
            gui.open_interp1(fname)

        gui.add_action(menu=['帮助', '生成测试数据'],
                       text='Example.interp1', slot=test_data)


class Interp2Edit(MatplotWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, view_init=None, cmap=None, jx=None, jy=None, lutsize=None, **opts):
        super().__init__(parent)
        self.data = Interp2()
        self.opts = opts
        self.context_actions.extend(
            [
                create_action(self, '导入数据', icon='import',
                              slot=self.import_data),
                create_action(self, '编辑', slot=self._edit),
                create_action(
                    self, '刷新', icon='refresh',
                    slot=lambda: self.plot_on_figure(
                        lambda figure: self.on_figure(figure))),
            ])
        self.view_init = view_init  # 视图初始化参数
        self.cmap = cmap
        self.jx = jx
        self.jy = jy
        self.lutsize = lutsize

    def on_figure(self, figure):
        from zmlx.plt.on_figure import add_axes3
        def on_ax(ax):
            if not isinstance(self.data, Interp2):
                ax.set_title(f'类型错误, 当前数据为: {type(self.data).__name__}')
                return

            assert isinstance(self.data, Interp2)
            if self.data.is_empty():
                ax.set_title('数据为空')
                return

            x_min, x_max = self.data.xrange()
            if x_min >= x_max:
                ax.set_title('x轴范围错误')
                return

            y_min, y_max = self.data.yrange()
            if y_min >= y_max:
                ax.set_title('y轴范围错误')
                return

            x = np.linspace(x_min, x_max, 50 if self.jx is None else self.jx)
            y = np.linspace(y_min, y_max, 50 if self.jy is None else self.jy)
            x, y = np.meshgrid(x, y)

            z = np.zeros_like(x)
            shape = np.shape(z)
            for i in range(shape[0]):
                for j in range(shape[1]):
                    z[i, j] = self.data.get(float(x[i, j]), float(y[i, j]))

            cmap = self.cmap if self.cmap is not None else 'coolwarm'
            cmap = get_cm(cmap)
            if self.lutsize is not None:
                cmap = cmap.resampled(self.lutsize)

            surf = ax.plot_surface(x, y, z, cmap=cmap)
            figure.colorbar(surf, ax=ax, shrink=0.5, aspect=10)

            if self.view_init is not None:
                ax.view_init(**self.view_init)

        figure.clear()
        add_axes3(figure, on_ax, **self.opts)

    def set_data(self, data):
        if isinstance(data, Interp2):
            self.data = data
            self.plot_on_figure(lambda figure: self.on_figure(figure))

    def get_data(self):
        return self.data

    def import_data(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '选择numpy文件', os.getcwd(),
            'Numpy Array(*.npy *.txt)'
        )
        if fname:
            self._set_xyz(NumpyAlgs.load(fname))

    def _edit(self):
        gui.edit_in_tab(widget_type=XyzEdit, set_data=self._set_xyz,
                        caption=f'Data({id(self)})')

    def _set_xyz(self, data):
        shape = np.shape(data)
        if len(shape) == 2 and shape[0] >= 2 and shape[1] == 3:
            from zmlx.utility.interp import Interp2 as AsInterp2
            x = data[:, 0]
            y = data[:, 1]
            z = data[:, 2]
            f = AsInterp2(x, y, z)
            x_min = np.min(x)
            x_max = np.max(x)
            y_min = np.min(y)
            y_max = np.max(y)
            f2 = Interp2()
            f2.create(xmin=x_min, dx=(x_max - x_min) / 30, xmax=x_max,
                      ymin=y_min, dy=(y_max - y_min) / 30, ymax=y_max,
                      get_value=f)
            self.set_data(f2)
            self.sig_changed.emit()
            print('成功')
        else:
            print('错误')

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            '二维插值 Interp2', ['.interp2', '.xml', '.txt'],
            name='interp2',
            init=Interp2,
            widget_type=Interp2Edit
        )

        def test_data():
            from zmlx.fluid import ch4
            f = ch4.create()
            f.den.save('Example.interp2')
            gui.open_interp2('Example.interp2')

        gui.add_action(
            menu=['帮助', '生成测试数据'],
            text='Example.interp2', slot=test_data)


def setup_ui():
    for obj in [ArrayEdit, XyEdit, XyzEdit, Interp1Edit, Interp2Edit]:
        try:
            obj.setup_ui()
        except Exception as e:
            print(e)

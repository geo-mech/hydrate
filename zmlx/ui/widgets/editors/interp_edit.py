"""插值数据编辑器（一维 ``Interp1Edit`` / 二维 ``Interp2Edit``）.

两者都是 ``MatplotWidget`` 的子类：图上是数据本身，右键菜单提供「导入 / 编辑 / 刷新」。
真正可编辑的数据是 ``self.data``（``Interp1`` / ``Interp2``），``get_data()`` 返回它。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: 注册移到插件 ``zmlx/ui/plugins/builtin/editors.py``
Modified by DeepSeek, 2026-10-22: 「转化为均匀间隔的数据」补重绘与 ``sig_changed``
"""

import os

try:
    import numpy as np
except ImportError:
    np = None

from zmlx.exts import Interp1, Interp2
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.editors.array_edit import NumpyAlgs
from zmlx.ui.widgets.editors.data_edit import XyzEdit
from zmlx.ui.widgets.editors.text_edit import ArrayTextEdit
from zmlx.ui.widgets.plt import MatplotWidget
from zmlx.plt.cmap import get_cm


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
                slot=self._to_evenly_spaced))

    def _to_evenly_spaced(self):
        """把当前数据转成均匀间隔（右键菜单动作）.

        ⚠️ 这是**用户操作**，所以要重绘并发 ``sig_changed``：2026-10-22 之前这里是个
        直接调 ``self.data.to_evenly_spaced()`` 的 lambda —— 改了数据却既不重绘、也不
        发信号，挂在它上面的响应（如 ``SeepageInterp1Edit`` 写回模型）收不到通知，
        模型里的数据就落后于界面。
        """
        self.data.to_evenly_spaced()
        self.set_data(self.data)   # 重绘
        self.sig_changed.emit()    # 通知外界：用户改了数据

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
            from zmlx.utils.interp import Interp2 as AsInterp2
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


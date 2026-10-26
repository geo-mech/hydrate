"""带绘图预览的数据编辑器（曲线 ``XyEdit`` / 曲面 ``XyzEdit``）.

``DataEdit`` 是基类：上半部分 ``MatplotWidget`` 只做预览，下半部分 ``ArrayEdit`` 才是
真正可编辑的数据；子类只需重写 ``on_figure()`` 决定怎么画。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: 注册移到插件 ``zmlx/ui/plugins/builtin/editors.py``，删掉未使用的 import
"""

from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.editors.array_edit import ArrayEdit
from zmlx.ui.widgets.plt import MatplotWidget


class DataEdit(QtWidgets.QWidget):
    """
    特定格式的Numpy矩阵的显示和编辑
    """
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        from zmlx.ui.widgets import MatplotWidget
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
        from zmlx.plt import add_axes2, add_curve2
        fig.clear()
        add_axes2(fig, add_curve2, data[:, 0], data[:, 1], **self.opts)



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
        from zmlx.plt import add_axes3, add_trisurf
        fig.clear()
        add_axes3(fig, add_trisurf, data[:, 0], data[:, 1], data[:, 2], **self.opts)


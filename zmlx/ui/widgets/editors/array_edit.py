"""Numpy 矩阵编辑器（只读浏览 + 文本编辑 / 文件导入，含读写工具 ``NumpyAlgs``）.

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: 注册移到插件 ``zmlx/ui/plugins/builtin/editors.py``
"""

import os

try:
    import numpy as np
except ImportError:
    np = None

from zmlx.algs.numpy_algs import text_to_numpy, numpy_to_text
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.editors.text_edit import ArrayTextEdit


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


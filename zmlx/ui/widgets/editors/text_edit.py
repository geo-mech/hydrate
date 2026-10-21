"""文本类数据编辑器（等宽字体、纯文本读写）.

``TextEdit`` 是字符串编辑器；``ArrayTextEdit`` 在它之上把文本解析成 numpy 数组。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: ``set_data`` 屏蔽信号 —— 只有用户改才发 ``sig_changed``
"""

from zmlx.algs.numpy_algs import text_to_numpy, numpy_to_text
from zmlx.ui.pyqt import QtCore, QtWidgets


class TextEdit(QtWidgets.QTextEdit):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.setFontFamily("Courier New")  # 使用等宽字体
        self.textChanged.connect(self.sig_changed.emit)

    def set_data(self, data):
        # ⚠️ 必须屏蔽信号：``setText`` 会触发 ``textChanged``，而 ``textChanged`` 已经
        #    接到 ``sig_changed`` 上 —— 不屏蔽的话「程序性地推入数据」也会发
        #    ``sig_changed``，违反了本子包的约定（**只有用户改才发**）。
        #    用 ``self.blockSignals`` 而不是 ``textChanged.disconnect``：它只屏蔽本对象
        #    发出的信号，子对象（视口、滚动条）不受影响，也不会破坏用户的 connect。
        # ⚠️ 必须 ``try/finally``：``blockSignals`` 改的是控件自身的标志位，中途抛异常
        #    （例如 data 的 ``__str__`` 失败）而没复位，控件会**永久哑掉** —— 此后用户
        #    怎么改都不再发 ``sig_changed``，且没有任何报错。
        self.blockSignals(True)
        try:
            self.setText(str(data))
        finally:
            self.blockSignals(False)

    def get_data(self):
        return self.toPlainText()


class ArrayTextEdit(TextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_data(self):
        return text_to_numpy(self.toPlainText())

    def set_data(self, data):
        self.blockSignals(True)  # 理由同 TextEdit.set_data：程序性推入数据不该发信号
        try:
            self.setText(numpy_to_text(data, fmt='%.05e'))
        finally:
            self.blockSignals(False)

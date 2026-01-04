from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets


class Label(QtWidgets.QLabel):
    sig_double_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None, text=None, status=None,
                 double_clicked=None):
        super(Label, self).__init__(parent)
        self._status = status
        if text is not None:
            self.setText(text)
        if callable(double_clicked):
            self.sig_double_clicked.connect(lambda: double_clicked())

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            gui.status(self._status, 3000)
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.sig_double_clicked.emit()
        super().mouseDoubleClickEvent(event)  # 调用父类的事件处理

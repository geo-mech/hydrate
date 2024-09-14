from zml import app_data
from zmlx.ui.Qt import QtWidgets


class Label(QtWidgets.QLabel):

    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        self._style_backup = None
        self._status = None

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            window = app_data.get('main_window')
            if window is not None:
                window.cmd_status(self._status, 3000)
        if self._style_backup is None:
            self._style_backup = self.styleSheet()
        self.setStyleSheet('border: 1px solid red;')
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._style_backup is not None:
            self.setStyleSheet(self._style_backup)
        super().leaveEvent(event)

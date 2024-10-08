import sys

from zmlx.ui.Qt import QtWidgets, QtCore


class VersionLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(f'Python {sys.version_info.major}.{sys.version_info.minor}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:  # 检查是否是左键点击
            try:
                from zml import about
                print(about())
            except Exception as e:
                print(e)

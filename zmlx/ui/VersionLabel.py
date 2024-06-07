import sys

from zmlx.ui.Qt import QtWidgets


class VersionLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(f'Python {sys.version_info.major}.{sys.version_info.minor}')

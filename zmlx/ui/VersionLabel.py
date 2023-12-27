from zmlx.ui.Qt import QtWidgets
import zml
import sys


class VersionLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(f'zml {zml.version} with Python {sys.version_info.major}.{sys.version_info.minor}')


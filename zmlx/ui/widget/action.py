from zmlx.ui.pyqt import is_pyqt6

try:
    if is_pyqt6:
        from PyQt6.QtGui import QAction
    else:
        from PyQt5.QtWidgets import QAction
except:
    QAction = None

from zmlx.ui.pyqt import is_pyqt6

try:
    if is_pyqt6:
        from PyQt6 import QtMultimedia
    else:
        from PyQt5 import QtMultimedia
except:
    QtMultimedia = None

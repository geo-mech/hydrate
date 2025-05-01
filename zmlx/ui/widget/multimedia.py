from zmlx.ui.qt import is_PyQt6

try:
    if is_PyQt6:
        from PyQt6 import QtMultimedia
    else:
        from PyQt5 import QtMultimedia
except:
    QtMultimedia = None

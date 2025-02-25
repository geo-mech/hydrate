from zmlx.ui.Qt import is_PyQt6

try:
    if is_PyQt6:
        from PyQt6.QtGui import QAction
    else:
        from PyQt5.QtWidgets import QAction
except:
    QAction = None

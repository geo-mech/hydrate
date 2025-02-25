from zmlx.ui.Qt import QtWidgets, is_PyQt6

def screen_size():
    if is_PyQt6:
        return QtWidgets.QApplication.primaryScreen().availableGeometry()
    else:
        return QtWidgets.QDesktopWidget().availableGeometry()


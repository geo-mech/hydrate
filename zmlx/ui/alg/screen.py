from zmlx.ui.Qt import QtWidgets, is_PyQt6


def get_current_screen_geometry(window):
    """获取窗口所在显示器的尺寸"""
    if is_PyQt6:
        screen = window.screen() if window else None
        if screen:
            return screen.availableGeometry()
    else:
        desktop = QtWidgets.QDesktopWidget()
        return desktop.availableGeometry(desktop.screenNumber(window))

def get_screen_geometry(screen_index=0):
    """获取指定显示器的尺寸"""
    if is_PyQt6:
        screens = QtWidgets.QApplication.screens()
        if 0 <= screen_index < len(screens):
            return screens[screen_index].availableGeometry()
    else:
        desktop = QtWidgets.QDesktopWidget()
        if screen_index < desktop.screenCount():
            return desktop.availableGeometry(screen_index)

def get_screen_number():
    if is_PyQt6:
        return len(QtWidgets.QApplication.screens())
    else:
        return QtWidgets.QDesktopWidget().screenCount()

def screen_size():
    if is_PyQt6:
        return QtWidgets.QApplication.primaryScreen().availableGeometry()
    else:
        return QtWidgets.QDesktopWidget().availableGeometry()

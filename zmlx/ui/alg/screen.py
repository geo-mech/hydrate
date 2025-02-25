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

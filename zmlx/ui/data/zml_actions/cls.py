is_sys, icon = True, 'clean'
text = '清屏'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().cls()

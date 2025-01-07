icon = 'quit'
text = '退出'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().close()

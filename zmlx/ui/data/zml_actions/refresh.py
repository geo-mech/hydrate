icon = 'refresh'
text = '刷新'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().refresh()

icon = 'quit'
text = '退出'


def slot():
    from zmlx.ui.main_window import get_window
    get_window().close()

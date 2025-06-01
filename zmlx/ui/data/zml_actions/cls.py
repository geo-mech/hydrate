icon = 'clean'
text = '清屏'
menu = '操作'


def slot():
    from zmlx.ui.main_window import get_window
    get_window().cls()

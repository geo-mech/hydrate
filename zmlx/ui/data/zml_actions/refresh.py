icon = 'refresh'
text = '刷新'


def slot():
    from zmlx.ui.main_window import get_window
    get_window().refresh()

text = '关闭所有页面'
icon = 'close_all'


def slot():
    from zmlx.ui.main_window import get_window
    get_window().close_all_tabs()


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return window.count_tabs() > 0
    return None

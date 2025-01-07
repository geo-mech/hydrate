text = '关闭所有页面'
support_hide = False
on_toolbar = True
icon = 'close_all'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().close_all_tabs()


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return window.count_tabs() > 0 and not window.is_running()

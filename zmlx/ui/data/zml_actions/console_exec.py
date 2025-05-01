text = '运行'
on_toolbar = True
tooltip = '运行当前标签页面显示的脚本'
icon = 'begin'


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return hasattr(
            window.get_current_widget(),
            'console_exec') and not window.is_running()


def slot():
    from zmlx.ui.main_window import get_window
    getattr(get_window().get_current_widget(), 'console_exec')()


def always_show():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is None:
        return False
    console = window.get_console()
    return not console.is_running()

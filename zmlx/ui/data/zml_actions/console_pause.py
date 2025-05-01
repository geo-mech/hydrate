text = '暂停'
icon = 'pause'
on_toolbar = True
tooltip = '暂停内核的执行 (需要提前在脚本内设置break_point)'


def slot():
    from zmlx.ui.main_window import get_window
    console = get_window().get_console()
    console.pause_clicked()


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is None:
        return False
    console = window.get_console()
    if not console.is_running():
        return False
    return not console.should_pause()

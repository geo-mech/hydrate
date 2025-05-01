text = '停止'
icon = 'stop'
on_toolbar = True
tooltip = '安全地终止内核的执行 (需要提前在脚本内设置break_point)'


def slot():
    from zmlx.ui.main_window import get_window
    console = get_window().get_console()
    console.stop_clicked()


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is None:
        return False
    console = window.get_console()
    return console.is_running()

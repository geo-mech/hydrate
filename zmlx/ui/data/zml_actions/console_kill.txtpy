icon = 'kill'
text = '强制结束'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().kill_thread()


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is None:
        return False
    console = window.get_console()
    return console.is_running()

text = '继续'
icon = 'begin'
on_toolbar = True


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
    if console.should_pause():
        return True
    else:
        return False

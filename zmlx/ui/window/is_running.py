def is_running():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return window.is_running()
    else:
        return False

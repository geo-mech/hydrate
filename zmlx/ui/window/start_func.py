def start_func(code):
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        if not window.is_running():
            window.start_func(code)

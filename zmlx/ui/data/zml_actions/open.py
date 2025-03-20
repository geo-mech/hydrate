icon = 'open'
on_toolbar = True
text = '打开'
always_show = True


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().open_file_by_dlg()


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

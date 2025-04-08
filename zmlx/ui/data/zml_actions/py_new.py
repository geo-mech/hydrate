text = '新建Python脚本'
icon = 'python'


def slot():
    from zmlx.ui.window.code import new_code
    from zmlx.ui.MainWindow import get_window
    win = get_window()
    if win is not None:
        if not win.is_running():
            new_code()


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

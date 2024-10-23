on_toolbar = True
icon = 'open'
tooltip = '设置当前的工作路径'
text = '工作路径'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().set_cwd_by_dialog()


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

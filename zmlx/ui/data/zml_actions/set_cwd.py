on_toolbar = True
icon = 'open'
tooltip = '设置当前的工作路径'
text = '工作路径'
always_show = True


def slot():
    from zmlx.ui.main_window import get_window
    get_window().set_cwd_by_dialog()


def enabled():
    from zmlx.ui.window_functions import is_running
    return not is_running()

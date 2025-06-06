text = '导出'
menu = '文件'
on_toolbar = True
icon = 'matplotlib'


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return hasattr(window.get_current_widget(),
                       'export_plt_figure') and not window.is_running()
    return None


def slot():
    from zmlx.ui.main_window import get_window
    getattr(get_window().get_current_widget(),
            'export_plt_figure')()

menu = '帮助'
text = '新建Issue'
icon = 'issues'


def slot():
    from zmlx.ui.alg import open_url
    from zmlx.ui.main_window import get_window
    get_window().start_func(
        lambda: open_url(url='https://gitee.com/geomech/hydrate/issues/new',
                         on_top=True,
                         caption='新建Issue',
                         icon='issues'
                         ))


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

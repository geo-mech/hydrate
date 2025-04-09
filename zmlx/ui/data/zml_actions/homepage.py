menu = '帮助'
text = '主页'
icon = 'home'


def slot():
    from zmlx.ui.alg import open_url
    from zmlx.ui.main_window import get_window
    get_window().start_func(
        lambda: open_url(url='https://gitee.com/geomech/hydrate',
                         on_top=True,
                         caption='IGG-Hydrate',
                         icon='home'
                         ))


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()
    return None

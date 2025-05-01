menu = '帮助'
text = '中科院地质地球所'
icon = 'iggcas'


def slot():
    from zmlx.ui.alg import open_url
    from zmlx.ui.main_window import get_window
    get_window().start_func(lambda: open_url(url='http://www.igg.cas.cn/',
                                             on_top=True,
                                             caption='中科院地质地球所主页',
                                             icon='iggcas'
                                             ))


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

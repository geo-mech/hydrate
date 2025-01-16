menu = '帮助'
text = '中科院地质地球所'
icon = 'iggcas'


def slot():
    from zmlx.ui.alg.open_url import open_url
    from zmlx.ui.MainWindow import get_window
    get_window().start_func(lambda: open_url(url='http://www.igg.cas.cn/',
                                             on_top=True,
                                             zoom_factor=1.5,
                                             caption='中科院地质地球所主页',
                                             icon='iggcas'
                                             ))


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

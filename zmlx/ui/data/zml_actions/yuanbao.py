menu = '帮助'
text = '腾讯元宝AI'


def slot():
    from zmlx.ui.alg.open_url import open_url
    from zmlx.ui.MainWindow import get_window
    get_window().start_func(lambda: open_url(url='https://yuanbao.tencent.com/chat/',
                                             on_top=True,
                                             caption='腾讯元宝AI'
                                             ))


def enabled():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        return not window.is_running()

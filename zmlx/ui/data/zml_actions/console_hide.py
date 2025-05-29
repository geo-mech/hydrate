text = '隐藏'
on_toolbar = True
icon = 'console'
tooltip = '隐藏主窗口右侧的控制台'


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        console = window.get_console()
        return console.isVisible()
    return None


def slot():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        console = window.get_console()
        console.setVisible(False)

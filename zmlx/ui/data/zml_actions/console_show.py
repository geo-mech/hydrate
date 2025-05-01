text = '显示'
on_toolbar = True
icon = 'console'
tooltip = '显示主窗口右侧的控制台'


def enabled():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        console = window.get_console()
        return not console.isVisible()


def slot():
    from zmlx.ui.main_window import get_window
    window = get_window()
    if window is not None:
        console = window.get_console()
        console.setVisible(True)

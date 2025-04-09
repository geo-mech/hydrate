text = '窗口风格(qss文件)'
menu = '设置'


def slot():
    from zmlx.ui.window_functions import show_txt
    from zmlx.ui.cfg import temp
    show_txt(temp('zml_window_style.qss'))

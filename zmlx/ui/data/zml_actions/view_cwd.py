text = '文件'
on_toolbar = True
icon = 'cwd'


def slot():
    from zmlx.ui.MainWindow import get_window
    get_window().view_cwd()


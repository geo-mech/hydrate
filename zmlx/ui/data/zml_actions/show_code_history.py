text = '代码运行历史'
menu = '帮助'


def slot():
    from zmlx.ui.main_window import get_window
    from zml import app_data
    get_window().show_code_history(
        folder=app_data.root('console_history'), caption='代码运行历史')

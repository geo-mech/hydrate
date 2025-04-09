icon = 'info'
text = '反馈'
menu = '帮助'


def slot():
    from zmlx.ui.widget.feedback import FeedbackWidget
    from zmlx.ui.main_window import get_window
    win = get_window()
    win.get_widget(the_type=FeedbackWidget, caption='反馈')


def enabled():
    from zmlx.ui.window_functions import is_running
    return not is_running()

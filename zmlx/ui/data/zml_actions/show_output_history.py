text = '输出历史'
is_sys = True
menu = '帮助'


def slot():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.OutputHistoryViewer import OutputHistoryViewer
    get_window().get_widget(the_type=OutputHistoryViewer, caption='输出历史',
                            on_top=True, oper=lambda w: w.set_folder())

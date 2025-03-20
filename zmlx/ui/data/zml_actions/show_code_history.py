text = '代码运行历史'
is_sys = True
menu = '帮助'


def slot():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.CodeHistoryViewer import CodeHistoryViewer
    from zml import app_data
    def oper(w: CodeHistoryViewer):
        w.set_folder(folder=app_data.root('console_history'))
    get_window().get_widget(the_type=CodeHistoryViewer, caption='代码运行历史', on_top=True,
                            oper=oper, icon='python')

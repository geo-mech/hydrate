text = 'Python控制台(测试)'
on_toolbar = False
icon = 'console'


def slot():
    from zmlx.ui.Widgets.PgConsole import PgConsole
    from zmlx.ui.MainWindow import get_window
    if PgConsole is not None:
        get_window().get_widget(the_type=PgConsole, caption='控制台',
                                on_top=True, icon='console')

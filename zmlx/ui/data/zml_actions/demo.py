on_toolbar = True
icon = 'demo'
text = '示例'
is_sys = True


def slot():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.Demo import DemoWidget
    get_window().get_widget(the_type=DemoWidget, caption='示例', on_top=True,
                            oper=lambda w: w.refresh, icon='demo')

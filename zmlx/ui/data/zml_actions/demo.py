on_toolbar = True
icon = 'demo'
text = '示例'
is_sys = True


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.demo_widget import DemoWidget
    get_window().get_widget(the_type=DemoWidget, caption='示例', on_top=True,
                            oper=lambda w: w.refresh, icon='demo')

text = '注册'
is_sys = True
icon = 'reg'


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.reg_tool import RegTool
    get_window().get_widget(the_type=RegTool,
                            caption='注册',
                            on_top=True, icon='reg')

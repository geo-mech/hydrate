text = '设置env'
icon = 'set'


def slot():
    from zmlx.ui.widget.env_edit import EnvEdit
    from zmlx.ui.main_window import get_window

    get_window().get_widget(the_type=EnvEdit, caption='设置Env',
                            on_top=True, icon='set')

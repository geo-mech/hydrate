text = '设置env'
dependency = """from zmlx.ui.Widgets.EnvEdit import EnvEdit"""
is_sys = True
icon = 'set'


def slot():
    from zmlx.ui.Widgets.EnvEdit import EnvEdit
    from zmlx.ui.MainWindow import get_window

    get_window().get_widget(the_type=EnvEdit, caption='设置Env',
                            on_top=True, icon='set')

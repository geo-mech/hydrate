on_toolbar = True
icon = 'info'
text = 'ReadMe'


def slot():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.ReadMe import ReadMeBrowser
    get_window().get_widget(the_type=ReadMeBrowser,
                            caption='ReadMe',
                            on_top=True, icon='info')

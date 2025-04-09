on_toolbar = True
icon = 'info'
text = 'ReadMe'


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.read_me import ReadMeBrowser
    get_window().get_widget(the_type=ReadMeBrowser,
                            caption='ReadMe',
                            on_top=True, icon='info')

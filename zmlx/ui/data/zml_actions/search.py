text = '搜索路径'
icon = 'set'


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.file_find import FileFind
    get_window().get_widget(the_type=FileFind,
                            caption='搜索路径',
                            on_top=True, icon='set')

tooltip = '显示工作区的中的变量'
text = '变量'
icon = 'variables'


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.mem_viewer import MemViewer
    get_window().get_widget(the_type=MemViewer,
                            caption='变量',
                            on_top=True,
                            oper=lambda w: w.refresh,
                            icon='variables')

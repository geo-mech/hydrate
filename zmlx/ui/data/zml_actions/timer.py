tooltip = '显示cpu耗时统计的结果'
text = '耗时'
on_toolbar = False
icon = 'clock'


def slot():
    from zmlx.ui.main_window import get_window
    from zmlx.ui.widget.timer_viewer import TimerViewer
    get_window().get_widget(the_type=TimerViewer,
                            caption='耗时',
                            on_top=True,
                            oper=lambda w: w.refresh,
                            icon='clock')

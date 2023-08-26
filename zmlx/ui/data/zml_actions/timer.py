# ** tooltip = '显示cpu耗时统计的结果'
# ** text = '耗时'
# ** is_sys = True

from zmlx.ui.Widgets.TimerViewer import TimerViewer
from zml import gui

gui.get_widget(type=TimerViewer, caption='耗时', on_top=True, oper=lambda w: w.refresh)

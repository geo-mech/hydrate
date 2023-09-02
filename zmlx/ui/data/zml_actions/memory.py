# ** tooltip = '显示工作区的中的变量'
# ** text = '变量'
# ** on_toolbar = 1
# ** icon = 'variables.png'
# ** is_sys = True

from zml import gui
from zmlx.ui.Widgets.MemViewer import MemViewer

gui.get_widget(type=MemViewer, caption='变量', on_top=True, oper=lambda w: w.refresh, icon='variables.png')

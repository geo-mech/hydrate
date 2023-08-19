# ** tooltip = '显示工作区的中的变量'
# ** text = '变量'
# ** on_toolbar = 1
# ** icon = 'variables.png'

from zmlx.ui.Widgets.MemViewer import MemViewer
from zml import gui

gui.get_widget(type=MemViewer, caption='变量', on_top=True, oper=lambda w: w.refresh)

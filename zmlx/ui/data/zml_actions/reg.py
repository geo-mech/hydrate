# ** text = '注册'
# ** is_sys = True
# ** icon = 'reg.png'

from zml import gui
from zmlx.ui.Widgets.RegTool import RegTool

gui.get_widget(type=RegTool, caption='注册', on_top=True, icon='reg.png')

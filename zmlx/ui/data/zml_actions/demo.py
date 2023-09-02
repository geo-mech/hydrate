# ** on_toolbar = True
# ** icon = 'demo.png'
# ** text = '示例'
# ** is_sys = True


from zml import gui
from zmlx.ui.Widgets.Demo import DemoWidget

gui.get_widget(type=DemoWidget, caption='示例', on_top=True, oper=lambda w: w.refresh, icon='demo.png')

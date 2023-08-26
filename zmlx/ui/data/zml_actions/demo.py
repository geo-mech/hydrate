# ** on_toolbar = True
# ** icon = 'python.png'
# ** text = '示例'


from zmlx.ui.Widgets.Demo import DemoWidget
from zml import gui

gui.get_widget(type=DemoWidget, caption='示例', on_top=True, oper=lambda w: w.refresh)

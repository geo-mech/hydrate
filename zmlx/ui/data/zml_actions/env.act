# ** text = '设置env'
# ** dependency = """from zmlx.ui.Widgets.EnvEdit import MultiLineEdit"""
# ** is_sys = True
# ** icon = 'set.png'

from zmlx.ui.GuiBuffer import gui
from zmlx.ui.Widgets.EnvEdit import MultiLineEdit


def init(widget):
    assert isinstance(widget, MultiLineEdit)
    widget.add(label='标签方向', key='TabPosition', items=['North', 'East', 'South', 'West'])
    widget.add(label='标签形状', key='TabShape', items=['Rounded', 'Triangular'])
    widget.add(label='内核优先级', key='console_priority', items=['LowestPriority', 'LowPriority',
                                                                  'InheritPriority', 'NormalPriority',
                                                                  'HighPriority', 'HighestPriority'])
    widget.add(label='禁用计时器', key='disable_timer', items=['False', 'True'])
    widget.add(label='disable_splash', key='disable_splash', items=['False', 'True'])


gui.get_widget(type=MultiLineEdit, caption='设置Env',
               on_top=True, init=init, icon='set.png')

# ** text = '设置env'
# ** dependency = """from zmlx.ui.Widgets.EnvEdit import MultiLineEdit"""

from zmlx.ui.Widgets.EnvEdit import MultiLineEdit
from zml import gui


def init(widget):
    assert isinstance(widget, MultiLineEdit)
    widget.add(label='标签方向', key='TabPosition', items=['North', 'East', 'South', 'West'])
    widget.add(label='标签形状', key='TabShape', items=['Rounded', 'Triangular'])
    widget.add(label='内核优先级', key='console_priority', items=['LowestPriority', 'LowPriority',
                                                                  'InheritPriority', 'NormalPriority',
                                                                  'HighPriority', 'HighestPriority'])


gui.get_widget(type=MultiLineEdit, caption='设置Env',
               on_top=True, init=init)

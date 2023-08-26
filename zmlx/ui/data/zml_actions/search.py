# ** text = '搜索路径'
# ** is_sys = True

from zml import gui
from zmlx.ui.Widgets.FileFind import FileFind

gui.get_widget(type=FileFind, caption='搜索路径', on_top=True)

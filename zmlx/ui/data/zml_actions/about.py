# ** icon = 'info.png'
# ** text = '关于'
# ** is_sys = True

from zml import gui
from zmlx.ui.Widgets.About import About

gui.get_widget(type=About, caption='关于', on_top=True, icon='info.png')

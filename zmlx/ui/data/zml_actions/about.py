# ** icon = 'info.png'
# ** text = '关于'

from zmlx.ui.Widgets.About import About
from zml import gui

gui.get_widget(type=About, caption='关于', on_top=True)

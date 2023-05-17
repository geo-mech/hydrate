# ** is_sys = True
# ** on_toolbar = True
# ** icon = 'open.png'
# ** tooltip = '设置当前的工作路径'

from zml import *

gui.window().console_widget.set_cwd_by_dialog()

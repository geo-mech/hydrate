# ** text = '日历'
# ** menu = '显示'
# ** is_sys = True


from zml import gui
from zmlx.ui.Qt import QtWidgets

gui.get_widget(type=QtWidgets.QCalendarWidget, caption='日历', on_top=True)

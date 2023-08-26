# ** text = '日历'
# ** menu = '显示'
# ** is_sys = True


from PyQt5 import QtWidgets
from zml import gui

gui.get_widget(type=QtWidgets.QCalendarWidget, caption='日历', on_top=True)

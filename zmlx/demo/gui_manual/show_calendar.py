from zmlx import gui
from zmlx.ui.pyqt import QtWidgets


def show_calendar():
    gui.get_widget(
        the_type=QtWidgets.QCalendarWidget, caption='日历')


def setup_ui():
    gui.add_action(
        menu='Gui Manual', text='显示日历', slot=show_calendar)


if __name__ == '__main__':
    gui.execute(func=setup_ui, close_after_done=False)

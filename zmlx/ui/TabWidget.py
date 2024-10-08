from zml import app_data
from zmlx.ui.Qt import QtWidgets


def set_position(widget):
    try:
        text = app_data.getenv('TabPosition', default='')
        if text == 'North':
            widget.setTabPosition(QtWidgets.QTabWidget.North)
        if text == 'South':
            widget.setTabPosition(QtWidgets.QTabWidget.South)
        if text == 'East':
            widget.setTabPosition(QtWidgets.QTabWidget.East)
        if text == 'West':
            widget.setTabPosition(QtWidgets.QTabWidget.West)
    except Exception as e:
        print(e)


def set_shape(widget):
    try:
        text = app_data.getenv('TabShape', default='')
        if text == 'Triangular':
            widget.setTabShape(QtWidgets.QTabWidget.Triangular)
        if text == 'Rounded':
            widget.setTabShape(QtWidgets.QTabWidget.Rounded)
    except Exception as e:
        print(e)


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        set_position(self)
        set_shape(self)

    def close_tab(self, index):
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)

    def find_widget(self, the_type=None, text=None):
        assert the_type is not None or text is not None
        for i in range(self.count()):
            widget = self.widget(i)
            if the_type is not None:
                if not isinstance(widget, the_type):
                    continue
            if text is not None:
                if text != self.tabText(i):
                    continue
            return widget

    def show_next(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index + 1 < self.count():
                self.setCurrentIndex(index + 1)

    def show_prev(self):
        if self.count() > 1:
            index = self.currentIndex()
            if index > 0:
                self.setCurrentIndex(index - 1)

    def close_all_tabs(self):
        while self.count() > 0:
            self.close_tab(0)


if __name__ == '__main__':
    from zmlx.ui.alg.show_widget import show_widget

    show_widget(TabWidget)

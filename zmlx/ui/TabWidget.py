from zml import app_data
from zmlx.ui.Qt import QtWidgets


def setTabPosition(widget):
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
    except:
        pass


def setTabShape(widget):
    try:
        text = app_data.getenv('TabShape', default='')
        if text == 'Triangular':
            widget.setTabShape(QtWidgets.QTabWidget.Triangular)
        if text == 'Rounded':
            widget.setTabShape(QtWidgets.QTabWidget.Rounded)
    except:
        pass


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.setMovable(True)
        setTabPosition(self)
        setTabShape(self)

    def close_tab(self, index):
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)

    def find_widget(self, type=None, text=None):
        assert type is not None or text is not None
        for i in range(self.count()):
            widget = self.widget(i)
            if type is not None:
                if not isinstance(widget, type):
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

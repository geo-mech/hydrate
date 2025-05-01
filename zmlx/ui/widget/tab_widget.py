from zml import app_data
from zmlx.ui.alg import create_action
from zmlx.ui.qt import QtWidgets, QtCore


def set_position(widget):
    try:
        text = app_data.getenv('TabPosition', default='North',
                               ignore_empty=True)
        if text == 'North':
            widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        if text == 'South':
            widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)
        if text == 'East':
            widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.East)
        if text == 'West':
            widget.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
    except Exception as e:
        print(e)


def set_shape(widget):
    try:
        text = app_data.getenv('TabShape', default='Rounded', ignore_empty=True)
        if text == 'Triangular':
            widget.setTabShape(QtWidgets.QTabWidget.TabShape.Triangular)
        if text == 'Rounded':
            widget.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
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

    def contextMenuEvent(self, event):
        from zmlx.ui.main_window import get_window
        window = get_window()

        # 点击的标签的索引
        tab_index = None
        for i in range(self.count()):
            if self.tabBar().tabRect(i).contains(event.pos()):
                tab_index = i

        menu = QtWidgets.QMenu(self)
        if self.count() >= 1:
            menu.addAction(window.get_action('close_all_tabs'))
            menu.addAction(window.get_action('tab_details'))
            if tab_index is not None:
                menu.addSeparator()
                menu.addAction(create_action(
                    self, text='重命名',
                    slot=lambda: self._rename_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭',
                    slot=lambda: self.close_tab(tab_index))
                )
                menu.addAction(create_action(
                    self, text='关闭其它',
                    slot=lambda: self._close_all_except(tab_index))
                )
            menu.addSeparator()
        menu.addAction(window.get_action('readme'))
        menu.addAction(window.get_action('about'))
        menu.addSeparator()
        menu.addAction(window.get_action('open'))
        menu.addAction(window.get_action('set_cwd'))
        menu.addAction(window.get_action('demo'))
        menu.addAction(window.get_action('set_demo_opath'))
        menu.exec(event.globalPos())

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

    def _close_all_except(self, index):
        if 0 <= index < self.count():
            while self.count() > 1:
                if index > 0:
                    self.close_tab(0)
                    index -= 1
                else:
                    self.close_tab(1)
        else:
            self.close_all_tabs()

    def _rename_tab(self, index):
        if index < self.count():
            text, ok = QtWidgets.QInputDialog.getText(
                self, '重命名',
                '请输入新的名称:',
                text=self.tabText(index))
            if ok:
                self.setTabText(index, text)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:  # 中间按钮关闭选项卡
            for i in range(self.count()):
                if self.tabBar().tabRect(i).contains(event.pos()):
                    self.close_tab(i)
        super().mousePressEvent(event)


if __name__ == '__main__':
    from zmlx.ui.alg import show_widget

    show_widget(TabWidget)

# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtGui, QtCore
from zmlx.ui.Config import load_pixmap


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        try:
            self.cover = load_pixmap("cover.png")
        except:
            self.cover = None
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

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

    def paintEvent(self, event):
        super().paintEvent(event)
        # 显示图片代码参考：
        # https://vimsky.com/examples/detail/python-ex-PyQt5.Qt-QPainter-drawPixmap-method.html
        pixmap = self.cover
        if pixmap is not None:
            try:
                # 旁边留白，以不遮挡住标签的内容
                width = self.rect().width() * 0.95
                height = self.rect().height() * 0.85
                if pixmap.width() / pixmap.height() > width / height:
                    fig_h = width * pixmap.height() / pixmap.width()
                    x = (self.rect().width() - width) / 2
                    y = (height - fig_h) / 2 + (self.rect().height() - height) / 2
                    target = QtCore.QRect(x, y, width, fig_h)
                else:
                    fig_w = height * pixmap.width() / pixmap.height()
                    x = (width - fig_w) / 2 + (self.rect().width() - width) / 2
                    y = (self.rect().height() - height) / 2
                    target = QtCore.QRect(x, y, fig_w, height)
                painter = QtGui.QPainter(self)
                painter.setRenderHints(QtGui.QPainter.Antialiasing
                                       | QtGui.QPainter.SmoothPixmapTransform)
                try:
                    dpr = self.devicePixelRatioF()
                except AttributeError:
                    dpr = self.devicePixelRatio()
                spmap = pixmap.scaled(target.size() * dpr, QtCore.Qt.KeepAspectRatio,
                                      QtCore.Qt.SmoothTransformation)
                spmap.setDevicePixelRatio(dpr)
                painter.drawPixmap(target, spmap)
                painter.end()
            except:
                pass


if __name__ == '__main__':
    from zmlx.ui.WidgetAlg import show_widget

    show_widget(TabWidget)

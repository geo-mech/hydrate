from zmlx.ui.Qt import QtGui, QtCore


def paint_image(widget, pixmap):
    """
    显示图片代码参考：
    https://vimsky.com/examples/detail/python-ex-PyQt5.Qt-QPainter-drawPixmap-method.html
    """
    if pixmap is None or widget is None:
        return
    try:
        width = widget.rect().width()
        height = widget.rect().height()
        if pixmap.width() / pixmap.height() > width / height:
            fig_h = width * pixmap.height() / pixmap.width()
            x = (widget.rect().width() - width) / 2
            y = (height - fig_h) / 2 + (widget.rect().height() - height) / 2
            target = QtCore.QRect(int(x), int(y), int(width), int(fig_h))
        else:
            fig_w = height * pixmap.width() / pixmap.height()
            x = (width - fig_w) / 2 + (widget.rect().width() - width) / 2
            y = (widget.rect().height() - height) / 2
            target = QtCore.QRect(int(x), int(y), int(fig_w), int(height))
        painter = QtGui.QPainter(widget)
        painter.setRenderHints(QtGui.QPainter.Antialiasing
                               | QtGui.QPainter.SmoothPixmapTransform)
        try:
            dpr = widget.devicePixelRatioF()
        except AttributeError:
            dpr = widget.devicePixelRatio()
        spmap = pixmap.scaled(target.size() * dpr, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                              QtCore.Qt.TransformationMode.SmoothTransformation)
        spmap.setDevicePixelRatio(dpr)
        painter.drawPixmap(target, spmap)
        painter.end()
    except:
        pass

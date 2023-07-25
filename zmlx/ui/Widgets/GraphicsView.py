from zmlx.ui.Qt import QtWidgets, QtGui


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing)

    def wheelEvent(self, event):
        t = 10.0
        if event.angleDelta().y() > 0:
            factor = (t + 1) / t
        else:
            factor = t / (t + 1)
        self.scale(factor, factor)

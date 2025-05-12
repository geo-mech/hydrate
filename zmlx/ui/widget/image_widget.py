"""
https://www.45fan.com/article.php?aid=1CUo8mPtEy1JGp5Y
"""

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class ImageViewer(QtWidgets.QGraphicsView):
    """
    图片查看器
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoomInTimes = 0
        self.maxZoomInTimes = 22

        # 创建场景
        self.graphicsScene = QtWidgets.QGraphicsScene()

        # 图片
        self.pixmap = QtGui.QPixmap()
        self.pixmapItem = QtWidgets.QGraphicsPixmapItem(self.pixmap)
        self.displayedImageSize = QtCore.QSize(0, 0)

        # 初始化小部件
        self.__init_widget()

    def __init_widget(self):
        """
        初始化小部件
        """
        self.resize(1200, 900)

        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 以鼠标所在位置为锚点进行缩放
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # 平滑缩放
        self.pixmapItem.setTransformationMode(
            QtCore.Qt.TransformationMode.SmoothTransformation)
        self.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing |
            QtGui.QPainter.RenderHint.SmoothPixmapTransform)

        # 设置场景
        self.graphicsScene.addItem(self.pixmapItem)
        self.setScene(self.graphicsScene)

    def wheelEvent(self, e: QtGui.QWheelEvent):
        """
        滚动鼠标滚轮缩放图片
        """
        if e.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def resizeEvent(self, e):
        """
        缩放图片
        """
        super().resizeEvent(e)

        if self.zoomInTimes > 0:
            return

        # 调整图片大小
        ratio = self.__get_scale_ratio()
        self.displayedImageSize = self.pixmap.size() * ratio
        if ratio < 1:
            self.fitInView(self.pixmapItem,
                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.resetTransform()

    def set_image(self, image_path: str):
        """
        设置显示的图片
        """
        self.set_pixmap(QtGui.QPixmap(image_path))

    def set_pixmap(self, pixmap: QtGui.QPixmap):
        assert isinstance(pixmap, QtGui.QPixmap)
        self.resetTransform()

        # 刷新图片
        self.pixmap = pixmap
        self.pixmapItem.setPixmap(self.pixmap)

        # 调整图片大小
        self.setSceneRect(QtCore.QRectF(self.pixmap.rect()))
        ratio = self.__get_scale_ratio()
        self.displayedImageSize = self.pixmap.size() * ratio
        if ratio < 1:
            self.fitInView(self.pixmapItem,
                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def resetTransform(self):
        """
        重置变换
        """
        super().resetTransform()
        self.zoomInTimes = 0
        self.__set_drag_enabled(False)

    def __is_enable_drag(self):
        """
        根据图片的尺寸决定是否启动拖拽功能
        """
        v = self.verticalScrollBar().maximum() > 0
        h = self.horizontalScrollBar().maximum() > 0
        return v or h

    def __set_drag_enabled(self, is_enabled: bool):
        """
        设置拖拽是否启动
        """
        self.setDragMode(
            self.DragMode.ScrollHandDrag if is_enabled else self.DragMode.NoDrag)

    def __get_scale_ratio(self):
        """
        获取显示的图像和原始图像的缩放比例
        """
        if self.pixmap.isNull():
            return 1

        pw = self.pixmap.width()
        ph = self.pixmap.height()
        rw = min(1, int(self.width() / pw))
        rh = min(1, int(self.height() / ph))
        return min(rw, rh)

    def fitInView(self, item: QtWidgets.QGraphicsItem,
                  mode=QtCore.Qt.AspectRatioMode.KeepAspectRatio):
        """
        缩放场景使其适应窗口大小
        """
        super().fitInView(item, mode)
        self.displayedImageSize = self.__get_scale_ratio() * self.pixmap.size()
        self.zoomInTimes = 0

    def zoom_in(self,
                view_anchor=QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse):
        """ 放大图像 """
        if self.zoomInTimes == self.maxZoomInTimes:
            return

        self.setTransformationAnchor(view_anchor)

        self.zoomInTimes += 1
        self.scale(1.1, 1.1)
        self.__set_drag_enabled(self.__is_enable_drag())

        # 还原 anchor
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def zoom_out(self,
                 view_anchor=QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse):
        """ 缩小图像 """
        if self.zoomInTimes == 0 and not self.__is_enable_drag():
            return

        self.setTransformationAnchor(view_anchor)

        self.zoomInTimes -= 1

        # 原始图像的大小
        pw = self.pixmap.width()
        ph = self.pixmap.height()

        # 实际显示的图像宽度
        w = self.displayedImageSize.width() * 1.1 ** self.zoomInTimes
        h = self.displayedImageSize.height() * 1.1 ** self.zoomInTimes

        if pw > self.width() or ph > self.height():
            # 在窗口尺寸小于原始图像时禁止继续缩小图像比窗口还小
            if w <= self.width() and h <= self.height():
                self.fitInView(self.pixmapItem)
            else:
                self.scale(1 / 1.1, 1 / 1.1)
        else:
            # 在窗口尺寸大于图像时不允许缩小的比原始图像小
            if w <= pw:
                self.resetTransform()
            else:
                self.scale(1 / 1.1, 1 / 1.1)

        self.__set_drag_enabled(self.__is_enable_drag())

        # 还原 anchor
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

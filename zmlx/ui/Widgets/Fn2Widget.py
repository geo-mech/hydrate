from matplotlib import cm

from zmlx.ui.Config import *
from zmlx.ui.Widgets.GraphicsView import GraphicsView


class Hf2ColorMap:
    @staticmethod
    def create_colormap(cm):
        colors = []
        for i in range(cm.N):
            c = [float(s) for s in cm(i)]
            if len(c) >= 3:
                colors.append(QtGui.QColor(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)))
        return colors

    @staticmethod
    def get_color(cval, cmin, cmax, cm):
        assert (len(cm) > 0)
        i = int(((cval - cmin) / (cmax - cmin)) * len(cm))
        if i >= len(cm):
            return cm[-1]
        if i < 0:
            return cm[0]
        else:
            return cm[i]

    @staticmethod
    def coolwarm():
        return Hf2ColorMap.create_colormap(cm.coolwarm)

    @staticmethod
    def jet():
        return Hf2ColorMap.create_colormap(cm.jet)


class Hf2Data:
    def __init__(self):
        self.fractures = []
        self.inlets = []

    def import_fractures(self, text, iw=4, ic=6):
        self.fractures = []
        if iw is None:
            iw = -1
        if ic is None:
            ic = -1
        for line in text.split('\n'):
            f = [float(s) for s in line.split()]
            if len(f) < 4:
                continue
            if 0 < iw < len(f):
                w = abs(f[iw])
            else:
                w = 0
            if 0 <= ic < len(f):
                c = f[ic]
            else:
                c = 0
            f = f[0: 4]
            f.append(w)
            f.append(c)
            self.fractures.append(f)

    def import_inlets(self, text, ix=0, iy=1):
        self.inlets = []
        for line in text.split('\n'):
            f = [float(s) for s in line.split()]
            if ix >= len(f) or iy >= len(f):
                continue
            x = f[ix]
            y = f[iy]
            self.inlets.append((x, y))

    def get_xrange(self):
        xrange = None
        for f in self.fractures:
            assert (len(f) == 6)
            for x in (f[0], f[2]):
                if xrange is None:
                    xrange = [x, x]
                    continue
                else:
                    xrange[0] = min(xrange[0], x)
                    xrange[1] = max(xrange[1], x)
        for f in self.inlets:
            x = f[0]
            if xrange is None:
                xrange = [x, x]
                continue
            else:
                xrange[0] = min(xrange[0], x)
                xrange[1] = max(xrange[1], x)
        return xrange

    def get_yrange(self):
        yrange = None
        for f in self.fractures:
            assert (len(f) == 6)
            for y in (f[1], f[3]):
                if yrange is None:
                    yrange = [y, y]
                    continue
                else:
                    yrange[0] = min(yrange[0], y)
                    yrange[1] = max(yrange[1], y)
        for f in self.inlets:
            y = f[1]
            if yrange is None:
                yrange = [y, y]
                continue
            else:
                yrange[0] = min(yrange[0], y)
                yrange[1] = max(yrange[1], y)
        return yrange

    def get_wmax(self):
        # get max fracture width
        wmax = 0
        for f in self.fractures:
            assert (len(f) == 6)
            wmax = max(wmax, f[4])
        return wmax

    def get_crange(self):
        # range of color value
        crange = None
        for f in self.fractures:
            assert (len(f) == 6)
            c = f[5]
            if crange is None:
                crange = [c, c]
                continue
            else:
                crange[0] = min(crange[0], c)
                crange[1] = max(crange[1], c)
        return crange


class Hf2FracView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Hf2FracView, self).__init__(parent)
        self.__boundingRect = None
        self.view = GraphicsView(self)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.view)
        self.data = Hf2Data()
        self.cmap = Hf2ColorMap.jet()

    def resizeEvent(self, event):
        super(Hf2FracView, self).resizeEvent(event)
        self.fit_bounding()

    def fit_bounding(self):
        if self.__boundingRect is not None:
            self.view.fitInView(self.__boundingRect, QtCore.Qt.KeepAspectRatio)

    def draw(self, data):  # Do the Draw.
        self.scene.clear()
        if data is None:
            return
        # Load ColorMap
        cm = self.cmap
        lenUnit = "m"

        xrange = data.get_xrange()
        yrange = data.get_yrange()
        crange = data.get_crange()
        if xrange is None or yrange is None or crange is None:
            return
        xmin = xrange[0]
        ymin = yrange[0]
        xmax = xrange[1]
        ymax = yrange[1]
        if xmin >= xmax or ymin >= ymax:
            return

        mwid = max(xmax - xmin, ymax - ymin) * 1.01
        lWidthMax = mwid / 100.
        lWidthMin = lWidthMax / 20.

        if len(data.fractures) > 0:
            wmax = data.get_wmax()
            assert (wmax >= 0)
            # print('w_max = ', w_max)
            pmax = crange[1]
            pmin = crange[0]
            if pmax <= pmin:
                pmin = (crange[0] + crange[1]) - 0.5
                pmax = (crange[0] + crange[1]) + 0.5
            # add line ui
            for f in data.fractures:
                assert (len(f) == 6)
                # Get the Line Width For Plot
                w = f[4]
                assert (w >= 0)
                if wmax >= 1.0e-10:
                    w = w * lWidthMax / wmax + lWidthMin
                else:
                    w = (lWidthMax + lWidthMin) * 0.5
                # print('w = ', w)
                c = Hf2ColorMap.get_color(f[5], pmin, pmax, cm)
                x1 = f[0]
                y1 = ymin + ymax - f[1]
                x2 = f[2]
                y2 = ymin + ymax - f[3]
                item = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
                item.setPen(QtGui.QPen(c, w))
                self.scene.addItem(item)

        for inj in data.inlets:
            assert (len(inj) == 2)
            x = inj[0]
            y = ymin + ymax - inj[1]
            item = self.__addEllipse(x, y, mwid * 0.01, QtGui.QPen(QtCore.Qt.red, mwid * 0.003))
            item.setBrush(QtGui.QBrush(QtCore.Qt.green, QtCore.Qt.SolidPattern))

        # set the data and bounding rect
        self.__dataRect = QtCore.QRectF(QtCore.QPointF(xmin, ymin), QtCore.QPointF(xmax, ymax))
        margin = mwid * 0.05
        self.__boundingRect = self.__dataRect.adjusted(-margin, -margin, margin, margin)

        # add border
        self.scene.addRect(self.__dataRect, pen=QtGui.QPen(QtCore.Qt.darkGray, mwid * 0.001))
        self.scene.addRect(self.__boundingRect, pen=QtGui.QPen(QtCore.Qt.yellow, mwid * 0.001))

        # add text
        self.__addText(xmin, ymin, xmax, ymax, margin, lenUnit)

        # adjust view
        self.view.fitInView(self.__boundingRect, QtCore.Qt.KeepAspectRatio)

    def __addEllipse(self, x, y, r, pen):
        return self.scene.addEllipse(QtCore.QRectF(x - r, y - r, r * 2., r * 2.), pen=pen)

    def __addText(self, xmin, ymin, xmax, ymax, margin, lenUnit):
        font = QtGui.QFont("Times", 10)
        # left-top corner
        item = self.scene.addText("(%.2f, %.2f)" % (xmin, ymax), font=font)
        item.setScale(margin * 0.9 / item.boundingRect().height())
        item.setPos(QtCore.QPointF(xmin - margin, ymin - margin))
        # left-bottom corner
        item = self.scene.addText("(%.2f, %.2f)" % (xmin, ymin), font=font)
        item.setScale(margin * 0.9 / item.boundingRect().height())
        item.setPos(QtCore.QPointF(xmin - margin, ymax))
        # right-bottom corner
        item = self.scene.addText("(%.2f, %.2f)" % (xmax, ymin), font=font)
        item.setScale(margin * 0.9 / item.boundingRect().height())
        item.setPos(QtCore.QPointF(xmax + margin - item.mapRectToScene(item.boundingRect()).width(), ymax))
        # right-top corner
        item = self.scene.addText("Length Unit = {0}".format(lenUnit), font=font)
        item.setScale(margin * 0.9 / item.boundingRect().height())
        item.setPos(QtCore.QPointF(xmax + margin - item.mapRectToScene(item.boundingRect()).width(), ymin - margin))


class Fn2Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Fn2Widget, self).__init__(parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)

        self.fracture_view = Hf2FracView(self)
        v_layout.addWidget(self.fracture_view)

        h_layout = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit(self)
        self.path_edit.setReadOnly(True)
        h_layout.addWidget(self.path_edit)
        button = QtWidgets.QToolButton(self)
        button.setText('...')
        button.setIcon(load_icon('open.png'))
        button.clicked.connect(self.open_fn2_file_by_file_dialog)
        h_layout.addWidget(button)
        v_layout.addLayout(h_layout)

        self.__is_sleeping = False
        self.set_is_sleeping(False)

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.set_is_sleeping(not self.__is_sleeping)

    def set_is_sleeping(self, value):
        self.__is_sleeping = value
        if self.__is_sleeping:
            self.fracture_view.setStyleSheet(f"background-color:{QtGui.QColor(220, 220, 220).name()}")
            self.path_edit.setStyleSheet(f"background-color:{QtGui.QColor(220, 220, 220).name()}")
        else:
            self.fracture_view.setStyleSheet('')
            self.path_edit.setStyleSheet('')

    def open_fn2_file(self, filepath):
        if self.__is_sleeping:
            return
        succeed = False
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                text = file.read()
                data = Hf2Data()
                data.import_fractures(text, 4, 6)
                self.fracture_view.draw(data)
                self.path_edit.setText(filepath)
                succeed = True
        if not succeed:
            self.fracture_view.draw(Hf2Data())
            self.path_edit.setText("")

    def open_fn2_file_by_file_dialog(self):
        fpath, _ = QtWidgets.QFileDialog.getOpenFileName(self
                                                         , "请选择要导入的裂缝文件(至少4列数据，分别是X1 Y1 X2 Y2)"
                                                         , self.path_edit.text(),
                                                         "二维裂缝网络文件 (*.fn2);;文本文件 (*.txt);;All Files (*)")
        if len(fpath) > 0:
            self.set_is_sleeping(False)
            self.open_fn2_file(fpath)

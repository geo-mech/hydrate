# ** name = '二维裂缝查看'
# ** desc = '打开 .fn2 二维裂缝网络文件：图形化查看裂缝分布与压力着色（注册 gui.show_fn2 与 .fn2 文件类型）'
# ** enabled = True
"""二维裂缝（.fn2）可视化插件：``Fn2Widget`` 控件 + ``gui.show_fn2`` 命令 + ``.fn2`` 文件类型.

⚠️ **它是插件（可关闭）**：这个能力原先以 ``MainWindow.show_fn2`` 的形式常驻在
界面骨架里，并连带注册了 ``.fn2`` 文件处理器。控件本体原先住在 ``ui/tabs/fn2.py``。

**2026-10-22：整体并入本文件**（「完全自含」形态，见 ``plugins/AGENTS.md`` §0.2）——
``Fn2Widget`` 与它的 4 个辅助类（``GraphicsView`` / ``Hf2ColorMap`` / ``Hf2Data`` /
``Hf2FracView``）**只有本插件在用**，所以收进同一个文件：禁用本插件时连控件代码
一起不加载。

⚠️⚠️ **那条弃用警告是刻意保留的（不是漏改）**：原 ``MainWindow.show_fn2`` 方法体第一行
就有 :func:`zmlx.system.warn`，提示「``gui.show_fn2`` 将在 2026-3-5 后移除，请改用
``zmlx.plt.show_fn2``」。搬进来时**原样保留**。⚠️ 注意那个日期**早已过期**，
而 ``zmlx.plt.show_fn2``（matplotlib 版）与 ``Fn2Widget``（Qt 交互版）**不能互相替代**
—— 后者能双击暂停刷新、能点按钮换文件，前者只是画一张图。所以这条警告目前读出的是
「别在脚本里用 ``gui.show_fn2`` 画图」，查看 ``.fn2`` 文件的正当入口仍是本插件。

⚠️ 注册了两样东西（与原 ``MainWindow`` 时期一致）：

=========================  ============================================
注册物                      用途
=========================  ============================================
``gui.show_fn2``           命令（脚本可调，⚠️ 会发弃用警告）
``.fn2`` 文件类型           「文件 → 打开」选到 ``.fn2`` 时用本插件查看
=========================  ============================================

⚠️ **为什么直接在 ``setup_ui`` 里调 ``gui.add_file_handler`` 而不用 ``gui.reg_file_type``**：
``reg_file_type`` 的 ``widget_type`` 必须成对实现 ``set_data`` / ``get_data``，
而 ``Fn2Widget`` 用的是「载入文件」语义（``open_fn2_file``），没有这两个方法 ——
缺了会静默降级成空标签页。``reg_file_type`` 内部做的也就是
「``add_func`` + ``add_file_handler``」，直接做这两步结果一样且没有静默失败风险。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: ``MainWindow.show_fn2`` 与 ``ui/tabs/fn2.py``
    整体并入本插件；去掉 ``.fn2`` 那条内联处理器，改由本插件注册
"""

import os

from zmlx.system import execute_once, warn
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.settings import load_icon


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)

    def wheelEvent(self, event):
        t = 10.0
        if event.angleDelta().y() > 0:
            factor = (t + 1) / t
        else:
            factor = t / (t + 1)
        self.scale(factor, factor)


class Hf2ColorMap:
    @staticmethod
    def create_colormap(cmap):
        colors = []
        for i in range(cmap.N):
            c = [float(s) for s in cmap(i)]
            if len(c) >= 3:
                colors.append(QtGui.QColor(int(c[0] * 255), int(c[1] * 255),
                                           int(c[2] * 255)))
        return colors

    @staticmethod
    def get_color(cval, c_min, c_max, cmap):
        assert (len(cmap) > 0)
        i = int(((cval - c_min) / (c_max - c_min)) * len(cmap))
        if i >= len(cmap):
            return cmap[-1]
        if i < 0:
            return cmap[0]
        else:
            return cmap[i]

    @staticmethod
    def coolwarm():
        from matplotlib import cm
        return Hf2ColorMap.create_colormap(cm.coolwarm)

    @staticmethod
    def jet():
        from matplotlib import cm
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
        self.__dataRect = None
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
            self.view.fitInView(
                self.__boundingRect,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def draw(self, data):  # Do the Draw.
        self.scene.clear()
        if data is None:
            return
        # Load ColorMap
        cmap = self.cmap
        len_unit = "m"

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

        m_wid = max(xmax - xmin, ymax - ymin) * 1.01
        l_width_max = m_wid / 100.
        l_width_min = l_width_max / 20.

        if len(data.fractures) > 0:
            wmax = data.get_wmax()
            assert (wmax >= 0)
            # print('w_max = ', w_max)
            p_max = crange[1]
            p_min = crange[0]
            if p_max <= p_min:
                p_min = (crange[0] + crange[1]) - 0.5
                p_max = (crange[0] + crange[1]) + 0.5
            # add line ui
            for f in data.fractures:
                assert (len(f) == 6)
                # Get the Line Width For Plot
                w = f[4]
                assert (w >= 0)
                if wmax >= 1.0e-10:
                    w = w * l_width_max / wmax + l_width_min
                else:
                    w = (l_width_max + l_width_min) * 0.5
                # print('w = ', w)
                c = Hf2ColorMap.get_color(f[5], p_min, p_max, cmap)
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
            item = self.__add_ellipse(
                x, y, m_wid * 0.01,
                QtGui.QPen(QtCore.Qt.GlobalColor.red, m_wid * 0.003))
            item.setBrush(QtGui.QBrush(
                QtCore.Qt.GlobalColor.green,
                QtCore.Qt.BrushStyle.SolidPattern))

        # set the data and bounding rect
        self.__dataRect = QtCore.QRectF(QtCore.QPointF(xmin, ymin),
                                        QtCore.QPointF(xmax, ymax))
        margin = m_wid * 0.05
        self.__boundingRect = self.__dataRect.adjusted(
            -margin, -margin, margin, margin)

        # add border
        self.scene.addRect(
            self.__dataRect,
            pen=QtGui.QPen(QtCore.Qt.GlobalColor.darkGray, m_wid * 0.001))
        self.scene.addRect(
            self.__boundingRect,
            pen=QtGui.QPen(QtCore.Qt.GlobalColor.yellow, m_wid * 0.001))

        # add text
        self.__add_text(xmin, ymin, xmax, ymax, margin, len_unit)

        # adjust view
        self.view.fitInView(self.__boundingRect,
                            QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def __add_ellipse(self, x, y, r, pen):
        return self.scene.addEllipse(
            QtCore.QRectF(x - r, y - r, r * 2., r * 2.), pen=pen)

    def __add_text(self, xmin, ymin, xmax, ymax, margin, len_unit):
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
        item.setPos(QtCore.QPointF(
            xmax + margin - item.mapRectToScene(item.boundingRect()).width(),
            ymax))
        # right-top corner
        item = self.scene.addText("Length Unit = {0}".format(len_unit),
                                  font=font)
        item.setScale(margin * 0.9 / item.boundingRect().height())
        item.setPos(QtCore.QPointF(
            xmax + margin - item.mapRectToScene(item.boundingRect()).width(),
            ymin - margin))


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
        button.setIcon(load_icon('open'))
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
            self.fracture_view.setStyleSheet(
                f"background-color:{QtGui.QColor(220, 220, 220).name()}")
            self.path_edit.setStyleSheet(
                f"background-color:{QtGui.QColor(220, 220, 220).name()}")
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
        fpath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "请选择要导入的裂缝文件(至少4列数据，分别是X1 Y1 X2 Y2)",
            self.path_edit.text(),
            "二维裂缝网络文件 (*.fn2);;文本文件 (*.txt);;All Files (*)")
        if len(fpath) > 0:
            self.set_is_sleeping(False)
            self.open_fn2_file(fpath)


def show_fn2(filepath, **kwargs):
    """用 :class:`Fn2Widget` 打开一个 ``.fn2`` 二维裂缝网络文件.

    Args:
        filepath: ``.fn2`` 文件路径（至少 4 列：``X1 Y1 X2 Y2``，可带压力列）。
        **kwargs: 传给 ``gui.get_widget`` 的参数，常用的有 ``caption``
            （缺省 ``'Fractures'``）、``on_top``。

    ⚠️⚠️ **本函数会发 ``DeprecationWarning``** —— 与搬家前的
    ``MainWindow.show_fn2`` **完全一致**（那条警告是刻意保留的，理由见模块文档）。
    它针对的是「拿 ``gui.show_fn2`` 当绘图函数用」的旧脚本；查看 ``.fn2`` 文件的
    正当入口仍是本插件（「文件 → 打开」）。

    ⚠️ **命令名 ``show_fn2`` 不能改**：历史标签页里存着 ``gui.show_fn2(...)``。
    """
    from zmlx.ui import gui

    warn(
        'gui.show_fn2 will be removed after 2026-3-5, '
        'please use zmlx.plt.show_fn2 instead',
        DeprecationWarning,
        stacklevel=2,
    )

    if kwargs.get('caption') is None:
        kwargs['caption'] = 'Fractures'
    widget = gui.get_widget(the_type=Fn2Widget, **kwargs)
    if widget is not None:
        widget.open_fn2_file(filepath)


@execute_once(file=__file__)
def setup_ui():
    """注册 ``gui.show_fn2`` 与 ``.fn2`` 文件类型（插件被执行时调一次）."""
    from zmlx.ui import gui

    gui.add_func('show_fn2', show_fn2)
    gui.add_file_handler('二维裂缝', ['.fn2'], {'open_file': show_fn2})


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``extra_setups/*.py`` 则由
#    ``extra_setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python fn2_view.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()

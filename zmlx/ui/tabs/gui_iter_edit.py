"""GuiIterator 显示与编辑控件.

上部: 原生 Qt 绘制的迭代耗时曲线（:class:`_TimingChart`，双纵轴）
下部: 参数编辑 (ratio、清空 history 等)

通过 set_data(iter) 设置要显示/编辑的 GuiIterator 对象，
get_data() 获取当前对象。

绘图为什么用原生 Qt，而不是 MatplotWidget
------------------------------------------
本控件上半部分原来是 ``zmlx.ui.widget.plt.MatplotWidget``（matplotlib 画布）。但这里要
画的东西只有「一条折线 + 一串散点 + 双纵轴 + 一行标题」，matplotlib 太重了。下表都是在
它上面**实测**出来的（不是猜测）：

==========================================  ======================================
matplotlib（原方案）                         原生 Qt（:class:`_TimingChart`）
==========================================  ======================================
首次构造 MatplotWidget **约 460 ms**        构造一个 QWidget，**约 0.1 ms**
  ├ QtAgg 后端导入 93 ms                   （本模块不再 import matplotlib）
  ├ ``set_chinese_font()`` 284 ms
  └ ``plt.figure()`` 16 ms
每次重画 63 ms：``show_timing`` 35~39 ms    每次刷新只是把数据拷给一个 QWidget 并
  + ``canvas.draw()`` 26 ms                 ``update()``，**约 0.09 ms**；真正的绘制
                                            是 QPainter 画折线/散点，1000 点约 2 ms
``draw()`` 会顺手按 300 dpi 自动存档 PNG     没有存档行为（本控件不需要）
中文字体要靠 ``rcParams`` 折腾               直接用系统字体
配色是另一套体系                             坐标轴/文字/网格取自 :class:`QPalette`，
                                            跟随主题与暗色模式
``sizeHint`` 由内层 ``FigureCanvas``         本类自己说了算
决定，改不动
==========================================  ======================================

⚠️ **「首次 460 ms」才是本控件最刺眼的一处**：``GuiIterator._plot_timing()`` 在第一次
绘图时会**自动创建本标签页**，也就是求解一开始就在 GUI 线程上停半秒。换成原生 Qt 之后
这段开销彻底消失（实测 ``GuiIteratorEdit()`` 460 ms -> **3.2 ms**）。

⚠️ **说清楚省下的是什么**：matplotlib **模块本身**其实早在 ``import zmlx`` 时就被拉进来
了（实测），本控件省掉的不是那一步，而是**「第一个 MatplotWidget」才付的那笔懒加载**：
QtAgg 后端导入、``set_chinese_font()`` 建字体缓存、``plt.figure()`` 建画布 —— 合计约
400 ms，且只在本进程第一次构造绘图控件时付出（第二次只要 4 ms）。对「求解一开始就自动
建这个标签页」的场景，那笔开销正好落在最不该卡的时候。

⚠️ **本控件因此不再需要 v1.9.14 为 matplotlib 加的「按需重绘 + 延后一拍」那套机制**：
那套机制存在的唯一理由是「一次重画要 63 ms」；现在刷新只是拷数据 + ``update()``，所以
:meth:`GuiIteratorEdit.refresh` 直接同步做掉即可，代码反而更短。

⚠️ **仍然不要期望「学术图」**：本控件要的只是「看一眼每步的迭代 / 绘图耗时」。因此这里
没有缩放漫游、没有交互图例、没有导出 —— 那些能力仍由 ``MatplotWidget``（复杂图、多轴、
等值线、三维）承担。这个取舍与 ``check_count_view.py`` 的柱状图完全一致。

⚠️ ``set_data()`` **故意不重绘**：``GuiIterator._plot_timing()`` 会在**每个绘图周期**
调用它（按 ``ratio`` 节流到约 20% 的时间占比），若在那里重绘，长时间求解会以很高的频率
重绘界面。
"""

import math

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

# ---------------------------------------------------------------------------
# 绘图参数（全部是版式数值；颜色一律取自调色板，见 _TimingChart._colors）
# ---------------------------------------------------------------------------

#: 绘图区四周的留白（左 / 上 / 右 / 下），给刻度、标题与横轴名用。
#: 左右留得比较宽：两侧各有一条**竖排的纵轴标题**（``Iter Time (s)`` / ``Plot Time (s)``），
#: 外加各自一套纵轴刻度数字。
CHART_MARGIN = (78, 30, 82, 42)

#: 竖排纵轴标题占用的横向带宽（左右各一条）。
#:
#: ⚠️ 这条带子与刻度数字**分开占位**：纵轴标题回答「该看哪根轴」，刻度数字回答「具体是多少」，
#: 两者挤在一起就都看不清了。见 :meth:`_TimingChart._paint_axis_titles`。
CHART_AXIS_TITLE_BAND = 20

#: 控件的最小高度 / 向布局提出的偏好高度（像素）。
#:
#: ⚠️ 这两个值在 matplotlib 方案里是**改不动**的（那时 ``sizeHint`` 属于内层的
#: ``FigureCanvasQTAgg``）；原生控件没有这个问题，见 :meth:`_TimingChart.sizeHint`。
CHART_MIN_HEIGHT = 160
CHART_HINT_HEIGHT = 260

#: 纵轴（左右各一）分几段。
CHART_TICK_COUNT = 4

#: 横轴最多标几个刻度（步数多的时候全标会糊成一片）。
CHART_TICK_STEPS = 6

#: 折线线宽（像素）。
#:
#: ⚠️⚠️ **必须是 1**（而且是整数）—— 这是实测出来的一个大坑，不是随手取的：
#: Qt 的 raster 引擎对「宽度 <= 1」的画笔走画线快速路径，而对**更宽的画笔**要先把折线
#: 描边膨胀成一个填充多边形再栅格化。迭代耗时曲线是上下抖动的，膨胀出来的多边形自交
#: 非常严重，代价直接爆掉：
#:
#: ==================  ==============  ==============
#: 画笔                1000 点抖动      1000 点平滑
#: ==================  ==============  ==============
#: 宽 1.6 + 抗锯齿      **46.6 ms**     0.18 ms
#: 宽 2 + 抗锯齿        **49.1 ms**     -
#: 宽 1 + 抗锯齿        **0.34 ms**     0.04 ms
#: 宽 1 + 不抗锯齿      0.33 ms         0.04 ms
#: ==================  ==============  ==============
#:
#: 差了 **140 倍**：把线加粗一点点，代价比整张图其他部分加起来还大。
CHART_LINE_WIDTH = 1

#: 散点半径（像素）。
CHART_MARKER_RADIUS = 2.6

#: 没有数据时显示的提示。
NO_DATA_TEXT = '暂无迭代数据'


def _blend(color_a, color_b, ratio):
    """把两种颜色按比例混合（``ratio=0`` 全取 a，``1`` 全取 b）.

    Args:
        color_a: 起始色。
        color_b: 目标色。
        ratio: 混合比例（0~1，超出范围会被夹住）。

    Returns:
        QtGui.QColor: 混合结果。
    """
    ratio = min(max(float(ratio), 0.0), 1.0)
    return QtGui.QColor(
        int(color_a.red() + (color_b.red() - color_a.red()) * ratio),
        int(color_a.green() + (color_b.green() - color_a.green()) * ratio),
        int(color_a.blue() + (color_b.blue() - color_a.blue()) * ratio))


def _nice_step(raw):
    """返回不小于 ``raw`` 的「好看」刻度间隔（1 / 2 / 2.5 / 5 × 10ⁿ）.

    Args:
        raw: 期望的间隔（<= 0 时按 1 处理）。

    Returns:
        float: 刻度间隔。
    """
    if not raw > 0:
        return 1.0
    base = 10.0 ** math.floor(math.log10(raw))
    for multiple in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= multiple * base:
            return multiple * base
    return 10.0 * base


def _axis_ticks(top, count=CHART_TICK_COUNT):
    """给出纵轴刻度值（从 0 起、等间隔、上界不小于 ``top``）.

    Args:
        top: 数据最大值。
        count: 期望分几段。

    Returns:
        list: 升序刻度值列表，至少两个元素。
    """
    if not top > 0:
        return [0.0, 1.0]
    step = _nice_step(top / float(max(count, 1)))
    n = int(math.ceil(top / step - 1.0e-9))
    return [i * step for i in range(n + 1)]


def _format_value(value):
    """把刻度值格式化成紧凑的字符串（``%.4g``：0.0123 / 1.234 / 1234）."""
    return '%.4g' % value


def _readable(color, background, fallback, min_gap=48):
    """颜色与背景的明度差太小时，退回 ``fallback``.

    ⚠️ 用曲线的颜色去写刻度数字，是为了让读者一眼看出「这根轴对应哪条曲线」；但有些主题的
    ``Highlight`` 与背景很接近（例如很浅的强调色配白底），照原色写字会看不见 —— 此时宁可用
    主题的次要文字色，也不能让刻度消失。

    Args:
        color: 想用的颜色（曲线色）。
        background: 背景色。
        fallback: 对比度不足时改用的颜色（通常是 ``muted``）。
        min_gap: 允许的最小明度差（0~255）。

    Returns:
        QtGui.QColor: 最终使用的颜色。
    """
    if abs(color.lightness() - background.lightness()) < min_gap:
        return fallback
    return color


class _TimingChart(QtWidgets.QWidget):
    """迭代耗时曲线：左轴 = 迭代耗时（折线），右轴 = 绘图耗时（散点）.

    只画 :class:`GuiIterator` 记录的最近若干步，用于「看一眼趋势」，不做交互。

    配色分两套来源：

    - **坐标轴 / 文字 / 网格**：一律由 :class:`QPalette` 混合得出（跟随主题与暗色
      模式，绝不写死色值）；
    - **两条曲线**：以调色板的 ``Highlight``（本程序的强调色）为基色，第二条做色相
      旋转以便一眼分开；强调色本身几乎无彩度时退回「正文色往背景混」的中性线。
    """

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象。
        """
        super().__init__(parent)
        self._steps = []
        self._iter_times = []
        self._plot_steps = []
        self._plot_times = []
        self._title = ''
        self._placeholder = ''
        self.setMinimumHeight(CHART_MIN_HEIGHT)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)

    # ------------------------------------------------------------------
    # 尺寸（**这就是当初在 matplotlib 上改不动的东西**）
    # ------------------------------------------------------------------

    def sizeHint(self):
        """返回偏好尺寸。

        ⚠️ 用 matplotlib 时这个方法属于内层的 ``FigureCanvasQTAgg``（固定 480 px、
        改不动）；现在它是本类自己的方法，返回什么完全由本类说了算。
        """
        return QtCore.QSize(480, CHART_HINT_HEIGHT)

    def minimumSizeHint(self):
        """返回最小尺寸：宽度可以压得比较狠，高度不低于 :data:`CHART_MIN_HEIGHT`."""
        return QtCore.QSize(160, CHART_MIN_HEIGHT)

    # ------------------------------------------------------------------
    # 数据
    # ------------------------------------------------------------------

    def set_data(self, history, title=''):
        """设置要画的数据。

        Args:
            history: ``GuiIterator._history`` 的切片（调用方已按显示条数裁剪过），
                每个元素是 ``(step, t_iter, t_plot)``。
            title: 图上方的标题，通常是 :meth:`GuiIterator.time_info` 的结果。
        """
        self._steps = [h[0] for h in history]
        self._iter_times = [h[1] for h in history]
        # 绘图耗时只画 > 0 的点：0 表示「这一步没有绘图」，是缺数据而不是 0 秒
        self._plot_steps = [h[0] for h in history if h[2] > 0]
        self._plot_times = [h[2] for h in history if h[2] > 0]
        self._title = str(title or '')
        self._placeholder = ''
        self.update()

    def clear(self, placeholder=NO_DATA_TEXT):
        """清空曲线。

        Args:
            placeholder: 清空后居中显示的一句提示；空串表示什么都不显示。
        """
        self._steps = []
        self._iter_times = []
        self._plot_steps = []
        self._plot_times = []
        self._title = ''
        self._placeholder = str(placeholder or '')
        self.update()

    # ------------------------------------------------------------------
    # 几何换算
    # ------------------------------------------------------------------

    def _plot_rect(self):
        """返回真正的绘图区矩形（已扣掉四周留白）."""
        left, top, right, bottom = CHART_MARGIN
        return QtCore.QRectF(
            left, top,
            max(self.width() - left - right, 1),
            max(self.height() - top - bottom, 1))

    def _x_tick_indexes(self):
        """挑出要标在横轴上的数据下标（最多 :data:`CHART_TICK_STEPS` 个）.

        ⚠️ 横坐标按**下标**均匀铺开，而不是按 step 值：step 通常连续，两者等价；但历史
        被裁剪过时（``_history[-1000:]``）按下标铺开才不会让点挤成一团。

        Returns:
            list: 升序下标列表。
        """
        n = len(self._steps)
        if n <= CHART_TICK_STEPS:
            return list(range(n))
        step = (n - 1) / float(CHART_TICK_STEPS - 1)
        return sorted({int(round(i * step)) for i in range(CHART_TICK_STEPS)})

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        """画整个图；没有数据时画一句提示.

        Args:
            event: 绘制事件。
        """
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
            if not self._steps:
                if self._placeholder:
                    painter.setPen(self._colors()['muted'])
                    painter.drawText(self.rect(),
                                     int(QtCore.Qt.AlignmentFlag.AlignCenter),
                                     self._placeholder)
            else:
                self._paint_chart(painter)
        finally:
            # ⚠️ 必须 end()：不结束会让 Qt 报警告，严重时影响绘制
            painter.end()

    def _colors(self):
        """从当前调色板取出一套配色（**不写死任何色值**）.

        ============  ======================================================
        text          正文色（``WindowText``）
        muted         次要文字（刻度、提示）：正文色往背景混 45%
        axis          坐标轴：往背景混 62%（比 muted 再淡一档）
        grid          网格：背景往 muted 混 35%
        iter          迭代耗时曲线：``Highlight``（本程序的强调色）
        plot          绘图耗时散点：``Highlight`` 转 150° 色相
        ============  ======================================================

        ⚠️ **为什么不直接写死原来 matplotlib 用过的 ``#4A90A4`` / ``#C76464``**：本程序
        会加载用户可编辑的 ``zml_window_style.qss``，还有暗色模式；坐标轴与文字一旦写死
        色值，换个主题就可能看不见。色相旋转得到的第二条线仍然「只在调色板内部取值」，
        所以亮色 / 暗色都能自动跟随。

        Returns:
            dict: 颜色字典。
        """
        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)

        # ⚠️ 背景取 Base 与 Window 中**较亮**的那个：本控件实际画在窗口底色上，而暗色
        #    主题下 Base 可能比 Window 还暗 —— 取亮的那个，「往它上面写字 / 从它出发
        #    调色」的方向才总是对的。
        background = base if base.lightness() >= window.lightness() else window

        muted = _blend(text, background, 0.45)
        axis = _blend(text, background, 0.62)
        grid = _blend(background, muted, 0.35)

        # 图例底色：与背景同色但半透明 —— 压在网格线上也看得清，又不至于像贴了块补丁
        legend_bg = QtGui.QColor(background)
        legend_bg.setAlpha(215)

        return {
            'text': text,
            'muted': muted,
            'axis': axis,
            'grid': grid,
            'background': background,
            'legend_bg': legend_bg,
            'iter': QtGui.QColor(highlight),
            'plot': self._second_color(highlight, background, text),
        }

    @staticmethod
    def _second_color(highlight, background, text):
        """第二条曲线的颜色：把强调色转个色相，保证两条线一眼能分开.

        ⚠️ 强调色本身几乎没彩度时（某些主题的 ``Highlight`` 是灰的），色相旋转没有
        意义，此时退回「正文色往背景里混」得到一条中性深/浅线，两种主题下都看得清。

        Args:
            highlight: 调色板的强调色。
            background: 当前背景色。
            text: 正文色。

        Returns:
            QtGui.QColor: 第二条曲线的颜色。
        """
        hue, sat, val, alpha = highlight.getHsv()
        if sat < 50 or hue < 0:
            return _blend(text, background, 0.25)
        return QtGui.QColor.fromHsv((hue + 150) % 360, sat, val, alpha)

    def _small_font(self):
        """返回比默认小一号的字体（刻度、刻度数字与图例用）."""
        font = self.font()
        size = font.pointSizeF()
        if size > 0:
            font.setPointSizeF(max(size - 1.0, 6.0))
        return font

    def _paint_chart(self, painter):
        """画标题、网格、双纵轴刻度、两条竖排纵轴标题、两条曲线与图例.

        绘制顺序：标题 -> 横向网格 + 左侧刻度 -> 坐标轴 -> 右侧刻度 -> 横轴刻度与
        ``Step`` -> 左右轴标题 -> 折线 -> 散点 -> 图例。曲线画在网格之后，图例画在最上层。

        Args:
            painter: 画笔。
        """
        colors = self._colors()
        plot = self._plot_rect()

        # 刻度数字用**对应曲线的颜色**：这样「蓝线看左轴、红点看右轴」不用猜。
        # 色与底太接近时退回 muted（见 _readable）。
        iter_text = _readable(colors['iter'], colors['background'], colors['muted'])
        plot_text = _readable(colors['plot'], colors['background'], colors['muted'])

        # ---- 纵轴刻度（左右各一套，各自独立定标）----
        left_ticks = _axis_ticks(max(self._iter_times) if self._iter_times else 0.0)
        right_ticks = _axis_ticks(max(self._plot_times) if self._plot_times else 0.0)
        left_top = left_ticks[-1]
        right_top = right_ticks[-1]

        def y_iter(value):
            return plot.bottom() - plot.height() * (value / left_top)

        def y_plot(value):
            return plot.bottom() - plot.height() * (value / right_top)

        # ---- 标题 ----
        painter.setFont(self.font())
        painter.setPen(colors['text'])
        painter.drawText(
            QtCore.QRectF(0, 2, self.width(), CHART_MARGIN[1] - 4),
            int(QtCore.Qt.AlignmentFlag.AlignCenter |
                QtCore.Qt.AlignmentFlag.AlignVCenter),
            self._title)

        # ---- 横向网格 + 左侧刻度 ----
        # 刻度数字的可用横向范围：紧挨着绘图区，但要把最外边那条竖排轴标题让出来
        tick_left_x = 4 + CHART_AXIS_TITLE_BAND + 6
        tick_left_w = max(plot.left() - 6 - tick_left_x, 12)
        tick_right_x = plot.right() + 6
        tick_right_w = max(self.width() - 4 - CHART_AXIS_TITLE_BAND - 6 - tick_right_x, 12)

        painter.setFont(self._small_font())
        metrics = painter.fontMetrics()
        for value in left_ticks:
            y = y_iter(value)
            painter.setPen(QtGui.QPen(colors['grid'], 1))
            painter.drawLine(QtCore.QPointF(plot.left(), y),
                             QtCore.QPointF(plot.right(), y))
            painter.setPen(iter_text)
            painter.drawText(
                QtCore.QRectF(tick_left_x, y - metrics.height() / 2.0,
                              tick_left_w, metrics.height()),
                int(QtCore.Qt.AlignmentFlag.AlignRight |
                    QtCore.Qt.AlignmentFlag.AlignVCenter),
                metrics.elidedText(_format_value(value),
                                   QtCore.Qt.TextElideMode.ElideRight,
                                   int(tick_left_w)))

        # ---- 坐标轴 ----
        painter.setPen(QtGui.QPen(colors['axis'], 1))
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())
        painter.drawLine(plot.topLeft(), plot.bottomLeft())
        painter.drawLine(plot.topRight(), plot.bottomRight())

        # ---- 右侧刻度（绘图耗时）----
        painter.setPen(plot_text)
        for value in right_ticks:
            y = y_plot(value)
            painter.drawText(
                QtCore.QRectF(tick_right_x, y - metrics.height() / 2.0,
                              tick_right_w, metrics.height()),
                int(QtCore.Qt.AlignmentFlag.AlignLeft |
                    QtCore.Qt.AlignmentFlag.AlignVCenter),
                metrics.elidedText(_format_value(value),
                                   QtCore.Qt.TextElideMode.ElideRight,
                                   int(tick_right_w)))

        # ---- 左右两条竖排纵轴标题（**该看哪根轴，就看这里**）----
        self._paint_axis_titles(painter, plot, iter_text, plot_text)

        # ---- 横轴刻度（step）----
        n = len(self._steps)
        slot = plot.width() / float(max(n - 1, 1))
        for index in self._x_tick_indexes():
            x = plot.left() + (0 if n <= 1 else index * slot)
            label = str(self._steps[index])
            width = int(max(max(slot, 24), metrics.horizontalAdvance(label) + 8))
            painter.drawText(
                QtCore.QRectF(x - width / 2.0, plot.bottom() + 4,
                              width, metrics.height()),
                int(QtCore.Qt.AlignmentFlag.AlignHCenter |
                    QtCore.Qt.AlignmentFlag.AlignTop),
                label)
        painter.drawText(
            QtCore.QRectF(plot.left(), plot.bottom() + metrics.height() + 6,
                          plot.width(), metrics.height()),
            int(QtCore.Qt.AlignmentFlag.AlignHCenter |
                QtCore.Qt.AlignmentFlag.AlignTop),
            'Step')

        # ---- 迭代耗时：折线 ----
        points = [QtCore.QPointF(plot.left() + (0 if n <= 1 else i * slot),
                                 y_iter(self._iter_times[i]))
                  for i in range(n)]
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        if len(points) >= 2:
            painter.setPen(QtGui.QPen(colors['iter'], CHART_LINE_WIDTH))
            painter.drawPolyline(QtGui.QPolygonF(points))
        else:
            # 只有一个点时折线画不出来，用一个小圆点表示
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QBrush(colors['iter']))
            painter.drawEllipse(points[0], CHART_MARKER_RADIUS,
                                CHART_MARKER_RADIUS)

        # ---- 绘图耗时：散点（只画 > 0 的点）----
        index_of = {step: i for i, step in enumerate(self._steps)}
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(colors['plot']))
        for step, value in zip(self._plot_steps, self._plot_times):
            index = index_of.get(step)
            if index is None:
                continue
            painter.drawEllipse(
                QtCore.QPointF(plot.left() + (0 if n <= 1 else index * slot),
                               y_plot(value)),
                CHART_MARKER_RADIUS, CHART_MARKER_RADIUS)

        # ---- 图例 ----
        self._paint_legend(painter, plot, colors)

    def _paint_axis_titles(self, painter, plot, iter_text, plot_text):
        """画左右两条**竖排的纵轴标题**（``Iter Time (s)`` / ``Plot Time (s)``）.

        ⚠️ 这不是装饰：本图有**两套纵轴**，不写清楚哪条曲线看哪根轴，读者就只能看到
        「一条线 + 一串点」，不知道该拿哪个刻度去读它。标题用对应曲线的颜色，与图例里
        样例的色一致，于是「蓝线 <-> 左轴」「红点 <-> 右轴」一眼可辨（matplotlib 版本
        原本也是这样：``set_ylabel(..., color=...)`` + ``tick_params(labelcolor=...)``）。

        Args:
            painter: 画笔。
            plot: 绘图区矩形。
            iter_text: 左轴标题颜色（迭代耗时的曲线色）。
            plot_text: 右轴标题颜色（绘图耗时的曲线色）。
        """
        if plot.width() < 60:
            return  # 太窄：标题会压到曲线上，宁可不画
        band = CHART_AXIS_TITLE_BAND
        self._paint_rotated_text(
            painter, QtCore.QRectF(4, plot.top(), band, plot.height()),
            'Iter Time (s)', iter_text)
        self._paint_rotated_text(
            painter,
            QtCore.QRectF(self.width() - 4 - band, plot.top(),
                          band, plot.height()),
            'Plot Time (s)', plot_text)

    @staticmethod
    def _paint_rotated_text(painter, rect, text, color):
        """在竖条 ``rect`` 里画一段旋转 -90° 的文字（自下而上读）.

        Args:
            painter: 画笔。
            rect: 文字所占的竖条区域。
            text: 要画的文字。
            color: 文字颜色。
        """
        painter.save()
        try:
            painter.setPen(color)
            painter.translate(rect.center())
            painter.rotate(-90)
            # 旋转之后，原来的「高」变成横轴、「宽」变成纵轴
            painter.drawText(
                QtCore.QRectF(-rect.height() / 2.0, -rect.width() / 2.0,
                              rect.height(), rect.width()),
                int(QtCore.Qt.AlignmentFlag.AlignCenter),
                text)
        finally:
            painter.restore()

    def _paint_legend(self, painter, plot, colors):
        """在绘图区右上角画图例（两条曲线的名字）.

        ⚠️ 图例只负责「颜色 <-> 曲线名」的对应；**「该看哪根轴」由两侧的竖排轴标题回答**
        （见 :meth:`_paint_axis_titles`）—— 两者分工不同，不能只留一个。

        Args:
            painter: 画笔。
            plot: 绘图区矩形。
            colors: 颜色字典。
        """
        painter.setFont(self._small_font())
        metrics = painter.fontMetrics()
        items = (('iter', 'Iter Time (s)'), ('plot', 'Plot Time (s)'))

        sample_w = 18
        text_w = max(metrics.horizontalAdvance(text) for _, text in items)
        row_h = metrics.height() + 2
        box_w = sample_w + 6 + text_w + 12
        box_h = row_h * len(items) + 10
        box = QtCore.QRectF(plot.right() - box_w - 6, plot.top() + 6,
                            box_w, box_h)
        if box.left() < plot.left() or box.bottom() > plot.bottom():
            return  # 绘图区太窄/太矮，宁可不画图例

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(colors['legend_bg']))
        painter.drawRoundedRect(box, 4, 4)

        y = box.top() + 5
        for key, text in items:
            mid = y + row_h / 2.0
            x0 = box.left() + 6
            if key == 'iter':
                painter.setPen(QtGui.QPen(colors['iter'], CHART_LINE_WIDTH))
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawLine(QtCore.QPointF(x0, mid),
                                 QtCore.QPointF(x0 + sample_w, mid))
            else:
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QBrush(colors['plot']))
                painter.drawEllipse(
                    QtCore.QPointF(x0 + sample_w / 2.0, mid),
                    CHART_MARKER_RADIUS + 0.8, CHART_MARKER_RADIUS + 0.8)
            painter.setPen(colors['text'])
            painter.drawText(
                QtCore.QRectF(x0 + sample_w + 6, y, text_w, row_h),
                int(QtCore.Qt.AlignmentFlag.AlignLeft |
                    QtCore.Qt.AlignmentFlag.AlignVCenter),
                text)
            y += row_h


class GuiIteratorEdit(QtWidgets.QWidget):
    """GuiIterator 可视化面板.

    依赖:
        - zmlx.utils.gui_iterator: GuiIterator, get_gui_iter
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._iter = None
        self._build_ui()
        self.set_data(None)  # 默认使用全局单例

    def set_data(self, data):
        """设置要显示/编辑的 GuiIterator 对象.

        ⚠️ 本方法**只同步参数与状态文字，不重绘图表**（见模块文档：它会被
        ``GuiIterator._plot_timing()`` 在每个绘图周期调用）。

        Args:
            data: GuiIterator 实例，None 则使用全局单例 get_gui_iter().
        """
        if data is None:
            from zmlx.utils.gui_iterator import get_gui_iter
            data = get_gui_iter()
        self._iter = data
        self._sync_from_iter()

    def get_data(self):
        """获取当前的 GuiIterator 对象."""
        return self._iter

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 上部: 耗时曲线图（原生 Qt 控件，构造 ≈ 0.1 ms）──
        self._chart = _TimingChart()
        self._chart.clear(NO_DATA_TEXT)
        layout.addWidget(self._chart, 1)

        # ── 下部: 参数 / 操作（可水平滚动）──
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(60)

        ctrl = QtWidgets.QWidget()
        ctrl_layout = QtWidgets.QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(8, 4, 8, 4)
        ctrl_layout.setSpacing(4)

        ctrl_layout.addWidget(QtWidgets.QLabel('绘图比例:'))

        self._ratio_spin = QtWidgets.QDoubleSpinBox()
        self._ratio_spin.setRange(0.001, 0.3)
        self._ratio_spin.setDecimals(3)
        self._ratio_spin.setSingleStep(0.01)
        self._ratio_spin.setToolTip('GUI 绘图占总时长的比例 (0.001~0.3)')
        self._ratio_spin.valueChanged.connect(self._on_ratio_changed)
        ctrl_layout.addWidget(self._ratio_spin)

        ctrl_layout.addWidget(QtWidgets.QLabel('最大绘图间隔:'))

        self._max_interval_spin = QtWidgets.QSpinBox()
        self._max_interval_spin.setRange(0, 10000)
        self._max_interval_spin.setSpecialValueText('不限制')
        self._max_interval_spin.setToolTip('最大绘图间隔 (step 数)，0 = 不限制')
        self._max_interval_spin.valueChanged.connect(self._on_max_interval_changed)
        ctrl_layout.addWidget(self._max_interval_spin)

        self._btn_clear = QtWidgets.QPushButton('清空历史')
        self._btn_clear.clicked.connect(self._on_clear_history)
        ctrl_layout.addWidget(self._btn_clear)

        self._btn_refresh = QtWidgets.QPushButton('刷新图表')
        self._btn_refresh.clicked.connect(self._on_refresh)
        ctrl_layout.addWidget(self._btn_refresh)

        self._status = QtWidgets.QLabel()
        ctrl_layout.addWidget(self._status)

        ctrl_layout.addStretch()
        scroll.setWidget(ctrl)
        layout.addWidget(scroll)

    def _sync_from_iter(self):
        """将控件值同步到当前 GuiIterator."""
        if self._iter is None:
            return
        self._ratio_spin.blockSignals(True)
        self._ratio_spin.setValue(self._iter.ratio)
        self._ratio_spin.blockSignals(False)
        self._max_interval_spin.blockSignals(True)
        self._max_interval_spin.setValue(
            self._iter.max_plot_interval
            if self._iter.max_plot_interval is not None else 0)
        self._max_interval_spin.blockSignals(False)
        self._update_status()

    def _on_ratio_changed(self, value):
        if self._iter is not None:
            self._iter.ratio = value

    def _on_max_interval_changed(self, value):
        if self._iter is not None:
            self._iter.max_plot_interval = value if value > 0 else None

    def _on_clear_history(self):
        if self._iter is not None:
            self._iter._history.clear()
            self._iter._step = 0
            self._iter._step_last_plot = None
            self._chart.clear(NO_DATA_TEXT)
            self._update_status()

    def _on_refresh(self):
        """「刷新图表」按钮：显式重绘."""
        self._sync_from_iter()
        self._refresh_chart()

    def _refresh_chart(self):
        """把最新的 history 交给图表（**微秒级，因此可以同步做**）.

        只取最近 ``_max_history_shown`` 条：与原来 ``show_timing`` 的裁剪一致。
        """
        it = self._iter
        if it is None:
            return
        if len(it._history) < 2:
            self._chart.clear(NO_DATA_TEXT)  # 数据不足以成线
            return
        self._chart.set_data(it._history[-it._max_history_shown:], it.time_info())

    def _update_status(self):
        if self._iter is None:
            return
        self._status.setText(
            f'Step: {self._iter._step}  |  '
            f'Iter: {self._iter._time_iter:.2f}s  |  '
            f'Plot: {self._iter._time_plot:.2f}s  |  '
            f'History: {len(self._iter._history)}')

    def refresh(self):
        """框架的被动刷新：切到本页 / 菜单「操作 → 刷新」时调用.

        ⚠️ 为什么这里可以**同步**画图、而不用 v1.9.14 那套「延后一拍」：那时一次重画要
        63 ms（matplotlib 重建整张图 + 绘制画布），现在没有那个开销了 —— 这里只是把
        history 拷给一个 QWidget 并 ``update()``，真正的绘制由 Qt 自己调度。因此本方法
        必须便宜（``MainWindow.refresh`` 在每次切标签页时都会调它），实测约 0.1 ms。
        """
        self._sync_from_iter()
        self._refresh_chart()

    @staticmethod
    def test():
        """手工查看本控件：塞一段合成数据，让曲线有东西可看."""
        import sys
        app = QtWidgets.QApplication(sys.argv)
        try:
            from zmlx.utils.gui_iterator import get_gui_iter
            it = get_gui_iter()
            for step in range(1, 301):
                t_iter = 0.02 + 0.006 * math.sin(step * 0.07)
                t_plot = 0.004 if step % 10 == 0 else 0.0
                it._history.append((step, t_iter, t_plot))
                it._step = step
                it._time_iter += t_iter
                it._time_plot += t_plot
        except Exception as err:
            print(f'Error (when fill test data): {err}')
        w = GuiIteratorEdit()
        w.resize(900, 600)
        w.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    GuiIteratorEdit.test()

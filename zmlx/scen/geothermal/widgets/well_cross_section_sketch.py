"""井截面取热的**模型示意图**（``WellCrossSectionSketch``）：把参数画成一张 x–z 剖面图.

配合 ``well_cross_section.WellCrossSectionWidget`` 使用：坐在参数表单右侧，
把当前参数对应的几何画出来 —— 「x 方向范围」「井在哪」「网格多密」这些
看文字要脑补的东西，直接见图。

画什么、对应哪个参数
--------------------

=====================  ==================================================
图上的东西              来源参数
=====================  ==================================================
矩形外框                 ``xr`` / ``zr``（计算域范围），四角标最小/最大值
框内网格线               ``jx`` / ``jz``（网格数；只画示意，不全画）
井（圆点 + 十字）         ``well_pos``（圆心 x、z）
井筒圆                   ``well_d``（直径，见下面的「示意放大」）
=====================  ==================================================

⚠️ **井筒直径是按示意画的，不是真实比例**：默认 ``well_d=0.2`` m，而计算域是
100 m 见方 —— 真实比例下它只有 0.2% 宽，画出来是个看不见的点。所以井筒圆取
「至少占短边的 1/40」，并在旁边标出真实直径数值；图的一角另有说明。

⚠️ **网格线是示意，不是全画**：``jx=jz=100`` 时全画会是糊成一片的黑块。实际只画
最多 ``MAX_GRID_LINES`` 条，并在标题里写出真实网格数。

⚠️ 参数填得不合法时（如 ``jx=abc``）**不报错、不崩**：图按「这份参数画不出来，退回默认」
处理，并在图上写一行灰字说明 —— 示意图不该成为输入的拦路虎。
"""

from zmlx.ui.pyqt import QtWidgets


class _Style:
    """示意图的配色与尺寸（不实例化，纯粹当命名空间用）.

    ⚠️ 颜色**显式指定**、不读主题：示意图是自成一体的说明图，与窗口主题联动反而
    在暗色下看不清。深色线条 + 浅色底在任何主题里都清楚。
    """

    #: 画布背景（与 matplotlib 默认的 figure 底色分开，避免暗色主题下白底刺眼）
    FACE = '#ffffff'
    #: 计算域边框
    DOMAIN = '#1f77b4'
    #: 网格线
    GRID = '#cccccc'
    #: 井
    WELL = '#d62728'
    #: 尺寸标注 / 文字
    ANNOT = '#333333'
    #: 提示性小字
    HINT = '#888888'


class _Limit:
    """画图用的规模上限（不实例化，纯粹当命名空间用）."""

    #: 最多画多少条网格线（每边）。再多就糊成一片了。
    MAX_GRID_LINES = 20
    #: 井筒圆的最小视觉半径：占画布短边的比例（保证再细的井也看得见）
    MIN_WELL_RATIO = 1.0 / 40.0


class WellCrossSectionSketch(QtWidgets.QWidget):
    """把井截面取热的几何参数画成一张示意图.

    Args:
        parent: Qt 父控件。

    Note:
        对外的唯一入口是 :meth:`set_params`；它接收**已经解析好的**参数字典
        （缺省项用默认值），不负责解析文本 —— 解析归
        ``well_cross_section.WellCrossSectionWidget``。
    """

    #: 三张默认值，与 ``_well_cross_section.create`` 的默认一致。
    DEFAULT_XR = (-50.0, 50.0)
    DEFAULT_ZR = (-50.0, 50.0)
    DEFAULT_JX = 100
    DEFAULT_JZ = 100
    DEFAULT_WELL_POS = (0.0, 0.0)
    DEFAULT_WELL_D = 0.2

    def __init__(self, parent=None):
        """建一个空的示意图控件（先按默认参数画一张）."""
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        from zmlx.ui.widgets.plt import MatplotWidget

        self._plot = MatplotWidget(self)
        layout.addWidget(self._plot)

        #: 当前要画的参数（键与小写 :meth:`set_params` 一致）
        self._params = {}
        self.set_params({})

    def set_params(self, params):
        """按给定参数重画示意图.

        Args:
            params: 参数字典，键取自 ``create`` 的关键字参数，缺省项用默认值。
                只需要这五项：``jx`` / ``jz`` / ``xr`` / ``zr`` / ``well_pos`` / ``well_d``；
                其余键被忽略（岩石物性、渗透率等画不到图上）。

        Note:
            刻意**不做**合法性校验：值不对时按「用默认值画」处理并在图上提示。
            校验是输入框那一侧的事，示意图不该抛异常打断用户输入。
        """
        self._params = dict(params)
        self._redraw()

    def refresh(self):
        """GUI 刷新钩子：重画一次（本控件无外部数据，重画即可）."""
        self._redraw()

    # ── 内部 ────────────────────────────────────────────────────────

    def _redraw(self):
        """取参数 → 画到 MatplotWidget 上（**必须在 GUI 线程**）."""
        view = self._compute_view()
        self._plot.plot_on_figure(
            lambda fig: self._draw(fig, view), savefig=False)

    def _compute_view(self):
        """把原始参数整理成「可以直接画」的一组数值，非法时退回默认.

        Returns:
            dict: ``{'xr':(lo,hi), 'zr':(lo,hi), 'jx':int, 'jz':int,
            'well':(x,z), 'well_d':float, 'hints':[str]}``。
            ``hints`` 是非空列表时，说明有参数被忽略了（会画在图上）。
        """
        hints = []
        p = self._params

        # ⚠️ ``xr`` / ``zr`` 是**区间**（要求 hi > lo），``well_pos`` 是**坐标点**
        #    （两个数任意大小都合法 —— ``(5, -10)`` 这种「x 正、z 负」的井位完全正常）。
        #    两条规则不同，所以 ``_pair`` 要区分 ``ordered``。
        xr = self._pair(p.get('xr'), self.DEFAULT_XR, 'xr', hints, ordered=True)
        zr = self._pair(p.get('zr'), self.DEFAULT_ZR, 'zr', hints, ordered=True)
        well = self._pair(p.get('well_pos'), self.DEFAULT_WELL_POS, 'well_pos',
                          hints, ordered=False)
        jx = self._positive_int(p.get('jx'), self.DEFAULT_JX, 'jx', hints)
        jz = self._positive_int(p.get('jz'), self.DEFAULT_JZ, 'jz', hints)
        well_d = self._positive_float(p.get('well_d'), self.DEFAULT_WELL_D, 'well_d', hints)

        return dict(xr=xr, zr=zr, jx=jx, jz=jz, well=well, well_d=well_d, hints=hints)

    @staticmethod
    def _pair(value, default, name, hints, *, ordered):
        """解析二元组参数；不合法时返回默认值并记一条提示.

        Args:
            value: 待解析的值，``None`` 表示没给（用 ``default``）。
            default: 默认值。
            name: 参数名（记进 ``hints``）。
            hints: 提示列表，不合法时往里追加 ``name``。
            ordered: ``True`` 表示这是**区间**（``xr`` / ``zr``，必须 ``hi > lo``）；
                ``False`` 表示这是**坐标点**（``well_pos``，两个数任意大小都合法）。

        Returns:
            tuple[float, float]: 解析出的两个数。
        """
        if value is None:
            return default
        try:
            lo, hi = float(value[0]), float(value[1])
            if ordered and not hi > lo:
                raise ValueError
            return lo, hi
        except (TypeError, ValueError, IndexError):
            hints.append(name)
            return default

    @staticmethod
    def _positive_int(value, default, name, hints):
        """解析正整数参数；不合法时返回默认值并记一条提示.

        ``None``（没给）直接返回默认值、**不算错误** —— 与 :meth:`_pair` 一致：
        界面上留空本来就表示「用默认值」，不该画上一行「参数无法解析」。
        """
        if value is None:
            return default
        try:
            iv = int(value)
            if iv <= 0:
                raise ValueError
            return iv
        except (TypeError, ValueError):
            hints.append(name)
            return default

    @staticmethod
    def _positive_float(value, default, name, hints):
        """解析正浮点参数；不合法时返回默认值并记一条提示.

        ``None``（没给）直接返回默认值、**不算错误** —— 与 :meth:`_pair` 一致。
        """
        if value is None:
            return default
        try:
            fv = float(value)
            if not fv > 0:
                raise ValueError
            return fv
        except (TypeError, ValueError):
            hints.append(name)
            return default

    def _draw(self, fig, view):
        """在给定 figure 上把示意图画出来（matplotlib 回调）.

        Args:
            fig: matplotlib ``Figure``。
            view: :meth:`_compute_view` 的返回值。
        """
        fig.clear()
        fig.patch.set_facecolor(_Style.FACE)
        ax = fig.add_subplot(111)
        ax.set_facecolor(_Style.FACE)

        x0, x1 = view['xr']
        z0, z1 = view['zr']
        jx, jz = view['jx'], view['jz']
        wx, wz = view['well']
        well_d = view['well_d']

        # ① 计算域外框
        import matplotlib.patches as mpatches

        ax.add_patch(mpatches.Rectangle(
            (x0, z0), x1 - x0, z1 - z0,
            fill=False, edgecolor=_Style.DOMAIN, linewidth=2))

        # ② 网格线（示意，最多 MAX_GRID_LINES 条）
        span_x, span_z = x1 - x0, z1 - z0
        nx = min(jx, _Limit.MAX_GRID_LINES)
        nz = min(jz, _Limit.MAX_GRID_LINES)
        for i in range(1, nx):
            x = x0 + span_x * i / nx
            ax.plot([x, x], [z0, z1], color=_Style.GRID, linewidth=0.6, zorder=1)
        for i in range(1, nz):
            z = z0 + span_z * i / nz
            ax.plot([x0, x1], [z, z], color=_Style.GRID, linewidth=0.6, zorder=1)

        # ③ 井：圆心 + 十字 + 示意放大的井筒圆
        #    ⚠️ 井可能在 xr/zr 之外（用户在输入途中或真填错了）：这时**仍然画**
        #    （坐标轴会包住它），否则用户看不到井、也不知道自己填的位置离家多远。
        well_inside = (x0 <= wx <= x1) and (z0 <= wz <= z1)
        ax.plot([wx], [wz], marker='o', color=_Style.WELL, markersize=6, zorder=5)
        arm = min(span_x, span_z) * 0.03
        ax.plot([wx - arm, wx + arm], [wz, wz], color=_Style.WELL, linewidth=1, zorder=5)
        ax.plot([wx, wx], [wz - arm, wz + arm], color=_Style.WELL, linewidth=1, zorder=5)
        r_visual = max(well_d / 2.0, min(span_x, span_z) * _Limit.MIN_WELL_RATIO)
        ax.add_patch(mpatches.Circle(
            (wx, wz), r_visual, fill=False, edgecolor=_Style.WELL,
            linewidth=1.2, linestyle='--', zorder=4))

        # ④ 坐标范围：把井也包进来，井跑到域外时图才有意义
        lo_x, hi_x = min(x0, wx), max(x1, wx)
        lo_z, hi_z = min(z0, wz), max(z1, wz)
        pad_x = (hi_x - lo_x) * 0.08
        pad_z = (hi_z - lo_z) * 0.08
        ax.set_xlim(lo_x - pad_x, hi_x + pad_x)
        ax.set_ylim(lo_z - pad_z, hi_z + pad_z)
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('x / m', color=_Style.ANNOT, fontsize=9)
        ax.set_ylabel('z / m', color=_Style.ANNOT, fontsize=9)
        ax.tick_params(colors=_Style.ANNOT, labelsize=8)

        ax.set_title(
            'x–z 剖面：{0:.0f} m × {1:.0f} m，网格 {2}×{3}'.format(
                span_x, span_z, jx, jz),
            color=_Style.ANNOT, fontsize=10)

        # ⚠️ 所有补充文字都放进**图内的白底框**里：放到坐标轴外面会被 x/y 轴标签
        #    和刻度挤掉（实测过，图上糊成一团）。
        box_kw = dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='#dddddd', alpha=0.92, zorder=6)
        ax.annotate(
            '域 x: [{0:g}, {1:g}]'.format(x0, x1),
            xy=(0.01, 0.99), xycoords='axes fraction',
            ha='left', va='top', color=_Style.ANNOT, fontsize=8, bbox=box_kw)
        ax.annotate(
            '域 z: [{0:g}, {1:g}]'.format(z0, z1),
            xy=(0.01, 0.90), xycoords='axes fraction',
            ha='left', va='top', color=_Style.ANNOT, fontsize=8, bbox=box_kw)
        # ⚠️ 不用 '⌀'（U+2300）：SimHei 等中文字体里没有这个字形，会画成方框
        ax.annotate(
            '井 ({0:g}, {1:g})，直径 {2:g} m'.format(wx, wz, well_d),
            xy=(wx, wz), xytext=(10, 12),
            textcoords='offset points', color=_Style.WELL, fontsize=9, bbox=box_kw)
        ax.annotate(
            '井筒圆为示意放大',
            xy=(0.99, 0.01), xycoords='axes fraction',
            ha='right', va='bottom', color=_Style.HINT, fontsize=7, bbox=box_kw)

        # 井落在计算域之外：这是**真正的配置错误**，要显著提示
        if not well_inside:
            ax.annotate(
                '井在计算域之外（xr / zr 没包住 well_pos）',
                xy=(0.99, 0.99), xycoords='axes fraction',
                ha='right', va='top', color=_Style.WELL, fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe8e8',
                          edgecolor=_Style.WELL, alpha=0.95, zorder=6))

        if len(view['hints']) > 0:
            ax.annotate(
                '无法解析、按默认绘制：{0}'.format('、'.join(view['hints'])),
                xy=(0.99, 0.90), xycoords='axes fraction',
                ha='right', va='top', color=_Style.WELL, fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe8e8',
                          edgecolor=_Style.WELL, alpha=0.95, zorder=6))



def test_1():
    """自测：开一个窗口，先按默认参数画，再依次切换参数。"""

    from zmlx.ui.pyqt import QtWidgets as _Qt
    from PyQt6.QtCore import QTimer
    import sys

    # 获取或创建 QApplication
    app = (
        _Qt.QApplication.instance()
        or _Qt.QApplication(sys.argv)
    )

    # 创建示意图窗口
    w = WellCrossSectionSketch()
    w.resize(560, 520)
    w.show()

    def show_custom():
        """切换到自定义参数。"""
        w.set_params(
            dict(
                xr=(-20, 20),
                zr=(0, 60),
                jx=40,
                jz=30,
                well_pos=(5, -10),
                well_d=0.4
            )
        )

    def show_invalid():
        """测试非法参数，jx='abc' 应回落到默认值。"""
        w.set_params(
            dict(
                xr=(-20, 20),
                zr=(0, 60),
                jx='abc',
                well_pos=(5, -10),
                well_d=0.4
            )
        )

    # QTimer 属于 QtCore，不属于 QtWidgets
    QTimer.singleShot(1500, show_custom)
    QTimer.singleShot(3000, show_invalid)

    app.exec()


if __name__ == '__main__':
    test_1()

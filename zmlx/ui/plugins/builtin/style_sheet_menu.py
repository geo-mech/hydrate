# ** name = '样式表'
# ** desc = '「设置 → 样式表」：可视化选择字体 / 配色 / 圆角生成 QSS，或直接编辑样式表文本；落盘后下次启动自动生效'
# ** enabled = True
"""样式表插件：`StyleSheetEdit` 控件 + `gui.show_style_sheet` 命令 + 「设置 → 样式表」菜单项.

⚠️ **它是插件（可关闭），不是核心功能**：这个入口原先以 `MainWindow.show_style_sheet`
的形式常驻在界面骨架里，菜单项也在 `__init_actions` 中。控件本体原先住在
`ui/tabs/style_sheet_edit.py`（1079 行）。

**2026-10-22：控件也整体并入本文件**（「完全自含」形态，见 `plugins/AGENTS.md` §0.2）——
`StyleSheetEdit` **只有本插件在用**，所以收进同一个文件：禁用本插件时连控件代码一起
不加载。⚠️ 当时已同步改掉这几处转发，否则 `ImportError`：
`ui/tabs/__init__.py` 删掉那条 import；弃用垫片 `ui/widget/style_sheet_edit.py` 与
`ui/widget/__init__.py` 的 `_PLUGINS` 表改指本模块。

**默认启用**：与「求解器」「运行环境」不同 —— 样式表是**用户随时会调**的外观设置
（换字体、调字号、改配色），藏起来会让人以为软件不能改外观。做成插件只是为了让它
**可被禁用**（例如管理员统一部署时锁掉外观），而不是为了默认收起它。

⚠️ **禁用本插件会同时失去两样东西**：① 菜单入口；② `gui.show_style_sheet()` 命令 ——
**历史标签页**（`gui_restore = gui.show_style_sheet()`）在插件被禁用后**恢复不了**
（重启时那条标签页会静默消失）。这是把命令从「`MainWindow` 公开方法（永远可用）」
改成「插件注册（可关）」的必然代价。

⚠️ 但 `gui.set_style_sheet` / `gui.get_style_sheet` **不受影响**：它们在 `main.py`
的 `__init_gui_api` 里直接转接到 Qt 的 `setStyleSheet` / `styleSheet`
（与 `resize` / `is_maximized` 同类），与插件无关 —— 所以**禁用插件后，已经落盘的
样式表照常生效**，只是没有可视化编辑器了。

职责划分（原控件的文档，随控件一并搬来）
----------------------------------------

⚠️ **职责划分**：`MainWindow` 那边只把 Qt 自己的 `setStyleSheet` /
`styleSheet` **转接**成 `gui.set_style_sheet` / `gui.get_style_sheet`，
**生成、应用、落盘全部在本控件里做**：本控件是唯一知道「样式表要存到
`zml_window_style.qss`」的地方（那也是下次启动 `main.__on_show` 会读的文件）。

⚠️ **应用走 GUI API**：GUI 线程里 `GuiApi` 当场派发，非 GUI 线程会自动排队到
GUI 线程（同 `zmlx/ui/widgets/AGENTS.md` 的「跨线程调用 GUI」）。

⚠️ **绝不静默覆盖用户文本**：参数模式与自定义模式在**载入时**按
「文本 == 由参数生成的结果」判定；文本对不上（例如从别处拷来的整份样式表）就按
自定义文本处理。在界面上从自定义切回参数模式，会先弹一句确认。

⚠️ **默认参数是「未设置」**（字体族与颜色为空串、字号/圆角/内边距为 0/-1）。此时
生成的是**空文本**，即「跟随系统外观」—— 生成的规则里只包含真正设置过的项，不会
因为打开过这个控件就把用户的界面改掉。

⚠️ **参数区里没有「先勾选才能用」的开关**：字体 / 字号 / 颜色都是直接可选的，
各自的「未设置」状态由下拉框的「跟随系统」和微调框的「默认」表达。被置灰的控件
等于在告诉用户「这里不能改」—— 之前用复选框当闸门就吃过这个亏（用户以为字体
改不了）。

⚠️ **生成的规则刻意收敛**：只给 `QWidget` 写 `color`（不写
`background-color`），背景色只给 `QMainWindow/QDialog/QMenuBar/...` 这些容器和
输入 / 按钮类控件 —— 给所有 `QWidget` 写死背景会把标签、滚动区视口涂成实色
（同 `license_button.py`、`license_register.py` 里那三条颜色约束）。

⚠️ 参数存在 `zml_style_options.json`、文本存在 `zml_window_style.qss`（都是
`settings.save` 的键，落在 app_data 的 temp 目录）。二者一起决定重启后回到哪个
模式：一致 → 参数模式（滑块和界面状态对得上），不一致 → 自定义文本。

⚠️ 本模块的模块级只放 import / 类定义 / 注册函数 / 自测：常量、颜色工具、QSS 生成器
全部收在 `_Qss` 里。这样模块级没有「散落的全局状态」。

Created by DeepSeek, 2026-10-07
Modified by DeepSeek, 2026-10-18: 菜单项从 `main.py` 的 `__init_actions` 搬来
    （只挪菜单，方法留在 `MainWindow`）
Modified by DeepSeek, 2026-10-22: `show_style_sheet` 与 `StyleSheetEdit` 控件
    整体并入本文件（`StyleSheetEdit` 只有本插件在用 → 完全自含）
"""

import contextlib
import json
import os
import sys

from zmlx.system import app_data, execute_once, read_text, write_text
from zmlx.ui import gui, settings
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QAction, QtCore, QtGui, QtWidgets


class _Qss:
    """QSS 生成器：参数 schema + 颜色小工具 + 生成规则。

    只装**类级成员**（常量 + 静态/类方法），不需要实例 —— 把它写成类而不是一堆
    模块级常量和函数，是为了让本模块的模块级保持干净（见模块文档）。
    颜色工具只依赖 :class:`QtGui.QColor`，所以整个生成器是纯函数，可以直接单测。
    """

    #: 参数字典的默认值 —— 全部「未设置」，生成空样式（跟随系统外观）。
    #: 字体族用 ``''`` 表示「跟随系统」、字号用 ``0`` 表示「不改字号」——
    #: 两者各自独立，都没设置就不写字体规则（见 :meth:`build`）。
    DEFAULT_OPTIONS = {
        'font_family': '',      # '' = 跟随系统字体
        'font_size': 0,         # 0 = 不改字号（只改字体族）
        'text': '',             # 以下四个色：'' = 不设置（跟随系统）
        'background': '',
        'accent': '',
        'border': '',
        'radius': -1,           # -1 = 不设置
        'padding': -1,
        'decorations': True,    # 是否同时设置标签页/表头/滚动条等细节
    }

    #: 配色预设：只覆盖颜色与圆角/内边距（字体由「字体 / 字号」两个控件单独控制）。
    #: 每项都是**完整**的六个键 —— 「跟随系统」要能明确地把颜色清回去，
    #: 不能靠「字典里没有这个键」来表达。
    PRESETS = {
        '跟随系统(不设置颜色)': dict(
            text='', background='', accent='', border='', radius=-1, padding=-1),
        '浅色': dict(
            text='#1f2329', background='#f5f6f8', accent='#2f6fd0',
            border='#c6cbd4', radius=4, padding=2),
        '深色': dict(
            text='#e4e6eb', background='#23272e', accent='#4c9aff',
            border='#454b54', radius=4, padding=2),
        '护眼绿': dict(
            text='#26331f', background='#e9f2e4', accent='#4a7c3f',
            border='#b8c9ae', radius=4, padding=2),
    }

    #: 四个颜色的 (参数键, 界面标签)，同时决定参数区的排列
    COLOR_ITEMS = (
        ('text', '文字色:'),
        ('background', '背景色:'),
        ('accent', '强调色:'),
        ('border', '边框色:'),
    )

    #: 输入类控件（要底色 / 边框 / 圆角的那一批）
    INPUT_SELECTORS = (
        'QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, '
        'QDoubleSpinBox, QDateEdit, QListView, QTreeView, QTableView, QListWidget, '
        'QTreeWidget, QTableWidget'
    )

    #: 容器选择器：**始终**跟着窗口底色走。
    #:
    #: ⚠️ 实测：`QMainWindow { background-color }` 管不到菜单栏 / 工具栏 / 状态栏 /
    #: 标签页容器 —— 它们各自会画一层自己的底色，必须逐个列出，否则深色主题下会在
    #: 窗口里留下几条系统色的亮带。这几个属于「窗口骨架」，不跟着「装饰」开关走。
    CONTAINER_SELECTORS = (
        'QMainWindow, QDialog, QMenuBar, QMenu, QToolBar, QStatusBar, '
        # 标签条那一块也要一起上色：只写 `QTabWidget::pane` 会在标签条区域留白
        'QTabWidget, QTabBar, QTabWidget::pane, '
        # 主窗口的中央区是 QSplitter（左/右两个标签页容器）
        'QSplitter'
    )

    @staticmethod
    def as_int(value, default=-1):
        """尽力把 value 变成 int；失败时返回 default。"""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def color(value):
        """把 ``'#rrggbb'`` 之类的文本转成 QColor；空串 / 非法值返回 None。"""
        if not isinstance(value, str) or len(value) == 0:
            return None
        color = QtGui.QColor(value)
        return color if color.isValid() else None

    @classmethod
    def color_text(cls, value):
        """返回可安全写进 QSS 的颜色文本；不合法时返回 ``''``。"""
        color = cls.color(value)
        return color.name() if color is not None else ''

    @classmethod
    def mix(cls, color_a, color_b, ratio):
        """按比例混合两个颜色（``ratio`` = 第二个颜色的占比），返回 ``'#rrggbb'``。

        任一颜色不合法时返回 ``''`` —— 调用方据此跳过对应的规则。
        """
        a, b = cls.color(color_a), cls.color(color_b)
        if a is None or b is None:
            return ''
        ratio = min(max(float(ratio), 0.0), 1.0)
        return QtGui.QColor(
            round(a.red() * (1 - ratio) + b.red() * ratio),
            round(a.green() * (1 - ratio) + b.green() * ratio),
            round(a.blue() * (1 - ratio) + b.blue() * ratio)).name()

    @classmethod
    def is_dark(cls, color):
        """按人眼亮度判断颜色是否偏暗（用于派生底色与对比色）。"""
        value = cls.color(color)
        if value is None:
            return False
        return (value.red() * 299 + value.green() * 587
                + value.blue() * 114) / 1000.0 < 128.0

    @classmethod
    def contrast_text(cls, color):
        """返回在给定底色上清楚可读的文字色（黑或白）。"""
        return '#ffffff' if cls.is_dark(color) else '#1a1a1a'

    @classmethod
    def input_background(cls, background):
        """由窗口底色**派生**输入类控件的底色。

        浅色主题用纯白；深色主题把底色略微提亮 —— 否则深色主题下输入框会和窗口
        糊成一片，看不出边界。派生而不是让用户再选一个色，是为了少一个旋钮。
        """
        if len(cls.color_text(background)) == 0:
            return ''
        if cls.is_dark(background):
            return cls.mix(background, '#ffffff', 0.08)
        return '#ffffff'

    @classmethod
    def match_preset(cls, options):
        """返回与给定参数匹配的预设名；都不匹配时返回 ``''``（表示自定义）。

        ⚠️ 只比预设自己声明的键（颜色 / 圆角 / 内边距）—— 字体是独立开关，
        不该影响「这算哪个配色预设」。
        """
        if not isinstance(options, dict):
            return ''
        for name, preset in cls.PRESETS.items():
            if all(options.get(key) == value for key, value in preset.items()):
                return name
        return ''

    @classmethod
    def build(cls, options=None):
        """根据参数生成 QSS 文本。

        Args:
            options: 参数字典（键见 :attr:`DEFAULT_OPTIONS`，缺的项按默认值补齐）。
                为 None 或全是「未设置」时返回 ``''``。

        Returns:
            str: QSS 文本；没有任何可写的规则时返回 ``''``。
        """
        opt = dict(cls.DEFAULT_OPTIONS)
        if isinstance(options, dict):
            for key in opt:
                if key in options:
                    opt[key] = options[key]

        text = cls.color_text(opt['text'])
        background = cls.color_text(opt['background'])
        accent = cls.color_text(opt['accent'])
        border = cls.color_text(opt['border'])
        radius = cls.as_int(opt['radius'], -1)
        padding = cls.as_int(opt['padding'], -1)
        decorations = bool(opt['decorations'])

        input_bg = cls.input_background(background)
        # 悬停 / 按下：在输入框底色上混入强调色（这样深色主题也不会跳成亮色）
        hover_bg = cls.mix(input_bg or background or '#ffffff', accent, 0.22)
        pressed_bg = cls.mix(input_bg or background or '#ffffff', accent, 0.42)
        # 禁用态文字：只在**知道底色**时才派生 —— 底色未知时派生的颜色可能正好和
        # 系统底色撞在一起（暗色模式下尤其），那就宁可不写，交给系统。
        disabled_text = (cls.mix(text, background, 0.55)
                         if (text and background) else '')
        # 装饰底板（标签页 / 表头 / 滚动条槽）：窗口底色与输入底色的中间值
        decoration_bg = (background if len(input_bg) == 0
                         else cls.mix(background, input_bg, 0.5))
        accent_text = cls.contrast_text(accent) if accent else ''
        # 是否在给标签页 / 表头 / 滚动条「上色描边」—— 决定要不要补默认的内边距、
        # 滚动条宽度这类**结构性**属性：只改个文字颜色时不该顺手改版式。
        structural = bool(decoration_bg or border or radius >= 0)
        radius_text = f'{radius}px' if radius >= 0 else ''
        padding_text = f'{padding}px' if padding >= 0 else ''
        border_text = f'1px solid {border}' if border else ''

        blocks = []

        def add(selector, props):
            """收集一条规则；属性值全为空的不收（= 该规则整体不存在）。"""
            items = [(key, value) for key, value in props
                     if isinstance(value, str) and len(value) > 0]
            if len(items) > 0:
                blocks.append((selector, items))

        # ---- 字体：字体族 / 字号各自独立，都没设置就整块不写（交给系统）----
        family = (opt['font_family']
                  if isinstance(opt['font_family'], str) else '')
        size = cls.as_int(opt['font_size'], 0)
        if len(family) > 0 or size > 0:
            add('*', [
                ('font-family', f'"{family}"' if len(family) > 0 else ''),
                ('font-size', f'{size}pt' if size > 0 else ''),
            ])

        # ---- 全局文字色（只写 color，绝不写 background）----
        add('QWidget', [('color', text)])

        # ---- 容器底色 ----
        add(cls.CONTAINER_SELECTORS, [('background-color', background)])

        # ---- 分隔条 ----
        # ⚠️ 必须显式上色：`QSplitter` 一旦带上样式表，中间那条把手就会退回调色板
        # 的 Base 色 —— 浅色主题下是一条**白缝**，深色主题下更刺眼（实测过）。
        add('QSplitter::handle', [('background-color', decoration_bg)])

        # ---- 工具提示 ----
        add('QToolTip', [
            ('color', text),
            ('background-color', decoration_bg),
            ('border', border_text),
        ])

        # ---- 输入类控件 ----
        add(cls.INPUT_SELECTORS, [
            ('background-color', input_bg),
            ('color', text),
            ('border', border_text),
            ('border-radius', radius_text),
            ('padding', padding_text),
            ('selection-background-color', accent),
            ('selection-color', accent_text),
        ])

        # ---- 按钮（工具按钮只给悬停/按下，避免工具栏变成一排方块）----
        add('QPushButton', [
            ('background-color', input_bg),
            ('color', text),
            ('border', border_text),
            ('border-radius', radius_text),
            ('padding', padding_text),
        ])
        add('QPushButton:hover, QToolButton:hover',
            [('background-color', hover_bg)])
        add('QPushButton:pressed, QToolButton:pressed',
            [('background-color', pressed_bg)])
        add('QPushButton:disabled, QToolButton:disabled',
            [('color', disabled_text)])

        # ---- 装饰：标签页 / 菜单 / 表头 / 滚动条 ----
        if decorations:
            # 标签条的内边距：垂直方向用用户设的，**水平方向固定给 10px** ——
            # 参数里的「内边距」是给输入框 / 按钮用的，直接套到标签上会把标题
            # 挤得贴着边框（试过）。用户没设垂直值时，改过颜色就补 5px。
            if padding >= 0:
                tab_padding = f'{padding}px 10px'
            elif structural:
                tab_padding = '5px 10px'
            else:
                tab_padding = ''
            add('QTabBar::tab', [
                ('background-color', decoration_bg),
                ('color', text),
                ('border', border_text),
                ('border-bottom', 'none' if border_text else ''),
                ('border-top-left-radius', radius_text),
                ('border-top-right-radius', radius_text),
                ('padding', tab_padding),
            ])
            add('QTabBar::tab:selected', [
                ('background-color', input_bg),
                ('color', accent),
            ])
            add('QTabBar::tab:hover', [('color', accent)])
            add('QMenu::item:selected', [
                ('background-color', accent),
                ('color', accent_text),
            ])
            if border:  # 分隔线只在有边框色时才画，否则别动菜单的间距
                add('QMenu::separator', [
                    ('height', '1px'),
                    ('background-color', border),
                    ('margin', '4px 8px'),
                ])
            # 表头：用户设了内边距就用，没设且确实在上色时补默认值
            header_padding = f'{padding}px 6px' if padding >= 0 else ''
            if len(header_padding) == 0 and structural:
                header_padding = '3px 6px'
            add('QHeaderView::section', [
                ('background-color', decoration_bg),
                ('color', text),
                ('border', 'none' if border else ''),
                ('border-right', border_text),
                ('padding', header_padding),
            ])
            # 表格左上角那个小方块（行头/列头交叉处）单独一条选择器，表头规则管不到
            add('QTableCornerButton::section', [
                ('background-color', decoration_bg),
                ('border', 'none' if border else ''),
                ('border-right', border_text),
                ('border-bottom', border_text),
            ])
            if border or decoration_bg:  # 只有真要给滚动条上色时才重定义它
                add('QScrollBar:vertical', [
                    ('background-color', decoration_bg),
                    ('width', '12px'),
                    ('margin', '0px'),
                ])
                add('QScrollBar:horizontal', [
                    ('background-color', decoration_bg),
                    ('height', '12px'),
                    ('margin', '0px'),
                ])
                add('QScrollBar::handle:vertical', [
                    ('background-color', border),
                    ('border-radius', '6px' if border else ''),
                    ('min-height', '24px'),
                ])
                add('QScrollBar::handle:horizontal', [
                    ('background-color', border),
                    ('border-radius', '6px' if border else ''),
                    ('min-width', '24px'),
                ])
                add('QScrollBar::add-line, QScrollBar::sub-line', [
                    ('height', '0px'),
                    ('width', '0px'),
                ])
                # ⚠️ 这里是 `background: none`（不是 `background-color: none`）
                # —— 后者在 Qt 里不是合法取值，写了等于没写（Qt 会静默忽略）。
                add('QScrollBar::add-page, QScrollBar::sub-page',
                    [('background', 'none')])

        if len(blocks) == 0:  # 全都没设置：给空文本，界面保持系统外观
            return ''

        lines = ['/* 由 zmlx「设置 → 样式表」生成（参数模式）：'
                 '切成「自定义文本」后可手工修改 */', '']
        for selector, props in blocks:
            lines.append(f'{selector} {{')
            lines.extend(f'    {key}: {value};' for key, value in props)
            lines.append('}')
            lines.append('')
        return '\n'.join(lines).rstrip('\n') + '\n'


class _ColorButton(QtWidgets.QPushButton):
    """颜色按钮：色块 + 十六进制文本；支持「未设置」（跟随系统）。

    色块用**图标**画（不是 ``setStyleSheet``）—— 本程序会加载用户样式表，
    按钮自己写死 ``background-color`` 会和它打架，图标则不受影响。
    """

    colorChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color_text = ''
        self.setToolTip('点击选择颜色\n右键可清除（清除 = 跟随系统，不写这条规则）')
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.clicked.connect(self._choose_color)
        self._refresh()

    def get_color_text(self):
        """返回 ``'#rrggbb'``；「未设置」时返回 ``''``。"""
        return self._color_text

    def set_color_text(self, text):
        """设置颜色（``''`` = 未设置）；取值没变时不发信号。"""
        text = _ColorButton.valid_text(text)
        if text == self._color_text:
            return
        self._color_text = text
        self._refresh()
        self.colorChanged.emit()

    @staticmethod
    def valid_text(text):
        """把颜色文本规范成 ``'#rrggbb'``；空串 / 非法值返回 ``''``。

        这里**不**复用 :class:`_Qss` 的颜色工具：按钮只需要「合法与否」这一件事，
        自己判两行就够了，不必让两个控件类互相引用。
        """
        if not isinstance(text, str) or len(text) == 0:
            return ''
        color = QtGui.QColor(text)
        return color.name() if color.isValid() else ''

    def _refresh(self):
        if len(self._color_text) == 0:  # 未设置：跟随系统
            self.setText('默认')
            self.setIcon(QtGui.QIcon())
            return
        color = QtGui.QColor(self._color_text)
        pixmap = QtGui.QPixmap(14, 14)
        pixmap.fill(color)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor('#808080'))
        painter.drawRect(0, 0, 13, 13)
        painter.end()
        self.setIcon(QtGui.QIcon(pixmap))
        self.setText(color.name())

    def _choose_color(self):
        initial = (QtGui.QColor(self._color_text) if len(self._color_text) > 0
                   else QtGui.QColor('#ffffff'))
        color = QtWidgets.QColorDialog.getColor(initial, self, '选择颜色')
        if color.isValid():
            self.set_color_text(color.name())

    def _clear_color(self):
        self.set_color_text('')

    def _show_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction('选择颜色...', self._choose_color)
        menu.addAction('清除（跟随系统）', self._clear_color)
        menu.exec(self.mapToGlobal(pos))


class _StyleTextEdit(QtWidgets.QPlainTextEdit):
    """样式表文本框（右键菜单里挂上宿主的 :attr:`context_actions`）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_actions = []

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                if isinstance(action, QAction):
                    menu.addAction(action)
                else:
                    menu.addSeparator()
        menu.exec(event.globalPos())


class StyleSheetEdit(QtWidgets.QWidget):
    """样式表编辑器（「参数生成」与「自定义文本」两种模式）。

    公开接口刻意保持很小：

    * :meth:`set_style_sheet` —— 载入一份 QSS 文本（自动判定模式）
    * :meth:`get_style_sheet` —— 返回当前文本（「应用」时用的就是它）
    * :meth:`apply` —— 调 ``gui.set_style_sheet`` 应用（可选落盘）
    * :meth:`reset` —— 恢复默认（清空参数与文本，立即生效并保存）

    其余都是内部实现（单下划线开头）；QSS 的生成规则见 :class:`_Qss`。
    """

    #: 模式取值（同时用作 :class:`QtWidgets.QComboBox` 的下标）
    MODE_PARAM = 0
    MODE_CUSTOM = 1
    MODE_TEXTS = ('参数生成', '自定义文本')

    #: 两种模式在顶部显示的说明（见 :meth:`_update_enabled`）
    HINT_PARAM = ('参数模式下文本框只读：改上面的参数即实时重新生成。'
                  '点「应用」后写入 zml_window_style.qss，下次启动自动加载。')
    HINT_CUSTOM = ('自定义文本模式下参数区不参与生成：文本框里的内容会原样应用'
                   '（可直接粘贴别处拷来的整份 QSS）。')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False  # 程序化刷新期间屏蔽「参数变了」的回调
        self._build_ui()
        self._load_state()

    # --------------------------------------------------------
    # 界面
    # --------------------------------------------------------

    def _build_ui(self):
        """搭出「模式 + 参数 + 文本 + 按钮」四段式界面。"""
        layout = QtWidgets.QVBoxLayout(self)

        # ---- 模式 ----
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel('模式:'))
        self._mode_combo = QtWidgets.QComboBox()
        self._mode_combo.addItems(list(self.MODE_TEXTS))
        self._mode_combo.setToolTip(
            '参数生成：由下面的参数实时生成 QSS\n'
            '自定义文本：忽略参数，原样使用文本框内容')
        top.addWidget(self._mode_combo)
        self._hint = QtWidgets.QLabel()
        self._hint.setWordWrap(True)
        top.addWidget(self._hint, stretch=1)
        layout.addLayout(top)

        # ---- 参数 ----
        self._param_box = QtWidgets.QGroupBox('参数')
        grid = QtWidgets.QGridLayout(self._param_box)
        row = 0

        grid.addWidget(QtWidgets.QLabel('配色预设:'), row, 0)
        self._preset_combo = QtWidgets.QComboBox()
        self._preset_combo.addItems(list(_Qss.PRESETS.keys()))
        self._preset_combo.setToolTip(
            '只改颜色 / 圆角 / 内边距；字体由「字体 / 字号」单独控制')
        grid.addWidget(self._preset_combo, row, 1)
        self._decorations = QtWidgets.QCheckBox('同时设置标签页/表头/滚动条等细节')
        self._decorations.setToolTip(
            '关掉后只设置字体与输入框、按钮等基本控件的颜色；\n'
            '标签页的形状、表头、滚动条、菜单选中色等细节保持系统外观')
        grid.addWidget(self._decorations, row, 3, 1, 2)
        row += 1

        # 字体：**不给「改不改字体」加开关** —— 那种开关看着就是「控件被禁用」，
        # 用户根本不知道要先勾它。改成下拉框里自带一项「跟随系统」：选了它就不写
        # font-family，选了具体字体才写；字号同理（0 = 默认，不写 font-size）。
        grid.addWidget(QtWidgets.QLabel('字体:'), row, 0)
        self._font_combo = QtWidgets.QComboBox()
        self._fill_font_combo(self._font_combo)
        self._font_combo.setToolTip(
            '「跟随系统」= 不在样式表里写字体族（用系统/主题的字体）')
        grid.addWidget(self._font_combo, row, 1, 1, 2)
        grid.addWidget(QtWidgets.QLabel('字号:'), row, 3)
        self._font_size = QtWidgets.QSpinBox()
        self._font_size.setRange(0, 48)
        self._font_size.setSpecialValueText('默认')  # 0 = 只改字体族
        self._font_size.setSuffix(' pt')
        self._font_size.setToolTip('「默认」= 不在样式表里写字号（只改字体族）')
        grid.addWidget(self._font_size, row, 4)
        row += 1

        self._colors = {}
        for idx, (key, label) in enumerate(_Qss.COLOR_ITEMS):
            if idx > 0 and idx % 2 == 0:
                row += 1
            column = 0 if idx % 2 == 0 else 3
            button = _ColorButton()
            self._colors[key] = button
            grid.addWidget(QtWidgets.QLabel(label), row, column)
            grid.addWidget(button, row, column + 1)
        row += 1

        grid.addWidget(QtWidgets.QLabel('圆角:'), row, 0)
        self._radius = QtWidgets.QSpinBox()
        self._radius.setRange(-1, 24)
        self._radius.setSpecialValueText('默认')
        self._radius.setSuffix(' px')
        grid.addWidget(self._radius, row, 1)
        grid.addWidget(QtWidgets.QLabel('内边距:'), row, 3)
        self._padding = QtWidgets.QSpinBox()
        self._padding.setRange(-1, 16)
        self._padding.setSpecialValueText('默认')
        self._padding.setSuffix(' px')
        grid.addWidget(self._padding, row, 4)
        row += 1

        layout.addWidget(self._param_box)

        # ---- 文本 ----
        self._text_edit = _StyleTextEdit()
        self._text_edit.setPlaceholderText(
            '样式表(QSS)文本；为空表示跟随系统默认外观')
        try:
            self._text_edit.setFont(QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.SystemFont.FixedFont))
        except Exception as err:
            print(f'Error: {err}')
        self._text_edit.context_actions = [
            create_action(self, '导入样式表文件...', icon='open',
                          slot=self._import_file),
            create_action(self, '导出样式表文件...', icon='save',
                          slot=self._export_file),
            None,
            create_action(self, '从当前生效的样式重新载入', icon='refresh',
                          slot=self._reload_current),
            create_action(self, '清空文本', icon='clean',
                          slot=self._clear_text),
        ]
        layout.addWidget(self._text_edit, stretch=1)

        # ---- 按钮 ----
        bottom = QtWidgets.QHBoxLayout()
        self._apply_btn = QtWidgets.QPushButton('应用')
        self._apply_btn.setDefault(True)
        self._apply_btn.setToolTip(
            '立即应用当前样式表，并写入 zml_window_style.qss（下次启动自动加载）')
        self._reset_btn = QtWidgets.QPushButton('恢复默认')
        self._reset_btn.setToolTip('清除自定义样式，恢复系统默认外观（立即生效并保存）')
        bottom.addWidget(self._apply_btn)
        bottom.addWidget(self._reset_btn)
        bottom.addStretch()
        self._auto_load = QtWidgets.QCheckBox('启动时自动加载')
        self._auto_load.setToolTip(
            '对应环境变量 load_window_style；取消勾选则下次启动不加载自定义样式'
            '（样式表本身仍保留，随时可再勾上）')
        bottom.addWidget(self._auto_load)
        layout.addLayout(bottom)

        # ---- 信号 ----
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._font_combo.currentIndexChanged.connect(self._on_param_changed)
        self._font_size.valueChanged.connect(self._on_param_changed)
        self._radius.valueChanged.connect(self._on_param_changed)
        self._padding.valueChanged.connect(self._on_param_changed)
        self._decorations.toggled.connect(self._on_param_changed)
        for button in self._colors.values():
            button.colorChanged.connect(self._on_param_changed)
        self._apply_btn.clicked.connect(self._on_apply_clicked)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        self._auto_load.toggled.connect(self._on_auto_load_toggled)

    def _update_enabled(self):
        """按当前模式刷新各控件的可用状态和顶部说明。

        ⚠️ **只有「模式」会禁用参数区**（自定义文本模式下参数不参与生成）。
        参数区里面不再有任何「先勾选才能用」的开关：字体 / 字号 / 颜色都是
        直接可选，各自的「未设置」状态由下拉框的「跟随系统」和微调框的
        「默认」表达 —— 被置灰的控件等于告诉用户「这里不能改」。
        """
        is_param = self._mode_combo.currentIndex() == self.MODE_PARAM
        self._param_box.setEnabled(is_param)
        self._text_edit.setReadOnly(is_param)
        self._hint.setText(self.HINT_PARAM if is_param else self.HINT_CUSTOM)

    # --------------------------------------------------------
    # 参数 <-> 界面
    # --------------------------------------------------------

    @staticmethod
    def _fill_font_combo(combo):
        """把「跟随系统」+ 本机字体族填进字体下拉框，并让每项用自己的字体显示。

        ⚠️ 用普通的 :class:`QtWidgets.QComboBox` 而不是 ``QFontComboBox``：后者
        的列表就是字体库，塞不进「跟随系统」这一项，而这一项正是「不写
        font-family」的表达方式。
        """
        combo.addItem('跟随系统')  # 下标 0：不写 font-family
        try:
            families = QtGui.QFontDatabase.families()  # PyQt6：静态方法
        except Exception:
            try:  # PyQt5：families() 是成员函数，得先建实例
                families = QtGui.QFontDatabase().families()
            except Exception as err:
                print(f'Error: {err}')
                return
        role = QtCore.Qt.ItemDataRole.FontRole
        for family in families:
            combo.addItem(family)
            combo.setItemData(combo.count() - 1, QtGui.QFont(family), role)

    def _set_font_family(self, family):
        """把字体族写进下拉框；``''`` 表示「跟随系统」。

        ⚠️ 本机没装的字体（例如从别的机器拷来的设置）要**临时补一项**：
        否则 ``setCurrentText`` 在不可编辑的下拉框上会静默失败，读回来就变成
        另一个字体，模式和参数会跟落盘的文本对不上。
        """
        if not isinstance(family, str) or len(family) == 0:
            self._font_combo.setCurrentIndex(0)
            return
        index = self._font_combo.findText(family)
        if index < 0:
            self._font_combo.addItem(family)
            index = self._font_combo.count() - 1
        self._font_combo.setCurrentIndex(index)

    def _font_family(self):
        """从下拉框读回字体族；「跟随系统」返回 ``''``。"""
        if self._font_combo.currentIndex() <= 0:
            return ''
        text = self._font_combo.currentText()
        return text if isinstance(text, str) else ''

    @contextlib.contextmanager
    def _silent(self):
        """程序化改控件期间，屏蔽「参数变了」之类的回调。

        ⚠️ 挡的是**本控件自己的槽**（它们开头都判 ``self._updating``），不是
        ``blockSignals`` —— 后者会连 Qt 内部的联动一起掐掉，反而更难排查。
        界面里凡是「把值写进控件」的地方都套一层它，免得读回来的值又被当成
        用户输入触发一轮刷新 / 落盘（``env_edit.py`` 的 ``_set_silently``
        就是同一个坑的另一处补丁）。
        """
        was_updating = self._updating
        self._updating = True
        try:
            yield
        finally:
            self._updating = was_updating

    def _collect_options(self):
        """从界面读回参数字典（与 :attr:`_Qss.DEFAULT_OPTIONS` 同构）。

        字体族由下拉框说了算（「跟随系统」→ ``''``）、字号由微调框说了算
        （0 → 不写 font-size），两者互不影响。
        """
        options = dict(_Qss.DEFAULT_OPTIONS)
        options.update(
            font_family=self._font_family(),
            font_size=self._font_size.value(),
            radius=self._radius.value(),
            padding=self._padding.value(),
            decorations=self._decorations.isChecked(),
        )
        for key, button in self._colors.items():
            options[key] = button.get_color_text()
        return options

    def _apply_options(self, options):
        """把参数字典写进各控件（期间屏蔽回调，不触发重新生成 / 保存）。"""
        if not isinstance(options, dict):
            options = {}
        with self._silent():
            self._set_font_family(options.get('font_family', ''))
            self._font_size.setValue(_Qss.as_int(options.get('font_size'), 0))
            for key, button in self._colors.items():
                value = options.get(key, '')
                button.set_color_text(value if isinstance(value, str) else '')
            self._radius.setValue(_Qss.as_int(options.get('radius'), -1))
            self._padding.setValue(_Qss.as_int(options.get('padding'), -1))
            self._decorations.setChecked(bool(options.get('decorations', True)))
            name = _Qss.match_preset(options)
            self._preset_combo.setCurrentIndex(
                self._preset_combo.findText(name) if len(name) > 0 else -1)
        self._update_enabled()

    def _refresh_text_from_params(self):
        """参数模式下按当前参数重写文本框；自定义模式下不动它。"""
        if self._mode_combo.currentIndex() != self.MODE_PARAM:
            return
        text = _Qss.build(self._collect_options())
        if text != self._text_edit.toPlainText():
            self._text_edit.setPlainText(text)

    def _sync_preset_combo(self, options):
        """让预设下拉框跟着参数走：匹配得上就选中，匹配不上就留空（= 自定义）。"""
        name = _Qss.match_preset(options)
        index = self._preset_combo.findText(name) if len(name) > 0 else -1
        if index == self._preset_combo.currentIndex():
            return
        with self._silent():
            self._preset_combo.setCurrentIndex(index)

    # --------------------------------------------------------
    # 信号槽
    # --------------------------------------------------------

    def _on_param_changed(self, *args):
        """任一参数变化：刷新预设归属，并在参数模式下重新生成文本。"""
        if self._updating:
            return
        self._sync_preset_combo(self._collect_options())
        self._refresh_text_from_params()

    def _on_preset_changed(self, index):
        """选了配色预设：把它的颜色 / 圆角 / 内边距灌进界面。"""
        if self._updating or index < 0:
            return
        preset = _Qss.PRESETS.get(self._preset_combo.itemText(index))
        if preset is None:
            return
        with self._silent():
            for key, value in preset.items():
                if key in self._colors:
                    self._colors[key].set_color_text(value)
                elif key == 'radius':
                    self._radius.setValue(_Qss.as_int(value, -1))
                elif key == 'padding':
                    self._padding.setValue(_Qss.as_int(value, -1))
        self._refresh_text_from_params()

    def _on_mode_changed(self, index):
        """切换模式；从自定义切回参数会覆盖文本，所以先问一句。"""
        if self._updating:
            self._update_enabled()
            return
        if index == self.MODE_PARAM:
            generated = _Qss.build(self._collect_options())
            if self._text_edit.toPlainText() != generated:
                reply = QtWidgets.QMessageBox.question(
                    self, '切换到参数生成',
                    '切换到「参数生成」会按当前参数重新生成样式表，'
                    '覆盖文本框里的内容。\n确定继续吗？')
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    with self._silent():
                        self._mode_combo.setCurrentIndex(self.MODE_CUSTOM)
                    self._update_enabled()
                    return
            self._refresh_text_from_params()
        self._update_enabled()

    def _on_apply_clicked(self):
        self.apply(save=True)
        gui.status('样式表已应用并保存（下次启动自动加载）', 5000)

    def _on_reset_clicked(self):
        reply = QtWidgets.QMessageBox.question(
            self, '恢复默认',
            '将清除所有自定义样式、恢复系统默认外观，'
            '并写入 zml_window_style.qss（下次启动同样生效）。\n确定继续吗？')
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.reset()
        gui.status('样式表已恢复默认', 5000)

    def _on_auto_load_toggled(self, checked):
        if self._updating:
            return
        app_data.setenv(
            key='load_window_style',
            value='Yes' if checked else 'No',
            encoding='utf-8')
        mode = '将加载' if checked else '不加载'
        gui.status(f'下次启动{mode}自定义样式表', 5000)

    # --------------------------------------------------------
    # 右键菜单动作
    # --------------------------------------------------------

    def _import_file(self):
        """从 .qss/.css 文件导入：载入后进入自定义文本模式。"""
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '导入样式表', '',
            '样式表 (*.qss *.css);;所有文件 (*.*)')
        if len(filepath) == 0:
            return
        text = read_text(path=filepath, encoding='utf-8', default='')
        self.set_style_sheet(text if isinstance(text, str) else '')
        gui.status(f'已载入样式表: {filepath}', 5000)

    def _export_file(self):
        """把文本框内容导出到 .qss/.css 文件。"""
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出样式表', 'zml_window_style.qss',
            '样式表 (*.qss *.css);;所有文件 (*.*)')
        if len(filepath) == 0:
            return
        write_text(path=filepath, text=self.get_style_sheet(), encoding='utf-8')
        gui.status(f'已导出样式表: {filepath}', 5000)

    def _reload_current(self):
        """重新载入「此刻真正生效」的那份样式表（可能还没落盘）。

        走 ``gui.get_style_sheet``（转接到窗口的 ``styleSheet()``）；没启动 GUI
        时退回读磁盘上的那份。
        """
        text = gui.get_style_sheet() if gui.exists() else None
        if not isinstance(text, str):
            text = settings.load(
                key='zml_window_style.qss', default='',
                encoding='utf-8', ignore_empty=True)
        self.set_style_sheet(text if isinstance(text, str) else '')
        gui.status('已重新载入当前生效的样式表', 5000)

    def _clear_text(self):
        """清空文本框（同时切到自定义模式，否则会和参数模式对不上）。"""
        with self._silent():
            self._mode_combo.setCurrentIndex(self.MODE_CUSTOM)
            self._text_edit.setPlainText('')
        self._update_enabled()

    # --------------------------------------------------------
    # 公开接口
    # --------------------------------------------------------

    def set_style_sheet(self, text=None):
        """载入一份样式表文本（模式自动判定）。

        判定规则：文本与「当前参数生成的结果」相同 → 参数模式；否则 → 自定义
        文本模式。这样从别处拷来的样式表**不会**被参数悄悄改掉。

        Args:
            text: QSS 文本；None 按空串处理。

        Raises:
            ValueError: ``text`` 不是字符串。
        """
        if text is None:
            text = ''
        if not isinstance(text, str):
            raise ValueError(f'text must be str or None, got {type(text).__name__}')
        mode = (self.MODE_PARAM if text == _Qss.build(self._collect_options())
                else self.MODE_CUSTOM)
        with self._silent():
            self._mode_combo.setCurrentIndex(mode)
            self._text_edit.setPlainText(text)
        self._update_enabled()

    def get_style_sheet(self):
        """返回文本框里当前的样式表文本（「应用」时用的就是它）。"""
        return self._text_edit.toPlainText()

    def apply(self, save=True):
        """应用当前样式表，并返回被应用的文本。

        Args:
            save: 是否同时写入 ``zml_window_style.qss``（下次启动自动加载）
                并记住当前参数。默认 True。

        Returns:
            str: 被应用的文本。

        Note:
            ``gui.set_style_sheet`` 只是 Qt ``QWidget.setStyleSheet`` 的**转接**
            （见 ``MainWindow.__init_gui_api``），本身不管落盘 —— 所以「存到哪、
            存不存」这些事全部由本控件负责：这里写 ``zml_window_style.qss``，
            而该文件正是下次启动时 ``main.__on_show`` 会读的那一个。

            只有**没启动 GUI**（独立运行本文件自测）时才不走 GUI API，直接把
            样式设在所在窗口上；落盘逻辑两条路共用，免得行为对不上。
        """
        text = self.get_style_sheet()
        if gui.exists():
            gui.set_style_sheet(text)
        else:
            window = self.window()
            if isinstance(window, QtWidgets.QWidget):
                window.setStyleSheet(text)
        if save:
            settings.save(
                key='zml_window_style.qss', value=text, encoding='utf-8')
            self._save_options()
        print(f'{"应用" if save else "预览"}样式表: {len(text)} 个字符')
        return text

    def reset(self):
        """恢复默认：清空参数与文本，立即应用并保存（回到系统外观）。"""
        with self._silent():
            self._mode_combo.setCurrentIndex(self.MODE_PARAM)
        self._apply_options(dict(_Qss.DEFAULT_OPTIONS))
        self._refresh_text_from_params()
        return self.apply(save=True)

    # --------------------------------------------------------
    # 持久化
    # --------------------------------------------------------

    @staticmethod
    def _load_options():
        """读回上次保存的参数；文件缺失 / 损坏时返回默认值（不抛异常）。"""
        options = dict(_Qss.DEFAULT_OPTIONS)
        text = settings.load(
            key='zml_style_options.json', default='',
            encoding='utf-8', ignore_empty=True)
        if not isinstance(text, str) or len(text) == 0:
            return options
        try:
            data = json.loads(text)
        except Exception as err:
            print(f'Error: {err}')
            return options
        if not isinstance(data, dict):
            return options
        for key in options:
            if key in data:
                options[key] = data[key]
        return options

    def _save_options(self):
        """记住当前参数（跨进程）；失败只打印，不影响样式表本身已生效。"""
        try:
            settings.save(
                key='zml_style_options.json',
                value=json.dumps(self._collect_options(), ensure_ascii=False,
                                 indent=2),
                encoding='utf-8')
        except Exception as err:
            print(f'Error: {err}')

    def _load_state(self):
        """载入上次的参数与样式表文本（重启后接着改）。"""
        text = settings.load(
            key='zml_window_style.qss', default='',
            encoding='utf-8', ignore_empty=True)
        if not isinstance(text, str):
            text = ''
        options = self._load_options()
        if len(text) == 0:
            # 当前生效的是「空样式」（没在用自定义样式表）。这时**连参数也从默认
            # 开始**：否则会留下「参数写着护眼绿、文本框却空着」的自相矛盾状态，
            # 用户点「应用」还以为没生效（实际是把空样式又应用了一遍）。
            options = dict(_Qss.DEFAULT_OPTIONS)
        self._apply_options(options)
        with self._silent():
            self._auto_load.setChecked(
                app_data.getenv(
                    key='load_window_style', default='Yes',
                    ignore_empty=True) != 'No')
        self.set_style_sheet(text)


def show_style_sheet():
    """显示「样式表」标签页（可视化生成 QSS，或直接编辑文本后应用）.

    ⚠️ **命令名不能改**：历史标签页存的就是 `gui.show_style_sheet()`，重启时按原文重放。

    ⚠️ 与 `MainWindow` 时期一样：**只通过 `gui.get_widget` 打开**，所以标签页只会
    一个，重复调用只是切到前面。
    """

    def oper(w):
        w.gui_restore = 'gui.show_style_sheet()'

    gui.get_widget(
        the_type=StyleSheetEdit,
        caption='样式表',
        on_top=True,
        icon='set',
        oper=oper,
        tooltip='可视化设置字体/配色等并生成样式表(QSS)；也可以直接编辑样式表文本',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 `gui.show_style_sheet` 并在「设置」下挂「样式表」（插件被执行时调一次）.

    ⚠️ 菜单标题与 `main.py` 里那几处**逐字一致**（都写 `'设置'`），否则
    `get_menu` 会另建一个同名的新顶层菜单，界面上出现两个「设置」。
    """
    gui.add_func('show_style_sheet', show_style_sheet)

    gui.add_action(
        menu='设置', name='edit_window_style',
        text='样式表',
        icon='set',
        tooltip='设置窗口样式表：可视化选择字体/配色/圆角，也可以直接编辑 QSS 文本',
        slot=show_style_sheet,
        overwrite=False,
    )


def test_1():
    """直接运行本文件时的自测界面.

    预置一套「深色」参数，这样一打开就能在文本框里看到生成出来的完整 QSS，
    而不是一个什么都看不出的空界面。⚠️ 这里**只改参数、不落盘**：窗口外观和
    `zml_window_style.qss` 都要等你自己点「应用」才会变。
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = StyleSheetEdit()
    w._preset_combo.setCurrentIndex(w._preset_combo.findText('深色'))
    w.resize(860, 640)
    w.show()
    sys.exit(app.exec())


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（`setups/*.py` 则由
#    `setups/__init__.py` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 `__name__` 是 `'__zml_plugin__'`；直接 `python style_sheet_menu.py`
#    时才是 `'__main__'`（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()

if __name__ == '__main__':
    test_1()

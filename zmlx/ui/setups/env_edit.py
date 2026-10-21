"""环境变量编辑器（``EnvEdit``）+ 命令 ``gui.show_env_edit`` + 「设置 → 系统」菜单项.

**本文件自含**：控件 :class:`EnvEdit`（以及它自带的全部自绘子控件）、
入口 :func:`show_env_edit`、菜单项与命令都在这里。

⚠️ **2026-10-31 由 ``zmlx/ui/tabs/env_edit.py`` 搬到 ``setups/``**（原模块删除、
**不留垫片**），同时把 `MainWindow.show_env_edit` 的方法体与「设置 → 系统」那条
``add_action`` 原样搬到这里。控件本体一字未改。

为什么在 ``setups/`` 而不是 ``tabs/``
------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— 「设置 → 系统」是修改**全局配置**的页面（``zml_env_items.json`` 里那些键：
  界面标签位置、是否显示启动画面、控制台宽度……），改完对整个软件生效，属**产品功能**，
  不该让用户在「设置 → 插件」里关掉。
- 它也**带着菜单项和快捷键**（``Ctrl+E``），不只是一个「被装配层打开成页面」的控件 ——
  ``tabs/`` 收的是后者。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

菜单与命令（**与搬迁前完全一致**）
----------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
菜单                        设置 → 系统（``name='env'``、``icon='set'``、``Ctrl+E``）
命令                        ``gui.show_env_edit()``
标签页                      标题「系统设置」，``gui_restore = 'gui.show_env_edit()'``
=========================  ==================================================

⚠️ **命令名 ``show_env_edit`` 不能改** —— 它被至少三处按**名字**引用：

1. 历史标签页的 ``gui_restore``（存的就是 ``gui.show_env_edit()``）；
2. ``ReadMe`` 里的链接 ``[菜单：设置 → 系统](zmlx://gui/show_env_edit)``
   （``tabs/readme_browser.py`` 按命令名取函数）；
3. 界面桥（``scen/gui_bridge/``）的**示例命令**与文档 —— ``client.show('show_env_edit')``。

⚠️ **菜单 ``name='env'`` 也不能改**：ribbon 配置与已保存的界面布局按 ``name`` 定位这一项。

下面是控件本身的说明
--------------------


以表单形式展示 ``zml_env_items.json`` 中定义的配置项。**每个控件都按该键
「代码里真正采用的默认值」初始化**，而不是一律显示空 / 未勾选 —— 这是本控件
最重要的一条契约（第一次改版就是因为把「未设置」显示成空，导致「主界面标签
位置」明明默认在顶部，界面上却是空行）。

控件映射由 ``kind`` 字段（基础类型）与 :data:`KEY_WIDGET`（示意图）共同决定：

==========  ==================================  ==================================
``kind``    控件                                 取值语义
==========  ==================================  ==================================
``bool``    :class:`_Switch`（自绘滑动开关）    开 = ``Yes``，关 = ``No``
``enum``    :class:`_Segmented`（自绘分段选择）  首项「默认」= 不写入；其余项原样写入
``int``     :class:`_PresetNumber` / ``QSpinBox`` 写入十进制整数
``str``     :class:`_LineEdit`（``QLineEdit``） 原样写入
==========  ==================================  ==================================

**示意图选择**（:data:`KEY_WIDGET`）—— 凡选项本身有「位置 / 形状 / 档位」含义的，
都用一张能代表它的示意图让用户直接点，而不是让用户去读文字：

==========================  ====================================================
key                         示意图控件
==========================  ====================================================
``TabPosition``             :class:`_BorderPicker` —— 点小窗口的某条边
``TabShape``                :class:`_TabShapePicker` —— 点圆角/三角小标签
``plt_export_dpi``          :class:`_PresetNumber` —— 档位按钮 + 自定义输入
==========================  ====================================================

⚠️ 示意图只改变「怎么选」，**不改变存什么**：写进持久化文件的仍是原来的字符串
或整数。

版式与视觉（2026-10-18 重做）
------------------------------
本界面**完全不使用样式表（QSS）**，所有「现代感」都由四样东西实现：

1. **分组卡片**：条目按 :data:`KEY_GROUP`（外观 / 启动 / 控制台 / 其它）分成卡片，
   每张卡片有自己的标题与留白；
2. **按类型决定行高**：示意图最大、开关最小巧 —— 行高跟着控件走，让每一行的
   视觉重量与它的交互复杂度相称，而不是所有行压成一个统一高度；
3. **原生绘制 + 点击动画**：开关、分段选择器、三类示意图、已修改色条、分组标题
   的强调线全部用 ``QPainter`` 画，颜色**只从当前 ``QPalette`` 取**（亮色 / 暗色
   自动跟随，也不会被用户的 ``zml_window_style.qss`` 盖掉）。点击时有短促的
   高亮脉冲（:class:`_AnimMixin`，120~220 ms），悬停有预览高亮；
4. **字体层次**：标题加粗放大、说明用混合得到的次要色（与 ``user_admin.CheckCountView``
   / ``gui_iter_edit`` 同一做法）。

⚠️ **为什么不用 QSS**：本程序会加载用户可编辑的 ``zml_window_style.qss``，还有
暗色模式。控件里一旦写死 ``color`` / ``background``，要么在暗色下看不清，要么把
用户主题盖掉。这里连自绘的色块也**不写任何色值**，一律从调色板派生。

⚠️ **读取时系统环境变量优先**（见 :meth:`zmlx.system.app_data.getenv`）：若某个键
在系统环境变量里已有取值，本界面写进持久化文件的取值会被它盖住、**改了不生效**。
这种键会：显示**实际生效的值**、**置灰禁止编辑**，并在备注处标出
「已被系统环境变量覆盖」。要在此修改，得先清除那个环境变量。

Modified by DeepSeek, 2026-10-02: 配合 getenv() 改为系统环境变量优先，被覆盖的键
置灰 + 提示；同时修正载入取值时会触发 _save 把读到的东西又写回文件的副作用
（现在统一用 _set_silently 屏蔽信号）。

Modified by DeepSeek, 2026-10-18: 引入 ``kind`` / ``default`` —— 控件按真实默认值
初始化，复选框与下拉框不再把「未设置」显示成空；DPI 的取值范围改为代码真正
校验的 50~3000；被系统环境变量覆盖时按钮/下拉框正确回显生效值。

Modified by DeepSeek, 2026-10-18: 界面重做 —— 分组卡片 + 按类型决定行高 +
自绘开关/分段选择器/色条（无 QSS），配色一律跟随调色板。
"""
import os

from zmlx.system import app_data, execute_once
from zmlx.ui import gui, settings
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

#: 统一的外边距与间距（避免各处 margin 随手给值造成节奏凌乱）。
MARGIN = 18
GAP = 12

#: 「次要文字」的混合比例：把文字色按此比例混进背景色。
MUTED_RATIO = 0.45

#: 左侧「已修改」色条的宽度与长度（像素）。
ACCENT_WIDTH = 3
ACCENT_HEIGHT = 26

#: **按控件类型决定的参数区高度**（像素）。
#:
#: 这是本次重做的关键：行高跟着控件走，而不是所有行一个高度。开关最小巧，
#: 数字框最高（带上下箭头）。示意控件各自另有尺寸（见它们的 ``WIDTH/HEIGHT``）。
FIELD_HEIGHT = {
    'bool': 26,
    'int': 30,
    'enum': 30,
    'str': 30,
}

#: 基础控件的固定宽度：所有行的控件右对齐在同一条竖直线上，形成清晰的栏。
FIELD_WIDTH = 230

#: 分组顺序与「哪些 key 归哪组」。
#:
#: ⚠️ 这些归属**写在控件里**，不依赖 ``zml_env_items.json`` 多带一个 ``group``
#: 字段 —— 数据表是「通用模板」，而「怎么分组、用哪种示意控件」是**本界面自己的
#: 呈现决策**。放在这里的好处是：数据表保持最小（只有 label/key/kind/default/
#: note），而界面想怎么组织都可以，二者互不绑架。
GROUP_ORDER = ['外观', '启动', '控制台', '其它']

#: key → 分组。没列到的归「其它」。
KEY_GROUP = {
    'TabPosition': '外观',
    'TabShape': '外观',
    'disable_splash': '启动',
    'show_readme': '启动',
    'restore_window_geometry': '启动',
    'load_window_style': '启动',
    'show_info_after_code_open': '启动',
    'Qt_version': '启动',
    'console_priority': '控制台',
    'disable_timer': '控制台',
    'use_web_engine': '控制台',
    'plt_export_dpi': '控制台',
}

#: key → 更直观的**示意控件**（见 :class:`_BorderPicker` / :class:`_TabShapePicker`
#: / :class:`_PresetNumber`）。没列到的按 ``kind`` 用基础控件。
#:
#: 判据：只有当「选项本身有空间位置 / 形状 / 档位含义」时，示意图才比文字更清楚。
KEY_WIDGET = {
    'TabPosition': 'border',       # 点小窗口的某条边 = 标签栏停靠在哪
    'TabShape': 'tabshape',        # 点圆角/三角小标签
    'plt_export_dpi': 'presets',   # 常用档位 + 自定义输入
}

#: ``plt_export_dpi`` 的快捷档位（仍是整数写入；档位只是快捷入口）。
#:
#: 取值参考：96 屏显常用、150 折中、300 印刷级、600 高精度矢量转位图。
#: ⚠️ 每一档都必须落在读取方校验的 50~3000 之内，否则 ``QSpinBox`` 会截断。
KEY_PRESETS = {
    'plt_export_dpi': [96, 150, 300, 600],
}


def _env_override(key):
    """返回同名**系统环境变量**的取值；没有定义（或为空）时返回 None。

    ⚠️ 判据与 :meth:`zmlx.system.app_data.getenv` 的查找顺序保持一致：系统环境
    变量优先，且**空字符串视为「没有定义」**（对应 getenv 的
    ``ignore_empty=True`` 默认行为）。

    Args:
        key: 配置项名称。

    Returns:
        Optional[str]: 系统环境变量里的取值；未定义或为空时返回 None。
    """
    try:
        value = os.environ.get(key)
    except Exception:      # 非法的键（如非字符串）一律当作「没有定义」
        return None
    if isinstance(value, str) and len(value) > 0:
        return value
    return None


def _blend(color_a, color_b, ratio):
    """把两种颜色按比例混合（``ratio=0`` 全取 a，``1`` 全取 b）。

    与 ``plugins/builtin/user_admin.py`` 的同名做法一致：只在调色板内部混合，
    不引入任何写死的色值 —— 亮色 / 暗色主题因此自动跟随。

    Args:
        color_a: 起始色。
        color_b: 目标色。
        ratio: 混合比例（超出 0~1 会被夹住）。

    Returns:
        QtGui.QColor: 混合结果。
    """
    ratio = min(max(float(ratio), 0.0), 1.0)
    return QtGui.QColor(
        int(color_a.red() + (color_b.red() - color_a.red()) * ratio),
        int(color_a.green() + (color_b.green() - color_a.green()) * ratio),
        int(color_a.blue() + (color_b.blue() - color_a.blue()) * ratio))


class _WrapLabel(QtWidgets.QLabel):
    """会自动折行、且**最小宽度可以压得很小**的标签。

    ⚠️⚠️ **为什么不用裸 ``QLabel(wordWrap=True)``**（这是本界面踩得最深的一个坑）：

    1. 裸 QLabel 的 ``minimumSizeHint`` 在 wordWrap 下会退化成「最长那个词有多
       宽」—— 一句长中文注释能把整行的最小宽度顶到几百像素（实测 498px），进而
       把整块界面撑住，窗口再也缩不窄；
    2. 于是很自然会想 ``setMinimumWidth(1)`` 放开它 —— 但那样 Qt 会拿**宽度 1**
       去算 ``sizeHint().height()``：一句话按 1px 宽折行 = 几十行 = 349px 高
       （实测），结果标题被顶到最上面、正文贴着中间，中间一大片空白。

    正解是让高度**跟着实际宽度算**（``heightForWidth``）：宽的时候一行写完，窄
    的时候自然折几行，既不会撑宽界面、也不会凭空长出一大块空白。

    ⚠️ 用 ``Policy.Preferred`` + ``hasHeightForWidth``：Qt 的布局会据此调用
    :meth:`heightForWidth`；垂直方向给 ``Maximum``，表示「不要再额外拉伸」。
    """

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setMinimumWidth(1)
        policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def hasHeightForWidth(self):
        """本标签的高度依赖宽度（折行）。"""
        return True

    def heightForWidth(self, width):
        """按给定宽度算出折行后需要的高度。

        ⚠️⚠️ **不能调 ``super().heightForWidth()``**（踩得很深）：``QLabel`` 的实现
        会走一遍**完整排版**，排版过程中又问 ``sizeHint``，而 ``sizeHint`` 又回来问
        ``heightForWidth`` —— 与本控件外层的布局回调构成环。表现是**进程直接崩溃**
        （栈溢出，连 traceback 都没有），实测窗口拖到 520px 就必崩。

        这里改用 ``QFontMetrics.boundingRect`` 的换行排版，**纯计算、不碰任何
        widget 状态**，所以不可能递归。
        """
        text = self.text()
        width = max(int(width), 1)
        if not text:
            return self.fontMetrics().lineSpacing()
        rect = self.fontMetrics().boundingRect(
            0, 0, width, 0xFFFFFF,
            int(QtCore.Qt.TextFlag.TextWordWrap) | int(QtCore.Qt.AlignmentFlag.AlignLeft),
            text)
        # 上下各留一点余量，避免最后一行的降部被裁
        return max(rect.height(), self.fontMetrics().lineSpacing()) + 2

    def minimumSizeHint(self):
        """最小尺寸：宽度可以压到 1，高度只要求**一行**。

        ⚠️ 高度用一行而不是 ``heightForWidth(1)``：那会把整句按 1px 折行算成
        几十行，进而撑高（甚至撑宽）整个布局。
        """
        return QtCore.QSize(1, self.fontMetrics().lineSpacing())

    def resizeEvent(self, event):
        """宽度变了 → 高度会变，通知布局重新算。"""
        super().resizeEvent(event)
        self.updateGeometry()


class EnvEdit(QtWidgets.QWidget):
    """环境变量编辑器（分组卡片 + 搜索过滤 + 按类型决定行高）。

    整体版式自上而下三块：

    - **顶部工具条**：标题 + 搜索框 + 「仅显示已修改」+「全部还原」；
    - **状态条**：一句话说清「有多少项被改过 / 被系统环境变量覆盖」；
    - **滚动列表**：按 ``group`` 分组的卡片，每张卡片内一行一项，
      ``label + 说明`` 在左、控件在右；左侧色条标出「这一项被改过」。

    每个值控件都暴露 ``reset_to_default()``（由 :meth:`reset_all` 汇总调用），
    用于把某个键**彻底还原成「未设置」**——即删除持久化文件，让代码自己的
    默认值重新生效。

    ⚠️ **不使用任何样式表**：见模块文档「版式与视觉」。
    """

    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.env_items = items
        self._widgets = []          # [值控件]（都带 key / default / reset_to_default）
        self._rows = []             # [(item, 行控件)] —— 过滤与重绘用
        self._only_modified = False
        self._in_sync = False

        self._build_ui()
        self._refresh_status()

    # ------------------------------------------------------------------ 构建

    def _build_ui(self):
        """搭建整体版式（先搭骨架，再填分组）。"""
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        outer.setSpacing(GAP)

        outer.addLayout(self._build_toolbar())
        outer.addWidget(self._build_status())
        outer.addWidget(self._build_scroll(), stretch=1)

    def _build_toolbar(self):
        """顶部工具条：标题 + 搜索 + 过滤 + 还原。"""
        bar = QtWidgets.QHBoxLayout()
        bar.setSpacing(GAP)

        title = QtWidgets.QLabel('系统')
        font = title.font()
        font.setPointSizeF(max(font.pointSizeF() + 4.0, 6.0))
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        title.setFont(font)
        bar.addWidget(title)

        caption = self._caption = QtWidgets.QLabel(
            '以下各项的初始状态，即程序当前实际生效的取值')
        caption.setFont(self._muted_font())
        # ⚠️ 工具条里每一项都允许被压缩：标题 + 这句说明 + 搜索框 + 复选框 + 按钮
        #    各自的最小宽度累加起来，会把整个界面钉在 588px 上（实测窗口请求 160px
        #    时实际仍有 588px），于是内部永远不进入「窄」布局、文字区也缩不下来。
        caption.setMinimumWidth(1)
        caption.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                              QtWidgets.QSizePolicy.Policy.Preferred)
        bar.addWidget(caption)

        bar.addStretch(1)

        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText('搜索配置…')
        self._search.setClearButtonEnabled(True)
        self._search.setMaximumWidth(220)
        self._search.setMinimumWidth(60)
        self._search.textChanged.connect(self._apply_filter)
        bar.addWidget(self._search)

        self._filter_box = QtWidgets.QCheckBox('仅显示已修改')
        self._filter_box.setToolTip('只看那些被改过、与默认值不同的项')
        self._filter_box.toggled.connect(self._on_filter_toggled)
        bar.addWidget(self._filter_box)

        self._reset_button = QtWidgets.QPushButton('全部还原')
        self._reset_button.setToolTip(
            '删除本界面写入的全部配置，让程序内部的默认值重新生效。\n'
            '（系统环境变量不受影响）')
        self._reset_button.clicked.connect(self.reset_all)
        bar.addWidget(self._reset_button)

        return bar

    def _build_status(self):
        """状态条：当前有多少项被改过、有多少项被系统环境变量覆盖。"""
        self._status = _StatusStrip()
        return self._status

    def sizeHint(self):
        """建议尺寸：偏宽一点，让示意图与说明都能舒展。

        ⚠️ **这是「建议」不是「要求」**：真正决定能不能缩窄的是
        :meth:`minimumSizeHint`。早先 ``minimumSizeHint`` 一路被示意图的
        ``setMinimumSize(WIDTH, ...)`` 顶到 588px，于是窗口窄于这个值时只会
        出横向滚动条、而不是把内容压窄 —— 用户看到的就是「这个界面太窄会
        撑坏」。现在示意图给的是更小的下限，界面的最小宽度才真正掉得下来。
        """
        return QtCore.QSize(820, 640)

    def minimumSizeHint(self):
        """最小尺寸：**故意给得很小**，让窗口变窄时是内容收缩，而不是撑宽上级。

        ⚠️ Qt 里 ``minimumSizeHint`` 会沿着布局向上传递（它会撑起上一级控件）。
        一个设置界面没有理由要求用户至少给 588px 宽 —— 窄的时候藏掉说明、收缩
        示意图就好，这比「窗口拉不小」或「满屏横向滚动条」都合理。
        """
        return QtCore.QSize(360, 240)

    def _build_scroll(self):
        """滚动区：按 group 分组的卡片列表。"""
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        # 窄到连控件都放不下时才出横向滚动条（说明文字已经由 _ConfigRow 自适应
        # 藏掉了，所以正常情况下不会出现）。
        self._scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, GAP, 0)
        layout.setSpacing(GAP + 4)

        groups = self._grouped_items()
        if len(groups) == 0:
            empty = QtWidgets.QLabel('没有可显示的配置项。')
            empty.setFont(self._muted_font())
            layout.addWidget(empty)
            self._reset_button.setEnabled(False)
        for group, group_items in groups.items():
            layout.addWidget(self._create_group(group, group_items))

        layout.addStretch(1)
        self._scroll.setWidget(container)
        return self._scroll

    def _grouped_items(self):
        """按 :data:`KEY_GROUP` 分组，返回 ``{组名: [条目]}``（保持约定顺序）。

        分组归属在**本文件内**决定（见 :data:`KEY_GROUP` 的说明），数据表不需要
        知道「界面怎么分组」。没登记的 key 一律归「其它」。
        """
        groups = {}
        for item in (self.env_items or []):
            key = item.get('key')
            if not key:
                continue
            group = KEY_GROUP.get(key, '其它')
            groups.setdefault(group, []).append(item)

        ordered = {}
        for name in GROUP_ORDER:
            if name in groups:
                ordered[name] = groups.pop(name)
        for name in sorted(groups):     # 出现约定外的新组，按名字排在后面
            ordered[name] = groups[name]
        return ordered

    def _create_group(self, group, items):
        """创建一个分组卡片（组名 + 组内各配置行）。"""
        card = _Card(self)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(0)

        head = _GroupHeader(group, len(items), card)
        layout.addWidget(head)

        for item in items:
            row = self._create_row(item, card)
            layout.addWidget(row)

        return card

    def _create_row(self, item, parent):
        """创建一行配置。

        ⚠️ **不套统一模板**：按内容的「重量」分成两种排法（见 :meth:`_layout_of`）。
        早先所有项都硬塞进「左文字 + 右控件」的行里，结果示意图那两行左边空出
        一大片，而字段行又挤。现在：

        - ``wide``  —— 带示意图 / 档位的大控件：**上下堆叠**，文字一行在左、
          示意图在右并独占剩余宽度（它本身就宽，横排最省地方）；
        - ``field`` —— 开关、下拉框、文本框这类窄控件：**左右并排**，标签在左、
          控件右对齐成一条竖线，紧凑易扫读。
        """
        kind = self._kind_of(item)
        layout_name = self._layout_of(item)
        row = _ConfigRow(self, kind, parent)

        if layout_name == 'wide':
            self._build_wide_row(row, item)
        else:
            self._build_field_row(row, item)

        widget = row.widget
        self._widgets.append(widget)
        row.key = item.get('key', '')
        row.item = item
        self._rows.append((item, row))

        # 值改变 → 更新色条与顶部的统计
        signal = getattr(widget, 'changed', None)
        if signal is not None:
            signal.connect(self._refresh_status)
        return row

    @staticmethod
    def _layout_of(item):
        """决定这一项用哪种排法：``'wide'``（示意图横排）或 ``'field'``（字段行）。

        只有**真的很高、很宽**的示意图才走 ``wide``（点边选方向、点形状选标签）：
        它们本身有半屏高，只能横着放。档位选择器（DPI）高度只有 30px、和一行文字
        差不多，走普通的字段行更紧凑 —— 这样说明文字能拿回整行的宽度，而不是被
        挤在左半边（实测 700px 时它只剩 278px，长说明被压成三行竖条）。
        """
        key = item.get('key')
        if KEY_WIDGET.get(key) == 'presets':
            return 'field'
        return 'wide' if KEY_WIDGET.get(key) else 'field'

    def _build_wide_row(self, row, item):
        """示意图类：标题 + 说明在左（说明有足够宽度），示意图在右。

        ⚠️ **说明不要塞在示意图下面**（试过一版）：示意图本身只有 220~320px 宽，
        说明挤在那个宽度里会被折成三四个字一行，再被行高裁掉，读不了。放在左侧
        文字栏里，它能用上整行剩下的宽度。
        """
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(GAP, 8, GAP + 4, 8)
        layout.setSpacing(GAP)

        # ---- 左：标题 + 说明（整体垂直居中）----
        # ⚠️ 弹簧只能放在**两端**，标题与说明之间不能再有弹簧：宽行里的示意图
        #    很高，一旦内部夹了弹簧，标题会被推到顶上、说明被推到底下，中间空出
        #    半屏（实测窄窗口就是这副样子）。这里用一个内层容器把「标题+说明」
        #    捆成**一整块**，再让这一整块居中。
        text_host = QtWidgets.QWidget(row)
        text_host.setMinimumWidth(_ConfigRow.TEXT_MIN_WIDTH)
        text_host_layout = QtWidgets.QVBoxLayout(text_host)
        text_host_layout.setContentsMargins(0, 0, 0, 0)
        text_host_layout.setSpacing(0)
        text_host_layout.addStretch(1)

        block = QtWidgets.QWidget(text_host)
        block_layout = QtWidgets.QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(3)

        title = self._make_title(item, block)
        title_font = QtGui.QFont(self.font())
        title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        title.setFont(title_font)
        block_layout.addWidget(title)

        row.note_label = self._make_note(item, block)
        if row.note_label is not None:
            block_layout.addWidget(row.note_label)

        # ⚠️ block 必须「按内容取高」，不能吃余量：它在 text_host 里、上下各有一个
        #    弹簧，若 block 自己能拉伸，弹簧形同虚设，block 会占满整列高度，里面
        #    的 note 也就被拉成一大块空白（实测 349px）。
        block.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                            QtWidgets.QSizePolicy.Policy.Maximum)

        text_host_layout.addWidget(block)
        text_host_layout.addStretch(1)
        layout.addWidget(text_host, stretch=1)
        row.set_text_host(text_host)

        # ---- 右：示意图（垂直居中）----
        # ⚠️ 用 maximumWidth 而不是 setFixedSize（那样界面最小宽度会被示意图钉死）：
        #    示意图可以**让出**一点宽度给文字栏，但优先取满 ``WIDTH``。
        #    ⚠️ 光设 maximumWidth 不够：自绘控件没写 sizeHint 时默认是 0，布局只会
        #    按 minimumWidth（150）分配 —— 实测示意图永远只有 150px 宽，标签名字
        #    被挤成省略号。所以下面再显式 setFixedWidth 到完整宽度，minimumWidth
        #    只在整体放不下时才起作用。
        width, height = self._field_size(item)
        widget = self._create_widget(item, row)
        widget.setFixedHeight(height)
        widget.setMinimumWidth(min(width, widget.minimumWidth()))
        widget.setFixedWidth(width)
        row.widget = widget
        row.field_width = width
        layout.addWidget(widget, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

    def _build_field_row(self, row, item):
        """字段类：标签（+说明）在左，控件右对齐。"""
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(GAP, 6, GAP + 4, 6)
        layout.setSpacing(GAP)

        # ⚠️ 用容器 + 上下弹簧垂直居中：同一张卡片里若混有较高的示意图行，
        #    文字直接贴顶会显得「上重下轻」。
        text_host = QtWidgets.QWidget(row)
        # ⚠️⚠️ 文字栏给一个**宽度下限**（构造期一次性设定，运行期不再改动）：
        #    左侧控件有固定的最小宽度（分段选择器 320px），窗口拖到很窄时布局只能
        #    从文字栏里扣，一路扣到 1px —— 标题就变成又窄又高的一根竖线，一个字都
        #    读不出来（实测 400px 窗口下 Qt_version 的标题是 1×40）。
        #    与其这样，不如让文字栏守住下限、整行放不下时由横向滚动条兜底：
        #    至少每一行都还读得懂。
        #    ⚠️ 必须在**构造期**设好：运行期改这个值会让布局在 Resize 事件里再排
        #    一次，形成 Qt 事件级死循环（实测进程栈溢出崩溃，无 traceback）。
        text_host.setMinimumWidth(_ConfigRow.TEXT_MIN_WIDTH)
        text_host_layout = QtWidgets.QVBoxLayout(text_host)
        text_host_layout.setContentsMargins(0, 0, 0, 0)
        text_host_layout.setSpacing(0)
        text_host_layout.addStretch(1)

        text_box = QtWidgets.QVBoxLayout()
        text_box.setSpacing(2)
        text_box.addWidget(self._make_title(item, text_host))

        row.note_label = self._make_note(item, text_host)
        if row.note_label is not None:
            text_box.addWidget(row.note_label)
        text_host_layout.addLayout(text_box)
        text_host_layout.addStretch(1)
        layout.addWidget(text_host, stretch=1)
        row.set_text_host(text_host)

        width, height = self._field_size(item)
        field = QtWidgets.QWidget(row)
        field_layout = QtWidgets.QVBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(0)
        field_layout.addStretch(1)

        widget = self._create_widget(item, field)
        widget.setFixedHeight(height)
        field_layout.addWidget(widget, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        field_layout.addStretch(1)

        # ⚠️ 容器**贴合控件的实际宽度**，不要一律 ``setFixedWidth(230)``：开关本身
        #    只有 46px，配一个 230px 的容器等于白占 184px —— 而这块空白正是从
        #    说明文字那里抢走的（实测 700px 窗口下开关行的说明只剩 368px，长说明
        #    被压成三行竖条）。需要整栏的控件（分段选择器、档位选择器等）反过来
        #    把容器撑到 ``width``（但不超过给它的地方）。
        natural = widget.sizeHint().width() if widget.sizeHint().isValid() else 0
        field.setFixedWidth(max(min(width, natural if natural > 0 else width),
                                 widget.minimumWidth(), 1))

        row.widget = widget
        layout.addWidget(field, 0)

    def _make_title(self, item, parent):
        """创建标题标签（可压缩，长标题允许折行）。

        ⚠️ 用 :class:`_WrapLabel`：裸 ``QLabel`` 的 ``minimumSizeHint`` 是「整句
        不折行时的宽度」，长标题（如「导出 Matplotlib 绘图时的默认 DPI」实测
        288px）会把整行的最小宽度顶上去，进而**撑住上一级控件** —— 窗口窄了就
        缩不下来。窄的时候标题折成两行，也好过整个界面装不进去。
        """
        return _WrapLabel(item.get('label', ''), parent)

    def _make_note(self, item, parent):
        """创建说明标签；没有说明时返回 None。

        ⚠️ 是否**显示**它由 :meth:`_apply_responsive` 按可用宽度决定（空间窄时
        整条藏起来，只留标题）—— 所以这里只负责创建，不负责可见性。

        ⚠️⚠️ 必须用 :class:`_WrapLabel` 而不是裸 ``QLabel``：见那个类的说明 ——
        裸 QLabel 在 ``wordWrap`` + 窄最小宽度下会按**宽度 1** 算高度，一句话被
        折成几十行，撑出一个几百像素的空白块。
        """
        note = (item.get('note') or '').strip()
        if not note:
            return None
        label = _WrapLabel(note, parent)
        label.setFont(self._muted_font())
        return label

    @staticmethod
    def _kind_of(item):
        """推断条目的控件类型（兼容没有 ``kind`` 的旧数据）。"""
        kind = item.get('kind')
        if kind is not None:
            return kind
        return 'enum' if item.get('items') else 'str'

    @staticmethod
    def _widget_kind(item):
        """返回本条目要用的**示意控件**名；``None`` 表示用 ``kind`` 的基础控件。

        ⚠️ 读的是本文件的 :data:`KEY_WIDGET`，**不是**数据表里的字段 —— 数据表
        （``zml_env_items.json``）是通用模板，只描述「有什么选项、默认是什么」；
        「用示意图还是文字框」是**本界面的呈现决策**，不该倒灌进数据。
        """
        return KEY_WIDGET.get(item.get('key'))

    def _create_widget(self, item, parent):
        """根据 :data:`KEY_WIDGET` / ``kind`` 创建最合适的输入控件。

        优先级：示意控件（:data:`KEY_WIDGET`）> 基础控件（``kind``）。
        """
        widget = self._widget_kind(item)
        if widget == 'border':
            return _BorderPicker(item, parent)
        if widget == 'tabshape':
            return _TabShapePicker(item, parent)
        if widget == 'presets':
            return _PresetNumber(item, parent,
                                 presets=KEY_PRESETS.get(item.get('key')))

        kind = self._kind_of(item)
        if kind == 'bool':
            return _Switch(item, parent)
        elif kind == 'enum':
            return _Segmented(item, parent)
        elif kind == 'int':
            return _SpinBox(item, parent)
        else:
            return _LineEdit(item, parent)

    def _field_size(self, item):
        """返回控件区的 ``(宽, 高)``。

        ⚠️ **行高跟着控件走**：示意图（点边选方向、档位按钮）需要更大的点击
        面积，开关最小巧。这样每一行的视觉重量与它的交互复杂度相称。

        ⚠️ 枚举用**更宽的**控件区：分段选择器要把每段文字摊开写清楚，230px 只
        够放 2 段短词。段数多的枚举会自己退化成下拉框（见
        :meth:`_Segmented._can_use_segments`），那种情况下宽一点也无妨。
        """
        widget_name = self._widget_kind(item)
        if widget_name == 'border':
            return (_BorderPicker.WIDTH, _BorderPicker.HEIGHT)
        if widget_name == 'tabshape':
            return (_TabShapePicker.WIDTH, _TabShapePicker.HEIGHT)
        if widget_name == 'presets':
            return (_PresetNumber.WIDTH, _PresetNumber.HEIGHT)
        kind = self._kind_of(item)
        if kind == 'enum':
            return (_Segmented.WIDTH, FIELD_HEIGHT.get(kind, 30))
        return (FIELD_WIDTH, FIELD_HEIGHT.get(kind, 30))


    def _muted_font(self):
        """比默认小一号的字体（说明 / 次要文字用）。"""
        font = self.font()
        size = font.pointSizeF()
        if size > 0:
            font.setPointSizeF(max(size - 1.0, 6.0))
        return font

    # ------------------------------------------------------------------ 过滤

    def _on_filter_toggled(self, value):
        """「仅显示已修改」被切换。"""
        self._only_modified = bool(value)
        self._apply_filter()

    def _apply_filter(self, *args):
        """按搜索词与「仅显示已修改」隐藏不匹配的行与空的分组。"""
        text = self._search.text().strip().lower()
        for item, row in self._rows:
            haystack = ' '.join([
                str(item.get('label', '')), str(item.get('key', '')),
                str(item.get('note', ''))]).lower()
            match = len(text) == 0 or text in haystack
            if match and self._only_modified:
                match = row.widget.is_modified()
            row.setVisible(match)

        # 组内一行都不剩时，把整张分组卡片也藏起来
        for card in self.findChildren(_Card):
            rows = card.findChildren(_ConfigRow)
            if len(rows) == 0:
                continue
            card.setVisible(any(not r.isHidden() for r in rows))

    # ------------------------------------------------------------------ 状态

    def _refresh_status(self):
        """刷新色条、状态条与「全部还原」按钮的可用性。"""
        modified = [w for w in self._widgets if w.is_modified()]
        overridden = [w for w in self._widgets if w.is_overridden()]
        for _item, row in self._rows:
            row.set_modified(row.widget.is_modified())
        self._status.set_state(
            total=len(self._widgets),
            modified=len(modified),
            overridden=len(overridden))
        self._reset_button.setEnabled(len(modified) > 0)
        if self._only_modified:
            self._apply_filter()

    def reset_all(self):
        """把本界面写入的所有配置还原为默认（删除持久化文件）。"""
        count = 0
        for widget in self._widgets:
            try:
                widget.reset_to_default()
                count += 1
            except Exception as err:
                print(f'还原配置 <{widget.key}> 失败: {err}')
        self._refresh_status()
        print(f'已还原 {count} 项配置（重启程序后生效）')

    def resizeEvent(self, event):
        """整个界面尺寸变化时，让各行重新决定「说明要不要显示」。

        ⚠️ 必须在这里主动分发：行在滚动区里被横向撑成固定宽度，窗口缩小时
        **行自己的 ``resizeEvent`` 根本不会触发**（实测：窗口 520px 时行宽仍是
        648px）。只有从这里（真正知道视口变化的层级）逐个通知才可靠。
        """
        super().resizeEvent(event)
        self._sync_responsive()

    def _sync_responsive(self):
        """按当前尺寸刷新所有行的说明可见性。

        ⚠️ 必须先 ``activate()`` 布局：``resizeEvent`` 发生的**那一刻**，子控件的
        几何还是旧的（Qt 在事件之后才重新排布）。不激活就量 ``widget.width()``，
        得到的是上一轮的宽度 —— 于是「该藏的没藏」（实测 560px 时 ``Qt_version``
        的说明要排 3.8 行仍被留下，就是量到了旧的 320px）。

        ⚠️⚠️ **本方法会改动布局，所以必须防重入**：``setVisible`` /
        ``setMinimumWidth`` 都会引起重新布局 → 又触发 ``resizeEvent`` → 再回到
        这里。没有闸门就是无限循环，表现为**进程直接崩掉（无异常、无 traceback，
        是栈溢出）**—— 实测把窗口拖到 520px 就必崩。
        """
        if self._in_sync:
            return
        self._in_sync = True
        try:
            layout = self.layout()
            if layout is not None:
                layout.activate()
            for _item, row in self._rows:
                row.update_responsive()
            # 工具条副标题：窄时藏掉，把地方留给控件本身。
            # ⚠️ 也只在**跨过边界**时才 setVisible，避免无谓的布局抖动。
            caption = getattr(self, '_caption', None)
            if caption is not None:
                want = self.width() >= 720
                if caption.isVisibleTo(self) != want:
                    caption.setVisible(want)
        finally:
            self._in_sync = False

    def showEvent(self, event):
        """首次显示后再同步一次（构造期算出的几何还不准）。"""
        super().showEvent(event)
        QtCore.QTimer.singleShot(0, self._sync_responsive)


# ============================================================
# 值控件
# ============================================================

class _BaseWidget:
    """所有配置控件的基类（mixin 模式用于类型标注）。

    ⚠️ 子类的 MRO 是「Qt 控件在前、本 mixin 在后」，所以这里只放与 Qt 语义无关的
    通用逻辑（取值、屏蔽信号、覆盖提示），不要覆盖 Qt 自己的方法名。

    ⚠️ 勾选框的语义，**一律用条目里的 ``default`` 表达**，不要靠「词义上的正反」
    去猜：``default`` 就是「该键被显式设为 Yes 时、代码里那个开关是否处于『开』
    的状态」—— 也就是「未设置时界面上应该勾着吗」。所以
    ``disable_timer`` / ``disable_splash`` / ``disable_auto_feedback`` 这类
    「禁用类」开关的 ``default`` 填 ``False``，``use_web_engine`` 这类填 ``True``，
    两者都遵循同一条规则：**开 = 持久化文件里写 Yes**。

    子类必须提供：

    - ``_load()``：按生效值刷新控件外观；
    - ``is_modified()``：当前状态是否与「程序内部的默认值」不同；
    - 属性 ``changed``：值被改动时发出（父控件据此刷新统计）。

    ``is_overridden()`` 由本 mixin 统一提供（读 ``_overridden`` 快照）。
    """

    key = ''
    default = None

    def _init_item(self, item):
        """从配置条目里取出本控件要用的字段。"""
        self.key = item.get('key', '')
        self.default = item.get('default', None)
        self._overridden = _env_override(self.key) is not None

    def is_overridden(self):
        """该键是否被同名的系统环境变量覆盖。"""
        return bool(getattr(self, '_overridden', False))

    def _set_silently(self, setter, value):
        """设置控件取值，但**不触发**落盘。

        ⚠️ 必须屏蔽信号：否则 ``_load()`` 里的一次 set 会被 ``valueChanged`` /
        ``currentIndexChanged`` 之类的信号引到 ``_save()``，把**刚读到的值又写回
        文件**（被环境变量覆盖时更糟 —— 会把环境变量的值写进持久化文件）。
        """
        self.blockSignals(True)
        try:
            setter(value)
        finally:
            self.blockSignals(False)

    def _effective_text(self):
        """读取本键**实际生效**的原始文本取值（系统环境变量优先）。

        与 :meth:`zmlx.system.app_data.getenv` 完全同构：系统环境变量里非空的
        取值优先，否则读持久化文件；两处都没有时返回 ``None``（= 未设置）。

        Returns:
            Optional[str]: 生效的原始取值；未设置时 ``None``。
        """
        override = _env_override(self.key)
        if override is not None:
            # 置灰：在本界面改它不会有任何效果（写进文件也会被环境变量盖住）
            self.setEnabled(False)
            self.setToolTip(
                f'⚠️ 该配置已被系统环境变量 <{self.key}> 覆盖。\n'
                f'当前生效值：{override}\n'
                f'在本界面的修改不会生效；如需在此修改，请先清除该环境变量。')
            return override
        value = app_data.getenv(
            self.key, encoding='utf-8', default=None, ignore_empty=True)
        if not isinstance(value, str) or len(value) == 0:
            return None
        return value

    def _stored_text(self):
        """只看**持久化文件**里的取值（忽略系统环境变量）；未设置返回 None。"""
        value = app_data.getenv(
            self.key, encoding='utf-8', default=None, ignore_empty=True,
            use_environ=False)
        if not isinstance(value, str) or len(value) == 0:
            return None
        return value

    def _save(self, value):
        """写入持久化文件（``value`` 为 None 表示「不写入」）。"""
        if value is None:
            self._remove()
            return
        app_data.setenv(key=self.key, value=value, encoding='utf-8')

    def _remove(self):
        """删除本键的持久化文件（不抛异常）。"""
        try:
            os.remove(app_data.root('env', self.key))
        except FileNotFoundError:
            pass

    def reset_to_default(self):
        """删除本键的持久化文件，使其回到程序内部的默认值。"""
        self._remove()
        self._load()
        self.changed.emit()


class _LineEdit(QtWidgets.QLineEdit, _BaseWidget):
    """自由文本输入。"""

    changed = QtCore.pyqtSignal()

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self.setClearButtonEnabled(True)
        self.editingFinished.connect(lambda: self._save(self.text()))
        self._load()

    def _load(self):
        value = self._effective_text()
        text = value if value is not None else str(self.default or '')
        self._set_silently(self.setText, text)
        self.changed.emit()

    def is_modified(self):
        """与默认值不同吗（只比较持久化文件里的值）。"""
        stored = self._stored_text()
        if stored is None:
            return False
        return stored != str(self.default if self.default is not None else '')


class _SpinBox(QtWidgets.QSpinBox, _BaseWidget):
    """整数配置（DPI 等）。

    ⚠️ ``min`` / ``max`` 必须与读取方真正校验的区间一致（``plt_export_dpi`` 的
    读取代码校验的是 50~3000）；否则越界值会被 QSpinBox **静默截断**成边界值，
    用户看到的数就不是他存进去的数。
    """

    changed = QtCore.pyqtSignal()

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self.setRange(int(item.get('min', 1)), int(item.get('max', 1000000)))
        try:
            self._default_int = int(item.get('default', self.minimum()))
        except (TypeError, ValueError):
            self._default_int = self.minimum()
        self.setSingleStep(10)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        if item.get('key') == 'plt_export_dpi':
            self.setSuffix(' dpi')
        self.valueChanged.connect(self._save)
        self._load()

    def _load(self):
        value = self._effective_text()
        try:
            number = int(value) if value is not None else self._default_int
        except (TypeError, ValueError):
            number = self._default_int
        self._set_silently(self.setValue, number)
        self.changed.emit()

    def _save(self, value=None):
        app_data.setenv(key=self.key, value=str(self.value()), encoding='utf-8')
        self.changed.emit()

    def is_modified(self):
        """是否显式存过一个非默认的数值。"""
        stored = self._stored_text()
        if stored is None:
            return False
        try:
            return int(stored) != self._default_int
        except (TypeError, ValueError):
            return True


class _AnimMixin:
    """给自绘控件加**点击反馈动画**的公共部分。

    三个状态组成一次动画：

    - ``_progress``：0.0 → 1.0，「已选中」的程度（用于颜色插值）；
    - ``_flash``：点击后一次短暂的「高亮脉冲」（0 → 1 → 0）；
    - ``_hover``：悬停目标（由子类自己维护）。

    ⚠️ 用 ``QVariantAnimation``（**不是** ``QPropertyAnimation``）：后者要求操作一个
    真正的 Qt 属性，而我们只需要一个浮点数 + ``update()``。

    ⚠️ 动画都**很短**（120~220 ms）：这类设置界面会被反复点击，慢了就成了负担。
    动画只触发 ``self.update()`` —— 不重排布局、不阻塞输入。
    """

    #: 「选中态」切换动画时长（毫秒）。
    ANIM_DURATION = 160

    def _init_anim(self):
        """创建动画对象（子类在自己的 ``__init__`` 里调用一次）。"""
        self._progress = 0.0
        self._flash = 0.0

        self._anim = QtCore.QVariantAnimation(self)
        self._anim.setDuration(self.ANIM_DURATION)
        self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_progress)

        self._flash_anim = QtCore.QVariantAnimation(self)
        self._flash_anim.setDuration(220)
        self._flash_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutQuad)
        self._flash_anim.valueChanged.connect(self._on_flash)

    def _animate_progress(self, target, animated=True):
        """把「选中程度」平滑推向 ``target``（0.0~1.0）。"""
        target = float(target)
        target = min(max(target, 0.0), 1.0)
        if not animated:
            self._anim.stop()
            self._progress = target
            self.update()
            return
        if abs(self._progress - target) < 0.001:
            return
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(target)
        self._anim.start()

    def _pulse(self):
        """点一下：跑一次「升起再落下」的高亮脉冲。"""
        self._flash_anim.stop()
        self._flash_anim.setStartValue(0.0)
        self._flash_anim.setKeyValueAt(0.4, 1.0)
        self._flash_anim.setEndValue(0.0)
        self._flash_anim.start()

    def _on_progress(self, value):
        try:
            self._progress = float(value)
        except (TypeError, ValueError):
            pass
        self.update()

    def _on_flash(self, value):
        try:
            self._flash = float(value)
        except (TypeError, ValueError):
            pass
        self.update()

    def _flash_pen(self, base_pen, color):
        """选中态描边：脉冲期间变粗、变亮，作为「刚点过」的确认。"""
        if self._flash <= 0.01:
            return base_pen
        return QtGui.QPen(color, base_pen.widthF() + 2.5 * self._flash)


class _BorderPicker(_AnimMixin, QtWidgets.QWidget, _BaseWidget):
    """标签栏停靠方向示意图：画一个小窗口，**点哪条边**，标签栏就停到哪边。

    用来替代「North / East / South / West」这样的文字下拉框 —— 文字版要求用户
    先知道 North 是「上」；示意图把答案直接画出来：标签栏就是窗口某条边上那块
    高亮的长条，点哪条边它就跳过去。

    ⚠️ 语义与枚举完全一致：写进文件的仍是 ``North`` / ``East`` / ``South`` /
    ``West``，示意图只改变「怎么选」，不改变存什么。
    再点一次**已选中的那条边** = 取消选择（不写入，回到程序默认值）。

    ⚠️ 颜色只从 ``QPalette`` 取（``Highlight`` = 停靠边、``Base``/``Window`` =
    窗口体、``Text`` 派生的次要色 = 其它边），不写任何色值。
    """

    changed = QtCore.pyqtSignal()

    WIDTH = 224
    HEIGHT = 138

    #: 四个方向（与 ``items`` 的文字一一对应）。
    SIDES = ('North', 'East', 'South', 'West')
    #: 边的厚度（代表标签栏）。
    THICK = 24
    #: 窗口体外缩，留出呼吸空间。
    INSET = 14
    #: 允许被压缩到的最小宽度。
    #:
    #: ⚠️ 不能把最小宽度设成 ``WIDTH``：那样整块界面的最小宽度就被示意图钉死
    #: （实测 588px），窗口再窄只会出横向滚动条。这里给一个更小的下限，让窗口变窄
    #: 时示意图跟着收窄，界面的最小宽度才掉得下来。
    MIN_WIDTH = 150

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self._init_anim()
        self._side = None
        self._hover = None
        self.setMinimumSize(self.MIN_WIDTH, self.HEIGHT)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._load(animated=False)

    # ---------------------------------------------------------------- 取值
    def _load(self, animated=True):
        value = self._effective_text()
        if value is not None and value in self.SIDES:
            side = value
        elif value is None:
            # 从没设置过：点亮真正生效的那一边（默认值），而不是留空
            side = self.default if self.default in self.SIDES else None
        else:
            side = None            # 存了不认识的值 → 不点亮任何边
        self._side = side
        self._animate_progress(1.0 if side is not None else 0.0, animated)
        self._sync_tooltip()
        self.changed.emit()

    def is_modified(self):
        """是否显式存过一个与默认值不同的方向。"""
        stored = (self._stored_text() or '').strip()
        if len(stored) == 0:
            return False
        return stored != str(self.default if self.default is not None else '')

    def current_side(self):
        """当前点亮的边（``None`` = 不写入，由程序默认值决定）。"""
        return self._side

    def set_side(self, side, save=True):
        """点亮某条边（``None`` = 取消选择 = 不写入）。"""
        side = side if side in self.SIDES else None
        if side == self._side:
            return
        self._side = side
        self._animate_progress(1.0 if side is not None else 0.0)
        self._pulse()
        self._sync_tooltip()
        if save:
            if side is None:
                self._remove()
            else:
                app_data.setenv(key=self.key, value=side, encoding='utf-8')
        self.changed.emit()

    def _sync_tooltip(self):
        """tooltip 说明当前选择。"""
        if self.is_overridden():
            return
        text = self._side if self._side is not None else '未设置（使用程序默认值）'
        self.setToolTip(
            f'{self.key} = {text}\n点击小窗口的某一条边来选择；'
            f'再点一次已选中的边则取消（回到默认）')

    # ---------------------------------------------------------------- 几何
    def _window_rect(self):
        """「小窗口」外框。"""
        return QtCore.QRectF(
            self.INSET, self.INSET,
            self.width() - 2 * self.INSET, self.height() - 2 * self.INSET)

    def _side_rect(self, side):
        """某条边的矩形（代表该方向上的标签栏）。"""
        rect = self._window_rect()
        thick = self.THICK
        if side == 'North':
            return QtCore.QRectF(rect.left(), rect.top(), rect.width(), thick)
        if side == 'South':
            return QtCore.QRectF(rect.left(), rect.bottom() - thick,
                                 rect.width(), thick)
        if side == 'West':
            return QtCore.QRectF(rect.left(), rect.top(), thick, rect.height())
        return QtCore.QRectF(rect.right() - thick, rect.top(),
                             thick, rect.height())

    def _side_at(self, pos):
        """坐标 ``pos`` 落在哪条边上；不在任何一条边上时返回 None。"""
        point = QtCore.QPointF(pos)
        for side in self.SIDES:
            if self._side_rect(side).contains(point):
                return side
        return None

    # ---------------------------------------------------------------- 交互
    def mousePressEvent(self, event):
        """点击某条边：选中它；点击已选中的边则取消。"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.isEnabled():
            side = self._side_at(event.position())
            if side is not None:
                self.set_side(None if side == self._side else side)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """记录悬停的边，用于预览高亮。"""
        side = self._side_at(event.position())
        if side != self._hover:
            self._hover = side
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清掉悬停。"""
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        """方向键直接选边（键盘可达性）。"""
        keys = {
            QtCore.Qt.Key.Key_Up: 'North',
            QtCore.Qt.Key.Key_Right: 'East',
            QtCore.Qt.Key.Key_Down: 'South',
            QtCore.Qt.Key.Key_Left: 'West',
        }
        if event.key() in keys:
            self.set_side(keys[event.key()])
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------------------------------------------------------------- 绘制
    def paintEvent(self, event):
        """画窗口体、四条边与当前选择。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        hl_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        background = base if base.lightness() >= window.lightness() else window
        muted = _blend(text, background, MUTED_RATIO)
        outline = _blend(background, text, 0.20)
        enabled = self.isEnabled()

        # ---- 窗口体 ----
        rect = self._window_rect()
        painter.setPen(QtGui.QPen(outline, 1))
        painter.setBrush(QtGui.QBrush(_blend(background, text, 0.04)))
        painter.drawRoundedRect(rect, 6, 6)

        # ---- 四条边 ----
        for side in self.SIDES:
            side_rect = self._side_rect(side)
            active = side == self._side
            hovered = side == self._hover

            if active:
                fill = QtGui.QColor(highlight)
            elif hovered:
                fill = _blend(background, highlight, 0.22)
            else:
                fill = _blend(background, text, 0.08)
            if not enabled:
                fill.setAlpha(120)

            painter.setPen(outline)
            painter.setBrush(QtGui.QBrush(fill))
            painter.drawRoundedRect(side_rect, 4, 4)
            if active:      # 脉冲期间再描一圈，强化「点到了」
                pen = self._flash_pen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen),
                                      highlight)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(side_rect, 4, 4)

            # 边里画三条短线，表示「这里是一排标签页」
            if active or hovered:
                painter.setPen(QtGui.QPen(hl_text if active else muted, 1.6))
                self._paint_tabs(painter, side, side_rect)

        # ---- 中央文字 ----
        painter.setFont(self.font())
        painter.setPen(QtGui.QPen(muted))
        label = self._side if self._side is not None else '未设置'
        painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, label)

        # ---- 聚焦框 ----
        if self.hasFocus():
            painter.setPen(QtGui.QPen(highlight, 1, QtCore.Qt.PenStyle.DashLine))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 8, 8)

        painter.end()

    @staticmethod
    def _paint_tabs(painter, side, rect):
        """在某条边里画三条等距短线，表示「这里是一排标签页」。"""
        count = 3
        if side in ('North', 'South'):
            step = rect.width() / (count + 1)
            for i in range(count):
                x = rect.left() + step * (i + 1)
                painter.drawLine(
                    QtCore.QPointF(x - 5, rect.center().y()),
                    QtCore.QPointF(x + 5, rect.center().y()))
        else:
            step = rect.height() / (count + 1)
            for i in range(count):
                y = rect.top() + step * (i + 1)
                painter.drawLine(
                    QtCore.QPointF(rect.center().x(), y - 5),
                    QtCore.QPointF(rect.center().x(), y + 5))


class _TabShapePicker(_AnimMixin, QtWidgets.QWidget, _BaseWidget):
    """标签形状示意图：并排画「圆角」与「三角」两个小标签，**点哪个选哪个**。

    ⚠️ 语义与枚举一致：写进文件的仍是 ``Rounded`` / ``Triangular``。
    默认值那一项会被点亮，所以「未设置」时也看得出实际生效的是圆角。

    ⚠️ 颜色只从 ``QPalette`` 取；形状用 ``QPainterPath`` 画。
    """

    changed = QtCore.pyqtSignal()

    WIDTH = 224
    HEIGHT = 70
    TAB_WIDTH = 90
    TAB_HEIGHT = 48
    SPACING = 12
    #: 允许被压缩到的最小宽度（理由同 :attr:`_BorderPicker.MIN_WIDTH`）。
    MIN_WIDTH = 150

    SHAPES = ('Rounded', 'Triangular')

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self._init_anim()
        self._shape = None
        self._hover = None
        self.setMinimumSize(self.MIN_WIDTH, self.HEIGHT)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._load(animated=False)

    # ---------------------------------------------------------------- 取值
    def _load(self, animated=True):
        value = self._effective_text()
        if value is not None and value in self.SHAPES:
            shape = value
        elif value is None:
            shape = self.default if self.default in self.SHAPES else None
        else:
            shape = None
        self._shape = shape
        self._animate_progress(1.0 if shape is not None else 0.0, animated)
        self._sync_tooltip()
        self.changed.emit()

    def is_modified(self):
        """是否显式存过一个与默认值不同的形状。"""
        stored = (self._stored_text() or '').strip()
        if len(stored) == 0:
            return False
        return stored != str(self.default if self.default is not None else '')

    def current_shape(self):
        """当前点亮的形状（``None`` = 不写入）。"""
        return self._shape

    def set_shape(self, shape, save=True):
        """点亮某个形状（``None`` = 取消选择 = 不写入）。"""
        shape = shape if shape in self.SHAPES else None
        if shape == self._shape:
            return
        self._shape = shape
        self._animate_progress(1.0 if shape is not None else 0.0)
        self._pulse()
        self._sync_tooltip()
        if save:
            if shape is None:
                self._remove()
            else:
                app_data.setenv(key=self.key, value=shape, encoding='utf-8')
        self.changed.emit()

    def _sync_tooltip(self):
        """tooltip 说明当前选择。"""
        if self.is_overridden():
            return
        text = self._shape if self._shape is not None else '未设置（使用程序默认值）'
        self.setToolTip(f'{self.key} = {text}\n点击小标签来选择')

    # ---------------------------------------------------------------- 几何
    def _tab_rects(self):
        """两个小标签的矩形（水平居中）。

        ⚠️ 宽度按文字的**实际长度比例**分配，而不是简单对半分：``Rounded`` 比
        ``Triangular`` 短一截，对半分会把右边的文字挤成省略号（实测窄窗口下
        ``Triangular`` 显示成 ``Triangu…``）。按比例分让两个名字都尽量完整。
        """
        spacing = self.SPACING
        total = max(self.width() - 8.0, 40.0)
        metrics = self.fontMetrics()
        widths = {s: max(metrics.horizontalAdvance(s)
                         + (28.0 if s == 'Triangular' else 20.0), 36.0)
                  for s in self.SHAPES}
        # ⚠️ 控件至少要有「两个标签名字都放得下」的宽度，否则文字只能显示成
        #    省略号（实测窗口压到 480px 时就这样）。``_field_size`` 给的是同一个
        #    数，这里再兜底一次，免得某处把它算小了。
        need = sum(widths.values()) + spacing
        if self.width() < need:
            widths = {s: max(w * (self.width() - spacing)
                             / max(sum(widths.values()), 1.0), 36.0)
                      for s, w in widths.items()}
        needed = sum(widths.values()) + spacing
        if needed > total:      # 空间不够 → 按比例压缩
            scale = (total - spacing) / max(sum(widths.values()), 1.0)
            widths = {s: max(w * scale, 24.0) for s, w in widths.items()}
        used = sum(widths.values()) + spacing
        left = (self.width() - used) / 2.0
        top = (self.height() - self.TAB_HEIGHT) / 2.0
        rects = {}
        x = left
        for shape in self.SHAPES:
            rects[shape] = QtCore.QRectF(x, top, widths[shape],
                                         self.TAB_HEIGHT)
            x += widths[shape] + spacing
        return rects

    def _shape_at(self, pos):
        """坐标 ``pos`` 落在哪个形状上；没有则返回 None。"""
        point = QtCore.QPointF(pos)
        for shape, rect in self._tab_rects().items():
            if rect.contains(point):
                return shape
        return None

    # ---------------------------------------------------------------- 交互
    def mousePressEvent(self, event):
        """点击某个小标签即选中它。"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.isEnabled():
            shape = self._shape_at(event.position())
            if shape is not None:
                self.set_shape(shape)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """记录悬停的形状。"""
        shape = self._shape_at(event.position())
        if shape != self._hover:
            self._hover = shape
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清掉悬停。"""
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        """左右方向键切换。"""
        if event.key() == QtCore.Qt.Key.Key_Left:
            self.set_shape('Rounded')
            event.accept()
            return
        if event.key() == QtCore.Qt.Key.Key_Right:
            self.set_shape('Triangular')
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------------------------------------------------------------- 绘制
    def paintEvent(self, event):
        """画两个形状标签，选中的那个填强调色。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        hl_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        background = base if base.lightness() >= window.lightness() else window
        muted = _blend(text, background, MUTED_RATIO)
        outline = _blend(background, text, 0.20)

        for shape, rect in self._tab_rects().items():
            active = shape == self._shape
            hovered = shape == self._hover
            if active:
                fill = QtGui.QColor(highlight)
            elif hovered:
                fill = _blend(background, highlight, 0.22)
            else:
                fill = _blend(background, text, 0.07)
            if not self.isEnabled():
                fill.setAlpha(120)

            painter.setPen(outline)
            painter.setBrush(QtGui.QBrush(fill))
            painter.drawPath(self._shape_path(shape, rect))
            if active:
                pen = self._flash_pen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen),
                                      highlight)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawPath(self._shape_path(shape, rect))

            painter.setPen(QtGui.QPen(hl_text if active else muted))
            # ⚠️ 文字要收在形状**里面**：三角形上沿是切过角的，两端各多让开一点，
            #    否则文字贴着斜边、看着像溢出（实测 "Triangular" 顶到了边）。
            #    空间实在不够时再退化成省略号。
            inset = 14 if shape == 'Triangular' else 8
            elided = painter.fontMetrics().elidedText(
                shape, QtCore.Qt.TextElideMode.ElideRight,
                max(int(rect.width()) - inset * 2, 1))
            painter.drawText(rect.adjusted(inset, 0, -inset, 0),
                             QtCore.Qt.AlignmentFlag.AlignCenter, elided)

        painter.end()

    @staticmethod
    def _shape_path(shape, rect):
        """构造形状路径：圆角矩形，或上沿切角的梯形。"""
        path = QtGui.QPainterPath()
        if shape == 'Rounded':
            path.addRoundedRect(rect, 10, 10)
            return path
        cut = rect.width() * 0.18
        path.moveTo(rect.left() + cut, rect.top())
        path.lineTo(rect.right() - cut, rect.top())
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        return path


class _PresetNumber(_AnimMixin, QtWidgets.QWidget, _BaseWidget):
    """「预设档位 + 自定义输入」的数字选择器（DPI 等）。

    左边一排档位按钮（:data:`KEY_PRESETS`），右边一个数字框。点档位即选中该值；
    数字框里填了别的值，所有档位都不高亮 —— 一眼看出「现在用的是非标准值」。

    ⚠️ 语义与 ``kind='int'`` 完全一致：写进文件的仍是一个十进制整数。档位只是
    快捷入口，不改变存什么。

    ⚠️ ``min`` / ``max`` 必须与读取方真正校验的区间一致（``plt_export_dpi``
    校验 50~3000）；越界值会被 ``QSpinBox`` 截断，用户看到的数就不是他填的数。

    ⚠️ 颜色只从 ``QPalette`` 取。
    """

    changed = QtCore.pyqtSignal()

    WIDTH = 320
    HEIGHT = 30
    PRESET_WIDTH = 52
    SPACING = 6
    #: 允许被压缩到的最小宽度 = 数字框宽 + 一个档位。
    #:
    #: ⚠️ 不能把最小值设成 ``WIDTH``（4 个档位全摊开的宽度）：那样这一行会把
    #: 整块界面的最小宽度顶到 648px（实测），窗口一窄就撑不开、只能出横向滚动条。
    #: 放不下的档位由 :meth:`_preset_rects` 自动少画几个，功能不受影响。
    MIN_WIDTH = 170

    def __init__(self, item, parent=None, presets=None):
        super().__init__(parent)
        self._init_item(item)
        self._init_anim()
        self._hover = -1
        self.setMinimumSize(self.MIN_WIDTH, self.HEIGHT)

        self._min = int(item.get('min', 1))
        self._max = int(item.get('max', 1000000))
        try:
            self._default_int = int(item.get('default', self._min))
        except (TypeError, ValueError):
            self._default_int = self._min

        self._presets = []
        for value in (presets or ()):
            try:
                value = int(value)
            except (TypeError, ValueError):
                continue
            if self._min <= value <= self._max:
                self._presets.append(value)

        self._spin = QtWidgets.QSpinBox(self)
        self._spin.setRange(self._min, self._max)
        self._spin.setSingleStep(10)
        self._spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        suffix = item.get('suffix')
        if suffix:
            self._spin.setSuffix(str(suffix))
        elif item.get('key') == 'plt_export_dpi':
            self._spin.setSuffix(' dpi')
        self._spin.valueChanged.connect(self._on_spin_changed)

        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._load(animated=False)

    # ---------------------------------------------------------------- 几何
    def _spin_width(self):
        """数字框的宽度。"""
        metrics = self.fontMetrics()
        return max(100.0, metrics.horizontalAdvance('000000 dpi') + 38.0)

    def _preset_rects(self):
        """档位按钮矩形列表（自左向右；放不下的不返回）。"""
        spin_width = self._spin_width()
        available = self.width() - spin_width - self.SPACING
        count = 0
        while count < len(self._presets):
            needed = (count + 1) * self.PRESET_WIDTH + count * self.SPACING
            if needed > available:
                break
            count += 1
        return [QtCore.QRectF(i * (self.PRESET_WIDTH + self.SPACING), 0.0,
                             self.PRESET_WIDTH, float(self.height()))
                for i in range(count)]

    def resizeEvent(self, event):
        """把数字框摆到最右边。"""
        super().resizeEvent(event)
        width = self._spin_width()
        self._spin.setGeometry(int(self.width() - width), 0, int(width),
                               self.height())

    def _preset_at(self, pos):
        """坐标 ``pos`` 落在第几个档位上；没有则返回 -1。"""
        point = QtCore.QPointF(pos)
        for i, rect in enumerate(self._preset_rects()):
            if rect.contains(point):
                return i
        return -1

    # ---------------------------------------------------------------- 取值
    def _load(self, animated=True):
        value = self._effective_text()
        try:
            number = int(value) if value is not None else self._default_int
        except (TypeError, ValueError):
            number = self._default_int
        number = min(max(number, self._min), self._max)
        self._spin.blockSignals(True)
        self._spin.setValue(number)
        self._spin.blockSignals(False)
        self._animate_progress(1.0, animated)
        self._sync_tooltip()
        self.changed.emit()

    def is_modified(self):
        """是否显式存过一个与默认值不同的数值。"""
        stored = self._stored_text()
        if stored is None:
            return False
        try:
            return int(stored) != self._default_int
        except (TypeError, ValueError):
            return True

    def value(self):
        """当前数值。"""
        return self._spin.value()

    def set_value(self, value, save=True):
        """设置数值（``save=False`` 时只改界面、不落盘）。"""
        value = int(min(max(int(value), self._min), self._max))
        self._spin.blockSignals(True)
        self._spin.setValue(value)
        self._spin.blockSignals(False)
        if save:
            app_data.setenv(key=self.key, value=str(value), encoding='utf-8')
            self._pulse()
        self._sync_tooltip()
        self.changed.emit()

    def _on_spin_changed(self, value):
        """数字框被用户改动。"""
        app_data.setenv(key=self.key, value=str(value), encoding='utf-8')
        self._pulse()
        self._sync_tooltip()
        self.changed.emit()

    def _sync_tooltip(self):
        """tooltip 说明取值范围与是否为预设档位。"""
        if self.is_overridden():
            return
        self.setToolTip(
            f'{self.key} = {self._spin.value()}'
            f'（默认 {self._default_int}，范围 {self._min}~{self._max}）\n'
            f'点击左侧档位快速选择，或在右侧直接输入')

    # ---------------------------------------------------------------- 交互
    def mousePressEvent(self, event):
        """点击档位即选中该值。"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.isEnabled():
            index = self._preset_at(event.position())
            if 0 <= index < len(self._presets):
                self.set_value(self._presets[index])
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """记录悬停的档位。"""
        index = self._preset_at(event.position())
        if index != self._hover:
            self._hover = index
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清掉悬停。"""
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    # ---------------------------------------------------------------- 绘制
    def paintEvent(self, event):
        """画档位按钮（选中的那个填强调色）。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        hl_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        background = base if base.lightness() >= window.lightness() else window
        muted = _blend(text, background, MUTED_RATIO)
        outline = _blend(background, text, 0.20)

        current = self._spin.value()
        for index, rect in enumerate(self._preset_rects()):
            if index >= len(self._presets):
                break
            value = self._presets[index]
            active = value == current
            hovered = index == self._hover
            if active:
                fill = QtGui.QColor(highlight)
            elif hovered:
                fill = _blend(background, highlight, 0.22)
            else:
                fill = _blend(background, text, 0.07)
            if not self.isEnabled():
                fill.setAlpha(120)

            painter.setPen(outline)
            painter.setBrush(QtGui.QBrush(fill))
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)
            if active:
                pen = self._flash_pen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen),
                                      highlight)
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)

            painter.setPen(QtGui.QPen(hl_text if active else muted))
            painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter,
                             str(value))

        painter.end()


class _Switch(QtWidgets.QWidget, _BaseWidget):
    """布尔开关（自绘的滑动开关，**不使用样式表**）。

    ⚠️ 状态 **直接映射「代码里真正采用的布尔值」**：开 = 该功能开启。
    持久化文件里仍写 ``Yes`` / ``No``（程序其它地方就是这么读的）：

    - 显式存了 ``Yes`` → 开；
    - 显式存了 ``No``  → 关；
    - 未设置 / 其它值  → 跟随 ``default``（条目里写的代码真实默认值）。

    这样「从未设置过」的键也会显示出它**实际生效**的状态。

    ⚠️ 颜色**全部从 ``QPalette`` 取**（``Highlight`` / ``Button`` / ``Base`` /
    ``Text``），不写任何色值，因此亮色 / 暗色主题都自动跟随，也不会被用户的
    ``zml_window_style.qss`` 盖掉。切换时用 ``QVariantAnimation`` 做一次平滑滑动。
    """

    changed = QtCore.pyqtSignal()

    #: 轨道尺寸（像素）。
    WIDTH = 46
    HEIGHT = 24
    #: 圆点的内边距 —— 决定滑块直径与「关」时圆点的位置。
    PADDING = 3

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self._default_bool = bool(item.get('default', False))
        self._checked = False
        self._position = 0.0          # 0.0 = 关，1.0 = 开（动画中间值）
        self._anim = QtCore.QVariantAnimation(self)
        self._anim.setDuration(130)
        self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._load()

    # ---------------------------------------------------------------- 取值
    def _load(self):
        value = (self._effective_text() or '').strip().lower()
        if value in ('yes', 'true', '1'):
            checked = True
        elif value in ('no', 'false', '0'):
            checked = False
        else:
            checked = self._default_bool  # 未设置 → 用代码真实默认值
        self._checked = checked
        self._position = 1.0 if checked else 0.0
        self._sync_tooltip()
        self.update()
        self.changed.emit()

    def is_modified(self):
        """是否显式存过一个非默认的状态。"""
        stored = self._stored_text()
        if stored is None:
            return False
        stored = stored.strip().lower()
        if stored in ('yes', 'true', '1'):
            return not self._default_bool
        if stored in ('no', 'false', '0'):
            return bool(self._default_bool)
        return False

    def setChecked(self, checked, animated=True):
        """设置开关状态（**不写文件**，供测试与程序内使用）。"""
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        self._sync_tooltip()
        if animated:
            self._anim.stop()
            self._anim.setStartValue(self._position)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
        else:
            self._position = 1.0 if checked else 0.0
            self.update()
        self.changed.emit()

    def isChecked(self):
        """当前是否为「开」。"""
        return self._checked

    def toggle(self):
        """翻转开关并落盘（用户交互用）。"""
        self.setChecked(not self._checked)
        app_data.setenv(
            key=self.key, value='Yes' if self._checked else 'No',
            encoding='utf-8')
        self.changed.emit()

    def _on_anim(self, value):
        try:
            self._position = float(value)
        except (TypeError, ValueError):
            self._position = 1.0 if self._checked else 0.0
        self.update()

    def _sync_tooltip(self):
        """tooltip 永远显示「当前落盘会是什么」，避免用户猜。"""
        if self.is_overridden():
            return  # 已被系统环境变量覆盖时保留覆盖说明
        self.setToolTip(
            f'{self.key} = {"Yes" if self._checked else "No"}'
            f'（默认 {"Yes" if self._default_bool else "No"}）\n点击切换')

    # ---------------------------------------------------------------- 交互
    def mousePressEvent(self, event):
        """鼠标点击切换。"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.isEnabled():
            self.toggle()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """空格 / 回车也能切换（键盘可达性）。"""
        if event.key() in (QtCore.Qt.Key.Key_Space, QtCore.Qt.Key.Key_Return,
                           QtCore.Qt.Key.Key_Enter):
            self.toggle()
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------------------------------------------------------------- 绘制
    def paintEvent(self, event):
        """自绘轨道 + 圆点，颜色全部来自调色板。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        text = palette.color(QtGui.QPalette.ColorRole.Text)
        button = palette.color(QtGui.QPalette.ColorRole.Button)
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        enabled = self.isEnabled()

        # 轨道：关 = 与底色相近的「凹陷」色；开 = 强调色
        off_track = _blend(button, base, 0.5)
        on_track = QtGui.QColor(highlight)
        if not enabled:
            off_track.setAlpha(140)
            on_track.setAlpha(140)

        track = _blend(off_track, on_track, self._position)
        rect = QtCore.QRectF(0.5, 0.5, self.WIDTH - 1.0, self.HEIGHT - 1.0)
        radius = rect.height() / 2.0

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(track))
        painter.drawRoundedRect(rect, radius, radius)

        # 圆点：白色 + 一点描边，深色主题下也不会糊进轨道
        diameter = self.HEIGHT - 2.0 * self.PADDING
        x0 = self.PADDING
        x1 = self.WIDTH - self.PADDING - diameter
        left = x0 + (x1 - x0) * self._position
        dot = QtCore.QRectF(left, self.PADDING, diameter, diameter)

        knob = QtGui.QColor('#ffffff')
        if not enabled:
            knob.setAlpha(200)
        painter.setPen(QtGui.QPen(_blend(off_track, text, 0.18), 1))
        painter.setBrush(QtGui.QBrush(knob))
        painter.drawEllipse(dot)

        # 聚焦框：键盘 Tab 过来时给个可见提示
        if self.hasFocus():
            painter.setPen(QtGui.QPen(highlight, 1, QtCore.Qt.PenStyle.DotLine))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2),
                                    radius + 2, radius + 2)

        painter.end()


class _Segmented(QtWidgets.QWidget, _BaseWidget):
    """枚举选项的**分段选择器**（自绘，**不使用样式表**）。

    这是把普通 ``QComboBox`` 换成更好看的控件的尝试：选项都摊开显示，
    当前值所在的那一段被一块圆角滑块高亮 —— 一目了然地看出「现在选的是哪个」，
    也省掉了「点开下拉框才知道有哪些选项」这一步。

    ⚠️ 语义与原来的下拉框**完全一致**：

    - 第一段固定是「默认」，代表「不写入该项」（选中它时删除持久化文件）；
    - 若持久化文件里存过这个键，界面就停在「默认」那一段；
    - 从没设置过（或已被还原）时，高亮真正生效的那一段（如 ``North``）。

    ⚠️ 选项多（超过 :attr:`MAX_SEGMENTS` 段）或文字太长时，分段选择器会挤成一团
    看不清 —— 这时**自动退化成普通下拉框**（标签里仍显示「默认（xxx）」）。
    当前数据里最多 6 个选项，短名可以容纳；`console_priority` 的名字较长，
    也会走退化路径。判断只在构造时做一次。
    """

    changed = QtCore.pyqtSignal()

    #: 最多几段时才用分段选择器（再多就换回下拉框）。
    MAX_SEGMENTS = 4

    #: 分段选择器的宽度（比基础控件宽：要把每一段的文字摊开写清楚）。
    WIDTH = 320
    RADIUS = 7

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._init_item(item)
        self._items = [str(x) for x in (item.get('items') or []) if str(x)]
        self._default_text = (
            f'默认（{self.default}）' if self.default is not None else '默认')
        self._labels = [self._default_text] + self._items
        self._hover = -1
        self._use_segments = self._can_use_segments()

        # 退化路径：普通下拉框（放同一个框里，隐藏分段选择器）
        self._combo = QtWidgets.QComboBox(self)
        self._combo.addItems(self._labels)
        self._combo.setMinimumContentsLength(10)
        self._combo.currentIndexChanged.connect(self._on_combo_changed)

        if self._use_segments:
            self._combo.setVisible(False)
            self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.setMouseTracking(True)
        else:
            self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._load()

    # ---------------------------------------------------------------- 版式
    def _can_use_segments(self):
        """判断是否值得用分段选择器（段数与文字宽度都要合适）。

        ⚠️ **在构造期判定**，此时控件还没被布局过、字体度量是「默认字体」的：
        早先的实现按 ``widest * 段数 + 24 * 段数`` 估算总宽，遇到
        ``默认（LowPriority）`` 这种首项就把 2 段的短列表也判成放不下，结果两个
        本来很适合分段的枚举全退化成下拉框。现在改成**只看平均每段要多少宽**，
        阈值留足余量；真正的溢出由 ``_Segmented`` 的省略号兜底。
        """
        if len(self._labels) > self.MAX_SEGMENTS:
            return False
        metrics = self.fontMetrics()
        widest = max(metrics.horizontalAdvance(text) for text in self._labels)
        # 平均分到每段的可用宽度够放下最长文字 + 内边距即可
        per_segment = float(self.WIDTH) / float(len(self._labels))
        return widest + 16 <= per_segment

    def resizeEvent(self, event):
        """让退化路径的下拉框铺满整个控件区。"""
        super().resizeEvent(event)
        if hasattr(self, '_combo'):
            self._combo.setGeometry(0, 0, self.width(), self.height())

    def sizeHint(self):
        """声明需要的宽度。

        ⚠️ 必须给：``QWidget`` 默认的 ``sizeHint`` 是 0×0，而父布局用
        ``AlignRight`` 摆放、**不会拉伸**子控件，于是控件宽度会真的变成 0 ——
        实测就是这样：``_Segmented`` 的 geometry 宽度为 0，整条枚举在界面上
        完全看不见（画布宽 0，什么都画不出来）。
        """
        return QtCore.QSize(self.WIDTH, self.height() or 30)

    def minimumSizeHint(self):
        """最小宽度：退化成下拉框时也要放得下文字。"""
        return QtCore.QSize(self.WIDTH, 26)

    # ---------------------------------------------------------------- 取值
    def _load(self):
        value = self._effective_text()
        index = -1
        if value is not None:
            index = self._index_of(value)
            if index < 0:
                # 存了一个不在列表里的值：显示「默认」，但把原值留在 tooltip
                self.setToolTip(
                    f'已保存的取值 <{value}> 不在可选项中，界面按默认值显示。')
                index = 0
        elif self.default is not None:
            # 从没设置过：高亮真正生效的那一项（和开关按 default 打开同理）
            index = self._index_of(str(self.default))
        self._index = max(index, 0)
        self._combo.blockSignals(True)
        self._combo.setCurrentIndex(self._index)
        self._combo.blockSignals(False)
        self.update()
        self.changed.emit()

    def _index_of(self, text):
        """在标签列表里找 ``text`` 的下标；找不到返回 -1。"""
        for i, label in enumerate(self._labels):
            if label == text:
                return i
        return -1

    def currentIndex(self):
        """当前选中的段。"""
        return self._index

    def currentText(self):
        """当前选中的段文字。"""
        return self._labels[self._index]

    def set_index(self, index, animated=False):
        """设置选中段（**会落盘**，与用户点击同一条路径）。"""
        index = int(index)
        if index < 0 or index >= len(self._labels):
            return
        self._index = index
        self._combo.blockSignals(True)
        self._combo.setCurrentIndex(index)
        self._combo.blockSignals(False)
        self.update()
        self._save_index(index)
        self.changed.emit()

    def _on_combo_changed(self, index):
        """退化路径下，下拉框的值变了。"""
        self._index = index
        self._save_index(index)
        self.changed.emit()

    def _save_index(self, index):
        """把选中的段写进持久化文件（第 0 段 = 删除文件）。"""
        if index <= 0:  # 「默认」= 不写入
            self._remove()
        else:
            app_data.setenv(
                key=self.key, value=self._labels[index], encoding='utf-8')

    def is_modified(self):
        """是否显式存过一个非默认的取值。"""
        stored = self._stored_text()
        if stored is None:
            return False
        return stored != str(self.default if self.default is not None else '')

    # ---------------------------------------------------------------- 交互
    def _segment_rects(self):
        """算出每一段的矩形（等宽）。"""
        width = self.width() / float(max(len(self._labels), 1))
        return [QtCore.QRectF(i * width, 0.0, width, self.height())
                for i in range(len(self._labels))]

    def _segment_at(self, pos):
        """返回坐标 ``pos`` 落在第几段；不在任何一段时返回 -1。"""
        rects = self._segment_rects()
        for i, rect in enumerate(rects):
            if rect.contains(QtCore.QPointF(pos)):
                return i
        return -1

    def mousePressEvent(self, event):
        """点击某一段即选中它。"""
        if not self._use_segments:
            super().mousePressEvent(event)
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.isEnabled():
            index = self._segment_at(event.position())
            if index >= 0:
                self.set_index(index)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """记录悬停段，用于画高亮。"""
        if self._use_segments:
            index = self._segment_at(event.position())
            if index != self._hover:
                self._hover = index
                self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清掉悬停段。"""
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        """左右方向键切换（键盘可达性）。"""
        if not self._use_segments:
            super().keyPressEvent(event)
            return
        if event.key() == QtCore.Qt.Key.Key_Left:
            self.set_index(max(self._index - 1, 0))
            event.accept()
            return
        if event.key() == QtCore.Qt.Key.Key_Right:
            self.set_index(min(self._index + 1, len(self._labels) - 1))
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------------------------------------------------------------- 绘制
    def paintEvent(self, event):
        """自绘分段：底槽 + 滑块 + 文字。"""
        if not self._use_segments:
            return  # 退化路径由 QComboBox 自己画

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        hl_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        background = base if base.lightness() >= window.lightness() else window
        muted = _blend(text, background, MUTED_RATIO)

        # 底槽：比背景略「凹」的圆角矩形
        slot = QtCore.QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.setPen(QtGui.QPen(_blend(background, text, 0.12), 1))
        painter.setBrush(QtGui.QBrush(_blend(background, text, 0.06)))
        painter.drawRoundedRect(slot, self.RADIUS, self.RADIUS)

        # 滑块（当前段）
        rects = self._segment_rects()
        if 0 <= self._index < len(rects):
            knob = rects[self._index].adjusted(2, 2, -2, -2)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QBrush(highlight))
            painter.drawRoundedRect(knob, self.RADIUS - 2, self.RADIUS - 2)

        # 文字
        metrics = painter.fontMetrics()
        for i, rect in enumerate(rects):
            if i == self._index:
                painter.setPen(QtGui.QPen(hl_text))
                font = QtGui.QFont(painter.font())
                font.setWeight(QtGui.QFont.Weight.DemiBold)
                painter.setFont(font)
            else:
                painter.setPen(QtGui.QPen(
                    text if i == self._hover else muted))
                painter.setFont(self.font())
            elided = metrics.elidedText(
                self._labels[i], QtCore.Qt.TextElideMode.ElideRight,
                int(rect.width()) - 8)
            painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, elided)

        painter.end()


# ============================================================
# 装饰性控件（全部原生绘制，颜色取自调色板）
# ============================================================

class _Card(QtWidgets.QFrame):
    """圆角卡片容器。

    自身不画背景（``QFrame`` 默认透明），只提供统一的圆角与留白；
    视觉层次由外层布局的间距建立。⚠️ 不用样式表 —— 见模块文档。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)


class _GroupHeader(QtWidgets.QWidget):
    """分组标题：加粗组名 + 条目数 + 一条贯穿的细分隔线。"""

    HEIGHT = 34

    def __init__(self, title, count, parent=None):
        super().__init__(parent)
        self._title = str(title)
        self._count = int(count)
        self.setFixedHeight(self.HEIGHT)
        font = self.font()
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        self.setFont(font)

    def paintEvent(self, event):
        """画组名、条目数与右侧分隔线。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)
        background = base if base.lightness() >= window.lightness() else window

        metrics = painter.fontMetrics()
        x = float(GAP)
        y = (self.height() + metrics.ascent() - metrics.descent()) / 2.0

        # 组名前的一小段强调色竖条
        bar = QtCore.QRectF(x, y - metrics.ascent(),
                            3.0, metrics.ascent() + metrics.descent())
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.drawRoundedRect(bar, 1.5, 1.5)

        x += 10.0
        painter.setPen(QtGui.QPen(text))
        painter.drawText(QtCore.QPointF(x, y), self._title)
        x += metrics.horizontalAdvance(self._title) + 8.0

        # 条目数用次要色
        count_text = f'{self._count} 项'
        painter.setPen(QtGui.QPen(_blend(text, background, MUTED_RATIO)))
        font = QtGui.QFont(painter.font())
        font.setWeight(QtGui.QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(QtCore.QPointF(x, y), count_text)
        x += painter.fontMetrics().horizontalAdvance(count_text) + 12.0

        # 贯穿到右边的细线
        if x < self.width() - GAP:
            mid = self.height() / 2.0
            painter.setPen(QtGui.QPen(_blend(background, text, 0.12), 1))
            painter.drawLine(QtCore.QPointF(x, mid),
                             QtCore.QPointF(self.width() - GAP, mid))
        painter.end()


class _ConfigRow(QtWidgets.QWidget):
    """一行配置：左侧一条「是否已修改」的色条 + 子控件。

    ⚠️ 色条是**画**出来的，且只在「与默认值不同」时出现（颜色取 ``Highlight``）。
    它比一行文字提示更省空间 —— 一眼扫过去就知道哪几项被改过。

    ⚠️ 本类还负责**按可用宽度自适应**（见 :meth:`_apply_responsive`）：窗口或
    标签页窄到放不下说明文字时，把说明整条藏起来、只留标题与控件。硬挤着显示
    被压成三四个字一行的说明，比不显示更难读。
    """

    #: 说明文字**最多允许排几行**；超过就整条藏掉。
    #:
    #: ⚠️ **不能只按宽度判断**（早先的写法）：说明长短差别很大，同样 170px 宽，
    #: 短的排 3 行还算能读、长的（如 Qt版本那条 60 多字）要排 5 行就成了又窄又高的
    #: 一根竖条 —— 实测 560px 窗口下 ``plt_export_dpi`` 的说明是 166×76（5 行）。
    #: 现在改成按**「这个宽度下要排几行」**判断：超过两行就藏掉，短说明仍可保留。
    NOTE_MAX_LINES = 2

    #: 说明文字的宽度下限（像素）。再窄下去即使只有一两行也会挤成竖条。
    NOTE_MIN_WIDTH = 150

    def __init__(self, parent=None, kind='str', card=None):
        super().__init__(parent)
        self.key = ''
        self.widget = None
        self.item = None
        self.kind = kind
        self.card = card
        self.note_label = None
        self._text_host = None
        self._modified = False
        self._has_note = False
        self._in_responsive = False

    def set_text_host(self, widget):
        """登记「标题 + 说明」所在的文字栏（自适应按它的宽度判断）。

        ⚠️⚠️ **这里刻意不再 installEventFilter**（试过，把进程打崩）：在文字栏的
        ``Resize`` 事件里回调 ``_apply_responsive``，而后者会改 ``minimumWidth`` →
        再触发一次 Resize → 形成 **Qt 事件级的死循环**。这种循环发生在 C++ 事件
        分发内部，Python 的重入标志根本挡不住（标志在两次**独立**事件之间已经是
        False），表现为进程栈溢出崩溃、连 traceback 都没有。

        刷新时机统一交给 :meth:`EnvEdit._sync_responsive`（父级在窗口尺寸变化 /
        首次显示后主动分发），那里有 ``_in_sync`` 闸门，并且只在一个方向推进。
        """
        self._text_host = widget

    def set_modified(self, modified):
        """设置左侧色条是否显示。"""
        modified = bool(modified)
        if modified != self._modified:
            self._modified = modified
            self.update()

    def resizeEvent(self, event):
        """宽度变化时重新决定「说明要不要显示」。"""
        super().resizeEvent(event)
        self._apply_responsive()

    def _viewport_width(self):
        """返回整个编辑器的宽度（用户拖动窗口得到的那个尺寸）。

        ⚠️ **不能用行宽，也不能用滚动视口宽**（两处都实测踩过）：

        - 行宽：滚动区里行会被横向撑到「内容自然宽度」（实测 648px），窗口缩到
          520px 时行宽仍是 648 —— 判断永远「够宽」；
        - 视口宽：最小被卡在 538px（内容最小宽度 + 滚动条），窗口再小也不缩，
          于是可算出的可用宽度永远 ≥444px。

        只有**编辑器自身**的宽度真实反映用户给了多少地方。
        """
        parent = self.parentWidget()
        best = self.width()
        while parent is not None:
            if isinstance(parent, EnvEdit):
                return parent.width()
            parent = parent.parentWidget()
        return best

    def update_responsive(self):
        """公开入口：重新决定说明是否显示（由父控件在尺寸变化时调用）。"""
        self._apply_responsive()

    #: 文字栏（标题）至少要有这么宽，否则**宁可让整行横向溢出**（出滚动条），
    #: 也不把标题压成一条 1px 的竖线。
    #:
    #: ⚠️ 这是「把窗口拖到最窄」时那个经典毛病的正解：控件有固定的最小宽度
    #: （分段选择器 320px），窗口再窄时布局只能从文字栏扣，一路扣到 ``1px`` ——
    #: 标题于是变成又窄又高的一条，一个字都读不出来（实测 400px 窗口下
    #: ``Qt_version`` 的标题是 1×40、``console_priority`` 是 1×110）。
    #: 与其这样，不如让文字栏守住下限、让整行放不下（滚动条负责兜底）——
    #: 至少每一行都还读得懂。
    TEXT_MIN_WIDTH = 120

    def _apply_responsive(self):
        """按可用宽度决定：说明显示 / 隐藏。

        判据 = 编辑器宽度 − 控件区宽 − 边距，即「文字栏真正能拿到多少」；
        然后用这个宽度算出**这条说明要排几行**，超过 :attr:`NOTE_MAX_LINES`
        就藏掉。所以同样窗口下，短说明留着、长说明先藏。

        ⚠️⚠️ **本方法只允许「切换说明的可见性」这一种副作用**。早先的版本还会
        在这里调 ``setMinimumWidth`` / ``updateGeometry``，那会让布局在 Resize
        事件内部再排一次、再发一次 Resize —— 形成 **Qt 事件级死循环**（发生在
        C++ 事件分发里，Python 的重入标志挡不住），进程栈溢出崩溃、连 traceback
        都没有：实测窗口拖到 520px 必崩。文字栏的宽度下限改由构造期一次性设定
        （:attr:`TEXT_MIN_WIDTH`），运行期不再摇摆。
        """
        if self.note_label is None or self._in_responsive:
            return
        field_width = self.widget.width() if self.widget is not None else 0
        available = self._viewport_width() - field_width - GAP * 4
        show = False
        if available >= self.NOTE_MIN_WIDTH:
            show = self._note_lines(int(available)) <= self.NOTE_MAX_LINES
        # ⚠️ 判据必须看控件**真实**的可见状态，不能只看 ``_has_note`` 这个缓存位：
        #    它的初值是 False（= 还没显示过），若拿它跟 ``show=False`` 比，首次需要
        #    隐藏时会被判成「没变化」而**跳过 setVisible** —— 于是说明明明该藏却
        #    一直显示（实测 440px 下 Qt_version 的说明根本没藏掉）。
        if show == self.note_label.isVisible():
            self._has_note = show
            return
        self._has_note = show
        self._in_responsive = True
        try:
            self.note_label.setVisible(show)
        finally:
            self._in_responsive = False

    def _note_lines(self, width):
        """估算这条说明在 ``width`` 宽下要排几行。

        ⚠️⚠️ **不能拿 ``QLabel.heightForWidth`` 的返回值来判断**：那个调用会让 Qt
        走一遍排版，而排版会反过来问 ``sizeHint`` / ``heightForWidth`` —— 与本类
        的 ``eventFilter`` / ``_apply_responsive`` 构成环，实测直接把进程打崩
        （栈溢出，连 traceback 都没有）。

        这里改成**纯字体度量**的估算：按自动换行的断点规则累加词宽，够不够宽就
        换行。不碰任何 Qt 布局 API，因此不可能递归。估算偏保守（中英文混排的
        词边界只按空格和标点切），但这只影响"要不要藏"的判断，不影响排版本身。
        """
        text = self.note_label.text() if self.note_label is not None else ''
        if not text:
            return 1
        metrics = self.note_label.fontMetrics()
        limit = max(int(width), 1)
        lines = 1
        current = 0
        for token in self._tokens(text):
            token_width = metrics.horizontalAdvance(token)
            if current + token_width <= limit:
                current += token_width
                continue
            if current > 0:      # 当前行放不下 → 换行
                lines += 1
                current = 0
            # 单个 token 本身就超宽（超长英文单词）→ 按字符折
            if token_width > limit:
                lines += token_width // limit
                current = token_width % limit
            else:
                current = token_width
        return lines

    @staticmethod
    def _tokens(text):
        """把说明切成「可换行的最小单位」：中文按字、英文按词、标点各自成组。"""
        buffer = ''
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff' or ch in '，。、；：！？（）《》':
                if buffer:
                    yield buffer
                    buffer = ''
                yield ch
            elif ch == ' ':
                if buffer:
                    yield buffer
                    buffer = ''
                yield ' '
            else:
                buffer += ch
        if buffer:
            yield buffer

    def paintEvent(self, event):
        """画左侧色条（未修改时不画任何东西）。"""
        super().paintEvent(event)
        if not self._modified:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        color = self.palette().color(QtGui.QPalette.ColorRole.Highlight)
        height = min(ACCENT_HEIGHT, self.height() - 6)
        if height > 0:
            top = (self.height() - height) / 2.0
            rect = QtCore.QRectF(0.0, top, ACCENT_WIDTH, height)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawRoundedRect(rect, ACCENT_WIDTH / 2.0, ACCENT_WIDTH / 2.0)
        painter.end()


class _StatusStrip(QtWidgets.QWidget):
    """顶部状态条：把「有多少项被改过 / 被覆盖」画成一句话。

    背景是一块很淡的圆角矩形（从 ``Window`` 混向 ``Base``），文字用
    ``text`` 与背景混合得到的次要色 —— 强调而不刺眼。被修改 / 被覆盖时
    这句会换成强调色，一眼能看出「有东西不一样了」。
    """

    RADIUS = 8
    PADDING_X = 14
    PADDING_Y = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._modified = 0
        self._overridden = 0
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Minimum)

    def set_state(self, total, modified, overridden):
        """更新统计数字并重绘。"""
        changed = (self._total, self._modified,
                   self._overridden) != (total, modified, overridden)
        self._total = int(total)
        self._modified = int(modified)
        self._overridden = int(overridden)
        if changed:
            self.updateGeometry()
            self.update()

    def _lines(self):
        """返回要绘制的 ``(文字, 是否强调)`` 列表。"""
        if self._modified > 0:
            head = (f'已修改 {self._modified} / {self._total} 项 —— '
                    f'左侧带色条的就是改过的项', True)
        else:
            head = (f'全部 {self._total} 项均为默认值', False)
        lines = [head]
        if self._overridden > 0:
            lines.append(
                (f'{self._overridden} 项已被系统环境变量覆盖，'
                 f'界面上置灰、改了不生效', True))
        else:
            lines.append(('改动立即保存，重启程序后生效', False))
        return lines

    def paintEvent(self, event):
        """画圆角底 + 若干行文字。"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)

        background = _blend(window, base, 0.55)
        rect = QtCore.QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.setPen(QtGui.QPen(_blend(background, text, 0.12), 1))
        painter.setBrush(QtGui.QBrush(background))
        painter.drawRoundedRect(rect, self.RADIUS, self.RADIUS)

        muted = _blend(text, background, MUTED_RATIO)
        metrics = self.fontMetrics()
        x = float(self.PADDING_X)
        y = float(self.PADDING_Y + metrics.ascent())
        for line, emphasized in self._lines():
            # 强调行前面点一个小圆点，语义比纯文字更强
            if emphasized:
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QBrush(highlight))
                dot_y = y - metrics.ascent() / 2.0
                painter.drawEllipse(QtCore.QPointF(x + 3.0, dot_y), 3.0, 3.0)
            painter.setPen(QtGui.QPen(highlight if emphasized else muted))
            painter.drawText(QtCore.QPointF(x + 12.0, y), line)
            y += metrics.height() + 2.0
        painter.end()

    def sizeHint(self):
        """按行数算出高度。"""
        metrics = self.fontMetrics()
        return QtCore.QSize(
            320, self.PADDING_Y * 2 + len(self._lines()) * (metrics.height() + 2))

    def minimumSizeHint(self):
        """与 :meth:`sizeHint` 相同（内容固定）。"""
        return self.sizeHint()


# ============================================================
# 测试
# ============================================================

def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = EnvEdit(items=settings.get_env_items())
    w.resize(880, 720)
    w.show()
    sys.exit(app.exec())


# ============================================================
# 入口：菜单「设置 → 系统」与命令 gui.show_env_edit
# ============================================================

def show_env_edit():
    """打开（或切到）「系统设置」标签页；同时也是 GUI 命令 ``gui.show_env_edit()``.

    ⚠️ 由 ``MainWindow.show_env_edit`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_env_edit', show_env_edit)`` **显式补上**。

    ⚠️ **每一项都按「代码里真正采用的默认值」初始化**（``items=settings.get_env_items()``
    交给控件）—— 这是 :class:`EnvEdit` 最重要的契约，详见模块文档第一段。

    ⚠️ 标签页按「控件类型 + 标题」复用：重复调用只会切到那一页。
    """
    def oper(w):
        w.gui_restore = """gui.show_env_edit()"""

    gui.get_widget(
        EnvEdit,
        caption="系统设置",
        on_top=True,
        icon="set",
        oper=oper,
        type_kw=dict(items=settings.get_env_items()),
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.show_env_edit`` + 菜单项「设置 → 系统」（``Ctrl+E``）.

    ⚠️ **菜单路径与图标 / 快捷键 / ``name`` 都与原来 ``main.py`` 里逐字一致**：
    ``menu="设置"`` 必须与 ``main.py`` 里那一处逐字相同，否则 ``get_menu`` 会另建一个
    同名顶层菜单，界面上出现两个「设置」；``name='env'`` / ``icon='set'`` / ``Ctrl+E``
    是 ribbon 配置、已保存界面布局与用户肌肉记忆的定位依据。
    """
    gui.add_func('show_env_edit', show_env_edit)

    gui.add_action(
        menu="设置",
        name="env",
        icon="set",
        text="系统",
        shortcut="Ctrl+E",
        slot=show_env_edit,
        overwrite=False,
    )


if __name__ == "__main__":
    test_1()

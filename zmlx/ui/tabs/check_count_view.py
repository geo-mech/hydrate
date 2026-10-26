"""许可查询次数统计控件（按天柱状图，数据来自 ``web_license.check_count``）.

界面
----

::

    （标签页标题已经是「授权记录」，控件内不再重复写标题与说明文字）

    ┌──────────────────────────────────────────────────────────────┐
    │ 正在查询...              ← 一句话横幅（成功时是区间摘要）       │
    └──────────────────────────────────────────────────────────────┘
    ────────────────────────────────────────────────────────────────
      邮箱 [you@example.com              ] [查询]
      区间 [2026-09-06] 至 [2026-10-05]  [最近7天][最近30天][最近60天]
      查询次数（2026-09-06 ~ 2026-10-05，共 30 天）         ← 柱状图
      （**不套组合框**：图自己已经有更准确的标题，外面再画一圈框是多余的）
    ▸ 服务器原始答复      ← QGroupBox，**默认收起**：原话 + 往返耗时
      （点标题展开；勾选框本身就是开关，不必自造按钮）

尺寸策略：够大就铺满，太小才缩图
--------------------------------

内容**直接铺在控件上，不套滚动区**，全屏只有一个弹性元素：

- **柱状图**（:class:`_BarChart`）是唯一的伸缩项（``stretch=1`` + ``Expanding``）；
- 其余各行（横幅 / 表单 / 原始答复）都是固定高度，**永不参与拉伸**。

数据从哪来
----------

:meth:`zmlx.exts.WebLicense.check_count` 返回的是**服务端原话**，成功时形如::

    Count: 3 0 5 1 ...  | Email: someone@example.com | Range: 2026-09-06 ~ 2026-10-05

★ **``Count:`` 后面那串数字的形状由服务端保证，本控件不重新解析它的语义**：
本控件只做一件事 —— 把 ``Range:`` 段拿来做横轴标签、把那串数字按顺序画成柱子。
**不自己算日期**：横轴的每一天都必须来自服务端。

判定纪律
--------

成功记号是 ``'Count:'``（前 6 个字符、带冒号），判定**只看开头**，绝不 ``==``
整串。⚠️ **绝不能拿判 ``user_list`` 的那段（``Users:``）来判本接口** —— 两者
都是 **6 个字符、都带冒号**，只差前面那个词，拿混了会把**成功读成失败**。

⚠️ **``Not permitted.`` 是 HTTP 200 的「正常业务答复」**，不是异常、也不是连接
失败 —— 原样显示给用户。它**同时代表**「你不是管理员」与「那个邮箱不存在」，
所以本控件**绝不**替服务端编一句「这个邮箱不存在」。

四种记号的辨别要点与权限模型见 ``zmlx/_private/AUTHORIZATION_NOTES.md`` §3 / §9。

耗时的活一律在线程里
--------------------

:meth:`zmlx.exts.WebLicense.check_count` 会阻塞，所以查询走 :class:`_Worker`
（QThread），期间按钮全部禁用；结果经信号回到主线程再画图。

⚠️ **本接口不做缓存**：它是用户的一次动作，缓存会让「刚查过的数字没变」与
「服务端没答理」看起来一模一样。

绘图为什么用原生 Qt（:class:`_BarChart`）
-----------------------------------------

本项目对「一排柱子」这种图**不用 matplotlib**：它内层画布的 ``sizeHint`` 改不动
（放进滚动区后滚动起点会顶到约 660 px），缩放时容易留白，配色与中文字体都各是
一套体系。:class:`_BarChart` 用 ``paintEvent`` 按当前尺寸直接画，配色取自
:meth:`QWidget.palette`（跟随主题 / 暗色模式），也没有额外依赖。

版式约定
--------

**不在控件里 ``setStyleSheet`` 写 ``color`` / ``background``**：本程序会加载
用户可编辑的 ``zml_window_style.qss``，并且有暗色模式，硬编码颜色要么在暗色下
看不清，要么把用户主题盖掉。需要「次要文字」就用 ``setEnabled(False)``，需要
边框就用 ``palette(mid)``（见 :data:`BANNER_QSS`）。

Added by DeepSeek, 2026-10-05
Modified by DeepSeek, 2026-10-10: 控件类 `LicenseCount` → `CheckCountView`，文件
`license_count.py` → `check_count_view.py`（旧名在 `license_count.py` 里留了转发层）。
"""

import datetime
import os
import time

from zmlx.exts import web_license
from zmlx.system import make_parent
from zmlx.ui.utils.lic_utils import (is_user_list, is_user_list_detail,
                                     merge_emails, parse_user_list,
                                     parse_user_list_detail,
                                     wrap_text_to_width)
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

#: 成功记号：前 6 个字符、忽略大小写、**带那个冒号**。
#:
#: ⚠️ 与 ``users:`` **刻意分开**（``user_list`` 的记号）—— 两者只差前面那个词，
#:    拿混了会把成功读成失败。判据见 :func:`parse_count_reply`。
COUNT_TAG = 'Count:'

DETAIL_SEP = ' | '

#: ``Range:`` 段的标签 —— 横轴标签的**唯一**来源（不要自己按个数反推日期）。
RANGE_TAG = 'Range:'

#: 默认查询的区间天数（点「最近 N 天」时用）。服务端在两个日期都留空时回
#: **最近 60 天（含今天）**，所以 60 这个值两边是一致的。
DEFAULT_DAYS = 30

#: 日期选择按钮的取值（天）。
DAY_CHOICES = (7, 30, 60)

#: 日期一律 ``YYYY-MM-DD``（10 个字符）—— 服务端**不收** 8 位紧凑写法。
DATE_FORMAT = '%Y-%m-%d'

#: 邮箱输入框的初始占位文本。
EMAIL_PLACEHOLDER = 'you@example.com'

#: 「服务器原始答复」框的固定高度：那里只有「原话 + 往返耗时」两行。
STATUS_VIEW_HEIGHT = 62

# ---------------------------------------------------------------------------
# 左侧邮箱列表
# ---------------------------------------------------------------------------

#: 左侧列表的固定宽度（像素）。
#:
#: ⚠️ 固定宽度而不是让它随内容伸缩：邮箱可能很长，放开会让左侧把右侧挤扁，
#: 而右侧（柱状图 + 表单）才是主要工作面。过长的邮箱由 ``QListWidget`` 自己
#: 出横向滚动条，完整内容也在悬停提示里。
LIST_WIDTH = 200

#: 左侧列表的最小高度（像素）——低于这个高度它自己出滚动条。
#: 它不参与纵向拉伸（拉伸全部留给柱状图，见 :meth:`CheckCountView._build_ui`）。
LIST_MIN_HEIGHT = 120

# ---------------------------------------------------------------------------
# 版式常量（与 license_register / feedback_tool 一致）
#
# ⚠️ 这里不写任何色值：见模块文档的「版式约定」。
# ---------------------------------------------------------------------------

MARGIN = 12
GAP = 8
BUTTON_HEIGHT = 34

#: 柱状图的最小高度（像素）。窗口被压矮时它**先缩**，缩到这里为止
#: —— 其余各行（横幅 / 表单 / 原始答复）始终完整显示。
#:
#: ⚠️ 这是柱状图**唯一**需要设的尺寸常量：它在布局里是唯一的弹性元素
#: （``Expanding`` + ``stretch=1``），窗口变高时自己会长。
#: **不要**再给它设 ``maximumHeight`` —— 那会把它钉死、上方留出一片空白。
CHART_MIN_HEIGHT = 160

#: 柱状图向布局提出的**偏好**高度（像素）。
#:
#: ⚠️ 与 matplotlib 方案最本质的差别就在这一条：这个值**真的管用**。
#: 布局空间不够时会把它压到 :data:`CHART_MIN_HEIGHT`，空间富余时它自己长满，
#: 两头都符合直觉（原生控件，见模块文档的对照表）。
CHART_HINT_HEIGHT = 260

#: 状态提示条的样式：**只含边框与内边距，没有任何 color / background**。
BANNER_QSS = 'border: 1px solid palette(mid); border-radius: 6px;'

# ---------------------------------------------------------------------------
# 柱状图的绘制参数（全部是版式数值，**没有色值** —— 颜色一律取自调色板）
# ---------------------------------------------------------------------------

#: 画布四周的留白（左 / 上 / 右 / 下），给刻度与标题用。
CHART_MARGIN = (46, 28, 14, 30)

#: 柱子占「每格宽度」的比例（剩下的当间隙）。
CHART_BAR_RATIO = 0.72

#: 横轴最多标几个刻度（柱子多的时候全标会糊成一片）。
CHART_MAX_TICKS = 10

#: 柱子不超过这个数量时，在柱顶写数值（再多就挤了）。
CHART_MAX_VALUE_LABELS = 31

#: 导出的默认 DPI（96 是屏幕基准，300 即放大到约 3.1 倍）。
CHART_EXPORT_DPI = 300


def is_count_reply(text) -> bool:
    """判断答复是否为 ``check_count`` 的**成功**正文。

    判据：去掉首尾空白后，**前 6 个字符**忽略大小写等于 ``count:``。

    为什么只认开头：成功正文后面还跟着 ``| Email: … | Range: …`` 两段，所以
    不能要求整串相等；而「只看开头」在服务端将来追加说明段时仍然安全。

    ⚠️ 只查开头、**不查整句**：失败文案里可能出现 ``count`` 这个词（例如某句
    描述），用「包含」判断会把它们误判成成功。

    ⚠️⚠️ **不要改用 ``users:``**（``user_list`` 的记号）：两者长度相同、都带
    冒号，只差前面那个词，拿混了会把**成功读成失败**。

    Args:
        text: 服务端回应正文（任意对象，会被转成字符串）。

    Returns:
        bool: 是 ``check_count`` 的成功正文返回 True。
    """
    return str(text if text is not None else '').strip()[
        :len(COUNT_TAG)].lower() == COUNT_TAG.lower()


def _find_range(text) -> str:
    """从答复里取出 ``Range:`` 段（取不到返回空串）.

    它承担两个作用：给横轴当日期标签、给标题当区间说明。**绝不**用它之外的东西
    推算日期（``Count:`` 后面只有数字，个数与日期的对应关系由服务端保证）。

    Args:
        text: 服务端回应正文。

    Returns:
        str: 例如 ``'2026-09-06 ~ 2026-10-05'``；没有该段时返回空串。
    """
    for part in str(text or '').split(DETAIL_SEP):
        part = part.strip()
        if part.lower().startswith(RANGE_TAG.lower()):
            return part[len(RANGE_TAG):].strip()
    return ''


def _find_values(text):
    """从答复的 ``Count:`` 段里取出那串数字（按原顺序）.

    ⚠️ **只做「切出数字」，不做任何日期换算**：个数 = 区间天数、逐日连续
    不跳号、顺序最早 -> 最新，这三条都由服务端保证。本地按个数反推日期只会
    与 ``Range:`` 段漂开。

    ⚠️ 负数是不该出现的（次数不会为负），所以 ``-`` 不参与切分 —— 出现了就说明
    服务端答复形态变了，宁可把它当解析失败（整段丢弃），也不要把 ``-1`` 画成
    一根往下的柱子。

    Args:
        text: 服务端回应正文。

    Returns:
        list: 非负整数列表；``Count:`` 段不存在或内容不是数字时返回空列表。
    """
    for part in str(text or '').split(DETAIL_SEP):
        part = part.strip()
        if part.lower().startswith(COUNT_TAG.lower()):
            body = part[len(COUNT_TAG):]
            values = []
            for token in body.split():
                if token.isdigit():
                    values.append(int(token))
            return values
    return []


def parse_count_reply(reply):
    """把 ``check_count`` 的答复拆成 ``(区间标签, 每天的次数)``.

    这是一个**纯函数**（不联网、不碰界面），所以可以离线单测：喂文本、看结论。

    ==================================================  ======================
    答复                                                 返回值
    ==================================================  ======================
    以 ``Count:`` 开头（含数字段）                        ``(区间标签, [int…])``
    以 ``Count:`` 开头但数字段是空的                      ``(区间标签, [])``
    其余一切（``Not permitted.`` / ``dll not found`` /    ``None``
    ``Users: …`` / 空响应 / 连不上的文案）
    ==================================================  ======================

    ⚠️ ``Not permitted.`` **是失败分支**（返回 ``None``）—— 调用方**不要**试图
    区分它的两种含义，也不要给用户编一句「这个邮箱不存在」。

    ⚠️ 以 ``Count:`` 开头但**一个数字都没有**时返回 ``(标签, [])`` 而不是
    ``None``：那说明服务端认了这个请求但区间里没有可画的数据，与「请求被拒」
    是两回事，界面应当分开说（见 :meth:`CheckCountView._on_reply`）。

    Args:
        reply: :meth:`zmlx.exts.WebLicense.check_count` 返回的正文。

    Returns:
        tuple | None: ``(区间标签, 数值列表)``；不是成功答复时返回 ``None``。
        区间标签可能为空串（服务端没给 ``Range:`` 段）。
    """
    text = str(reply if reply is not None else '').strip()
    if not is_count_reply(text):
        return None
    return _find_range(text), _find_values(text)


def today_str():
    """返回今天的 ``YYYY-MM-DD``（本地日期）.

    Returns:
        str: 例如 ``'2026-10-05'``。
    """
    return datetime.date.today().strftime(DATE_FORMAT)


def days_ago_str(days):
    """返回 ``days`` 天前（含今天在内共 ``days + 1`` 天）的 ``YYYY-MM-DD``.

    ⚠️ 这里的日期只用于**预填输入框**，也就是「用户想查哪一段」的初值。真正的
    区间以服务端答复里的 ``Range:`` 段为准 —— 两者偶尔不一致（服务端有自己的
    边界规则）时，**界面显示的一律是服务端那一份**（见 :meth:`CheckCountView.
    _on_reply`），本地这份不会被当成结论。

    Args:
        days: 往前推的天数；``0`` 就是今天。

    Returns:
        str: 例如 ``'2026-09-06'``。
    """
    day = datetime.date.today() - datetime.timedelta(days=max(int(days), 0))
    return day.strftime(DATE_FORMAT)


#: 正在后台跑的线程（模块级强引用）。
#:
#: ⚠️ **线程的 parent 绝不能是本控件**：标签页关闭时控件会被
#: ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，parent 是本控件的线程会
#: **跟着一起被析构**；而 Qt 规定「正在运行的 QThread 不能被销毁」，请求还没
#: 回来时就会直接 abort::
#:
#:     QThread: Destroyed while thread is still running
#:
#: 这是**进程级崩溃**，不是异常。本控件的每个请求最长 30 秒，关标签时线程几乎
#: 必然还在跑。``closeEvent`` 里的 ``wait()`` 兜不住 —— ``close_tab`` 走
#: ``deleteLater()``，**根本不发** ``closeEvent``。
#:
#: 挂在这里线程一定能跑完；控件销毁后迟到结果由 :func:`_is_deleted` 拦掉。
_RUNNING_WORKERS = []


def _forget_worker(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）。"""
    try:
        _RUNNING_WORKERS.remove(worker)
    except ValueError:
        pass


def _is_deleted(obj):
    """判断一个 Qt 对象的底层 C/C++ 对象是否已经被销毁。

    ⚠️ **为什么需要它**：本控件的结果槽是**用 lambda 连的**
    （``connect(lambda ...: self._on_reply(...))``）。Qt 只能对「接收者是
    QObject 的**绑定方法**」做自动断连 —— lambda 没有接收者对象，
    控件被 ``deleteLater()`` 销毁后**连接依然有效**，线程回来时那个 lambda
    照样被调用，于是在一个已经死掉的控件上碰子控件，抛::

        RuntimeError: wrapped C/C++ object of type QPushButton has been deleted

    （若槽是 ``self._on_reply`` 这种绑定方法，Qt 会自动断连、不会有这个问题 ——
    所以 ``about.py`` 不需要本函数。）

    Args:
        obj: 任意 Qt 对象（QWidget 等）。

    Returns:
        bool: 底层对象已被销毁返回 True。

    Added by DeepSeek, 2026-10-07
    """
    # ⚠️ 名字必须**按绑定逐个试**：PyQt6 的 sip 在 ``PyQt6.sip`` 下，顶层
    #    ``import sip`` 在 PyQt6 环境里找不到（会静默退化成「没被删」= 没生效）。
    for name in ('PyQt6.sip', 'PyQt5.sip', 'sip', 'shiboken6', 'shiboken2'):
        try:
            mod = __import__(name, fromlist=['_'])
        except ImportError:
            continue
        checker = getattr(mod, 'isdeleted', None)
        if checker is not None:
            try:
                return bool(checker(obj))
            except Exception:
                return False
        checker = getattr(mod, 'isValid', None)
        if checker is not None:
            # shiboken 的语义与 sip 相反：isValid 为真 = 还活着
            try:
                return not bool(checker(obj))
            except Exception:
                return False
    # 拿不到绑定层的检查函数：保守地认为「还活着」，让正常路径照常工作
    return False


class _Worker(QtCore.QThread):
    """在后台线程里查一次「查询次数统计」（**绝不碰界面**）。

    与 ``license_register._Worker`` 同构：线程里只发请求，结果用信号发回主线程。

    ⚠️ ``check_count`` 按契约**永不抛异常**，下面那个 ``except`` 只是防御：
    异常真逃出 :meth:`run` 的话线程会静默死掉、信号永不发出，按钮就永远停在
    禁用状态 —— 看起来像程序卡死。

    Attributes:
        sig_done: 信号，携带 ``(答复, 耗时文本)``。耗时单独一个参数、不挤进答复
            正文里，免得污染「只看开头」的成功判定。
    """

    sig_done = QtCore.pyqtSignal(str, str)

    def __init__(self, email, from_date, to_date, parent=None):
        """初始化。

        Args:
            email: 要统计**谁**的邮箱（原样转交，本地不 trim、不校验）。
            from_date: 起始日（``YYYY-MM-DD``）；空串 = 不发该字段。
            to_date: 结束日（``YYYY-MM-DD``，闭区间含这一天）；空串同上。
            parent: Qt 父对象。
        """
        super(_Worker, self).__init__(parent)
        self._email = email
        self._from = from_date
        self._to = to_date
        self.setObjectName('CheckCountViewWorker')

    def run(self):
        """线程体：发一次请求并把答复发回主线程。

        ⚠️ 耗时在**这里**量：量的必须是「请求本身用了多久」。若改成回到主线程
        再掐表，量到的会变成「界面等了多久」，里面混着信号跨线程的排队延迟。
        """
        start = time.perf_counter()
        try:
            reply = web_license.check_count(
                self._email, from_=self._from, to=self._to)
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：check_count 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        from zmlx.ui.utils.lic_utils import format_elapsed

        self.sig_done.emit(text, format_elapsed(time.perf_counter() - start))


class _BarChart(QtWidgets.QWidget):
    """原生柱状图（**本模块私有**）—— 一排柱子 + 基线 + 均值线 + 刻度.

    ⚠️ **刻意不做成公共控件**：它只为「许可查询次数」这一张图服务（横轴是日期、
    纵轴是次数、零值要画出来）。将若别处也要柱状图，再把它提出来独立成模块 ——
    现在提前抽象只会猜错需求。

    ⚠️ **它只用 PyQt，不需要额外安装任何东西**（PyQt 本来就是本项目运行 GUI 的
    前提）。用原生 Qt 而不是 matplotlib 的理由，见模块文档的对照表 —— 核心是
    ``sizeHint`` 终于「改得动」了，且不会出现内外层之间的留白。

    特性
    ----

    ====================  ====================================================
    悬停                 鼠标移到某根柱子上，``toolTip`` 显示「<标签>：<值> 次」
    点击                 选中该柱子（高亮）并把「标签：值」复制到剪切板
    右键                 导出 PNG / 复制图片 / 复制选中值 / 打开保存目录
    ====================  ====================================================

    配色**全部**取自 :meth:`QWidget.palette`，跟随主题与暗色模式。
    """

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象。
        """
        super(_BarChart, self).__init__(parent)
        self._values = []
        self._labels = []
        self._title = ''
        self._placeholder = ''
        self._hover_index = -1
        self._selected_index = -1

        # 鼠标移动要跟着走，否则收不到 mouseMoveEvent（悬停高亮就没法做）
        self.setMouseTracking(True)
        self.setMinimumHeight(CHART_MIN_HEIGHT)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)

        # 右键菜单的扩展点（与原 MatplotWidget.context_actions 同一套写法）
        self.context_actions = []

        # 自动保存目录：与 matplotlib 图**共用同一个**输出目录，
        # 免得用户为两种图记两个地方。
        now = datetime.datetime.now()
        name = now.strftime('%Y-%m-%d-%H-%M-%S-') + f'{now.microsecond:06d}'
        try:
            # ⚠️ **import 子模块 ``zmlx.plt._save``，不要 import 包 ``zmlx.plt``**
            #    —— 后者的 ``__init__`` 会连带拉起一大串 matplotlib 相关模块，
            #    而「只是想拿个保存路径」不需要它们。``_save.py`` 自己只依赖 os
            #    与 zmlx.system，很干净。
            from zmlx.plt._save import get_plt_save_path
            self._folder_save = get_plt_save_path(name)
        except Exception as err:
            print(f'Error (when get save path): {err}')
            self._folder_save = None

    # ------------------------------------------------------------------
    # 尺寸（**这就是当初在 matplotlib 上改不动的东西**）
    # ------------------------------------------------------------------

    def sizeHint(self):
        """返回偏好尺寸.

        ⚠️ 这个方法就是当初用 matplotlib 时**改不动**的那个 —— 那时它属于内层的
        ``FigureCanvasQTAgg``，只能靠运行时替换 ``__class__`` 去改（未定义行为，
        会偶发卡死）。现在它是本类自己的方法，返回什么完全由本类说了算，
        不需要任何花招。
        """
        return QtCore.QSize(480, CHART_HINT_HEIGHT)

    def minimumSizeHint(self):
        """返回最小尺寸：宽度可以压得很狠，高度不低于 :data:`CHART_MIN_HEIGHT`。"""
        return QtCore.QSize(120, CHART_MIN_HEIGHT)

    # ------------------------------------------------------------------
    # 数据
    # ------------------------------------------------------------------

    def set_data(self, labels, values, *, title=None):
        """设置要画的数据。

        Args:
            labels: 每根柱子的横轴标签（日期串）。
            values: 每根柱子的数值；**``0`` 也会被画出来**，因为「逐日连续
                不跳号」意味着 ``0`` 是真的那天没有查询，不是缺数据。
            title: 图上方的标题；``None`` 表示不改动当前标题。
        """
        self._labels = [str(v) for v in (labels or [])]
        self._values = [int(v) for v in (values or [])]
        if title is not None:
            self._title = str(title)
        self._placeholder = ''
        # 数据换了，之前的悬停 / 选中都不再对应得上
        self._hover_index = -1
        self._selected_index = -1
        self.update()

    def set_placeholder(self, text):
        """没有数据时显示一句提示（而不是留一片空白）。

        Args:
            text: 提示文本。
        """
        self._placeholder = str(text or '')
        self._labels = []
        self._values = []
        self._hover_index = -1
        self._selected_index = -1
        self.update()

    # ------------------------------------------------------------------
    # 几何换算
    # ------------------------------------------------------------------

    def _plot_rect(self):
        """返回真正画柱子的矩形（已扣掉四周留白）."""
        left, top, right, bottom = CHART_MARGIN
        return QtCore.QRect(
            left, top,
            max(self.width() - left - right, 1),
            max(self.height() - top - bottom, 1))

    def _bar_rect(self, index):
        """返回第 ``index`` 根柱子的矩形（按当前数值与尺寸算出）.

        Args:
            index: 柱子序号。

        Returns:
            QtCore.QRectF: 柱子矩形；序号非法或没有数据时是空矩形。
        """
        n = len(self._values)
        if n <= 0 or not (0 <= index < n):
            return QtCore.QRectF()
        plot = self._plot_rect()
        slot = plot.width() / float(n)
        peak = max(self._values) or 1
        height = plot.height() * self._values[index] / float(peak)
        bar_w = slot * CHART_BAR_RATIO
        left = plot.left() + index * slot + (slot - bar_w) / 2.0
        return QtCore.QRectF(left, plot.bottom() - height, bar_w, height)

    def _index_at(self, pos):
        """把鼠标位置换算成柱子序号（悬停 / 点击都用它）.

        ⚠️ 判定用「每格的横向范围」而不是「柱子的矩形」：值很小时（例如只有 1）
        柱子极矮，按矩形判定几乎点不中；按整格判定则好点得多 —— 这也是各处柱状图
        的通行做法。

        Args:
            pos: 鼠标位置。

        Returns:
            int: 柱子序号；不在任何一列上时返回 ``-1``。
        """
        n = len(self._values)
        if n <= 0:
            return -1
        plot = self._plot_rect()
        if not (plot.left() <= pos.x() <= plot.right()):
            return -1
        if not (plot.top() <= pos.y() <= plot.bottom() + 12):
            return -1
        slot = plot.width() / float(n)
        index = int((pos.x() - plot.left()) / slot)
        return index if 0 <= index < n else -1

    def _tick_indexes(self):
        """挑出要标在横轴上的位置（最多 :data:`CHART_MAX_TICKS` 个，总含最后一天）.

        Returns:
            list: 升序索引列表。
        """
        n = len(self._values)
        if n <= CHART_MAX_TICKS:
            return list(range(n))
        step = (n - 1) / float(CHART_MAX_TICKS - 1)
        return sorted({int(round(i * step)) for i in range(CHART_MAX_TICKS)})

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        """画整个图；没有数据时画一句提示。

        Args:
            event: 绘制事件。
        """
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
            if not self._values:
                if self._placeholder:
                    painter.setPen(self._colors()['muted'])
                    painter.drawText(self.rect(),
                                     QtCore.Qt.AlignmentFlag.AlignCenter,
                                     self._placeholder)
            else:
                self._paint_chart(painter)
        finally:
            # ⚠️ 必须 end()：不结束会让 Qt 报警告，严重时影响绘制
            painter.end()

    @staticmethod
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

    def _colors(self):
        """从当前调色板取出一套配色（**不写死任何色值**）.

        取色思路：**全部在调色板内部做混合**，不引入任何外部色值，所以亮色 /
        暗色主题都自动跟随。

        ============  ======================================================
        text          正文色（``WindowText``）
        muted         次要文字（刻度、数值标注）：正文色往背景混 45%
        axis / line   坐标轴与均值线：往背景混 62%（比 muted 再淡一档）
        bar           柱子：``Highlight``（本程序的强调色）
        zero          0 值的「浅底」：背景往 muted 混 45%
        ============  ======================================================

        ⚠️ **为什么不直接用 ``Disabled`` 那组当「次要文字」**（``license_register``
        里用 ``setEnabled(False)`` 表达「次要」是可行的，但那是给**控件**用的）：
        实测该组在亮色主题下是 ``#bebebe``，画在白色底上几乎看不见，刻度会糊掉。
        同理 0 值的浅底若只比背景深 6%（``#f1f1f1`` vs ``#ffffff``），色差只有
        **42**，等于没画 —— 现在混 45%，色差约 **200**，一眼就能看出「这里有个 0」。
        """
        palette = self.palette()
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)

        # ⚠️ 背景取 Base 与 Window 中**较亮**的那个：本控件实际画在窗口底色上，
        #    而暗色主题下 Base 可能比 Window 还暗 —— 取亮的那个才能保证
        #    「往它上面写字 / 从它出发调色」的方向总是对的。
        background = base if base.lightness() >= window.lightness() else window

        muted = self._blend(text, background, 0.45)
        axis = self._blend(text, background, 0.62)
        zero = self._blend(background, muted, 0.45)

        return {
            'text': text,
            'muted': muted,
            'axis': axis,
            'line': axis,
            'zero': zero,
            'background': background,
            'bar': QtGui.QColor(highlight),
            'bar_hover': QtGui.QColor(highlight).lighter(118),
            'bar_selected': QtGui.QColor(highlight).darker(120),
        }

    def _small_font(self):
        """返回比默认小一号的字体（刻度与数值标注用）."""
        font = self.font()
        size = font.pointSizeF()
        if size > 0:
            font.setPointSizeF(max(size - 1.0, 6.0))
        return font

    def _paint_chart(self, painter):
        """画标题、基线、均值线、柱子与刻度。

        Args:
            painter: 画笔。
        """
        colors = self._colors()
        plot = self._plot_rect()
        n = len(self._values)
        peak = max(self._values) or 1
        # 纵向留 15% 余量：柱顶的数字与均值线不至于贴到标题上
        scale = plot.height() / float(max(peak * 1.15, 1))
        metrics = painter.fontMetrics()

        # ---- 标题 ----
        if self._title:
            painter.setFont(self.font())
            painter.setPen(colors['text'])
            painter.drawText(
                QtCore.QRectF(0, 2, self.width(), CHART_MARGIN[1] - 4),
                int(QtCore.Qt.AlignmentFlag.AlignCenter |
                    QtCore.Qt.AlignmentFlag.AlignVCenter),
                metrics.elidedText(self._title,
                                   QtCore.Qt.TextElideMode.ElideRight,
                                   max(self.width() - 8, 10)))

        # ---- 基线 ----
        painter.setPen(QtGui.QPen(colors['axis'], 1))
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())

        # ---- 平均值虚线 ----
        mean = sum(self._values) / float(n)
        if mean > 0:
            y = int(plot.bottom() - mean * scale)
            painter.setPen(QtGui.QPen(colors['line'], 1,
                                      QtCore.Qt.PenStyle.DashLine))
            painter.drawLine(plot.left(), y, plot.right(), y)
            painter.setFont(self._small_font())
            painter.setPen(colors['muted'])
            painter.drawText(
                QtCore.QRectF(plot.right() - 78, y - metrics.height() - 1,
                              78, metrics.height()),
                int(QtCore.Qt.AlignmentFlag.AlignRight |
                    QtCore.Qt.AlignmentFlag.AlignVCenter),
                '\u65e5\u5747 %.1f' % mean)

        # ---- 柱子 ----
        show_values = n <= CHART_MAX_VALUE_LABELS
        for i, value in enumerate(self._values):
            rect = self._bar_rect(i)
            if value > 0:
                rect = QtCore.QRectF(rect.left(),
                                     plot.bottom() - value * scale,
                                     rect.width(), value * scale)
                if i == self._selected_index:
                    color = colors['bar_selected']
                elif i == self._hover_index:
                    color = colors['bar_hover']
                else:
                    color = colors['bar']
            else:
                # ⚠️ 0 **也要画出来**（一个矮矮的浅色底），因为「逐日连续不跳号」
                #    意味着 0 是真的那天没有查询，不是缺数据。
                #    ⚠️ 高度取 4 px 而不是 2 px：2 px 在多数缩放下只有一两个像素
                #    高，配上浅色基本看不见（实测过）。
                rect = QtCore.QRectF(rect.left(), plot.bottom() - 4,
                                     rect.width(), 4)
                color = colors['zero']

            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawRect(rect)

            if show_values:
                painter.setFont(self._small_font())
                painter.setPen(colors['text'] if value else colors['muted'])
                painter.drawText(
                    QtCore.QRectF(rect.left() - 8,
                                  rect.top() - metrics.height() - 2,
                                  rect.width() + 16, metrics.height()),
                    int(QtCore.Qt.AlignmentFlag.AlignHCenter |
                        QtCore.Qt.AlignmentFlag.AlignBottom),
                    str(value))

        # ---- 横轴刻度 ----
        painter.setFont(self._small_font())
        painter.setPen(colors['muted'])
        slot = plot.width() / float(n)
        for i in self._tick_indexes():
            label = self._labels[i] if i < len(self._labels) else str(i + 1)
            center = plot.left() + i * slot + slot / 2.0
            width = int(max(slot * 2, 30))
            painter.drawText(
                QtCore.QRectF(center - width / 2.0, plot.bottom() + 4,
                              width, metrics.height() + 4),
                int(QtCore.Qt.AlignmentFlag.AlignHCenter |
                    QtCore.Qt.AlignmentFlag.AlignTop),
                metrics.elidedText(label,
                                   QtCore.Qt.TextElideMode.ElideRight, width))

    # ------------------------------------------------------------------
    # 鼠标交互
    # ------------------------------------------------------------------

    def _tooltip_text(self, index):
        """返回某根柱子的提示文字。

        Args:
            index: 柱子序号。

        Returns:
            str: 例如 ``'09-28：3 次'``；序号非法时返回空串。
        """
        if not (0 <= index < len(self._values)):
            return ''
        label = self._labels[index] if index < len(self._labels) else ''
        value = self._values[index]
        if label:
            return f'{label}\uff1a{value} \u6b21'
        return f'{value} \u6b21'

    def mouseMoveEvent(self, event):
        """鼠标移动：刷新悬停高亮与 ``toolTip``。

        ⚠️ 只有**序号变化**时才 ``update()``：鼠标在同一根柱子上移动会产生大量
        事件，每个都重绘会让界面发涩。

        Args:
            event: 鼠标事件。
        """
        index = self._index_at(event.pos())
        if index != self._hover_index:
            self._hover_index = index
            self.setToolTip(self._tooltip_text(index))
            self.update()
        super(_BarChart, self).mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标离开：清掉悬停高亮。

        Args:
            event: 离开事件。
        """
        if self._hover_index != -1:
            self._hover_index = -1
            self.update()
        super(_BarChart, self).leaveEvent(event)

    def mousePressEvent(self, event):
        """左键点击：选中该柱子，并把「标签：值」复制到剪切板。

        Args:
            event: 鼠标事件。
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            index = self._index_at(event.pos())
            if index >= 0:
                self._selected_index = index
                self._copy_text(self._tooltip_text(index))
                self.update()
                return
            if self._selected_index != -1:      # 点空白 = 取消选中
                self._selected_index = -1
                self.update()
        super(_BarChart, self).mousePressEvent(event)

    @staticmethod
    def _copy_text(text):
        """把一段文本复制到剪切板（失败只打印，不抛）。

        Args:
            text: 要复制的文本。
        """
        if not text:
            return
        try:
            QtWidgets.QApplication.clipboard().setText(text)
        except Exception as err:
            print(f'Error (when copy to clipboard): {err}')

    # ------------------------------------------------------------------
    # 导出 / 复制（与原 MatplotWidget 的能力对齐）
    # ------------------------------------------------------------------

    def render_pixmap(self, *, dpi=None, background=None):
        """把当前图渲染成 :class:`QtGui.QPixmap`（导出与复制共用）.

        ⚠️ 用 ``QWidget.render()``，所以**导出的就是屏幕上看到的**（含悬停 /
        选中高亮）—— 不必另写一份绘制逻辑，也就不会出现「导出与界面不一致」。

        Args:
            dpi: 目标分辨率；``None`` 表示用屏幕尺寸（96）。
            background: 背景色；``None`` 表示用主题的 ``Base`` 色。
                **不要**用透明：PNG 透明底在白色文档里看不清柱子。

        Returns:
            QtGui.QPixmap: 渲染结果。
        """
        dpi = 96 if dpi is None else dpi
        scale = max(float(dpi) / 96.0, 0.1)
        size = QtCore.QSize(max(int(self.width() * scale), 1),
                            max(int(self.height() * scale), 1))
        pixmap = QtGui.QPixmap(size)
        if background is None:
            background = self.palette().color(QtGui.QPalette.ColorRole.Base)
        pixmap.fill(background)
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
            painter.scale(scale, scale)
            self.render(painter, QtCore.QPoint(0, 0))
        finally:
            painter.end()
        return pixmap

    @staticmethod
    def _export_dpi():
        """取用户配置的导出 DPI（取不到时用 :data:`CHART_EXPORT_DPI`）."""
        try:
            from zmlx.io.env import plt_export_dpi
            return int(plt_export_dpi.get_value())
        except Exception:
            return CHART_EXPORT_DPI

    def savefig(self, fname, *, dpi=None):
        """把当前图存成图片文件。

        Args:
            fname: 目标路径（自动建父目录）。
            dpi: 分辨率；``None`` 表示用用户配置的导出 DPI。

        Returns:
            bool: 成功返回 ``True``。
        """
        try:
            pixmap = self.render_pixmap(
                dpi=self._export_dpi() if dpi is None else dpi)
            path = make_parent(fname)
            ok = pixmap.save(path)
            if not ok:
                print(f'Error when save figure: cannot write <{path}>')
            return bool(ok)
        except Exception as err:
            print(f'Error when save figure: {err}')
            return False

    def savefig_by_dlg(self):
        """弹框选路径并导出（与 ``MatplotWidget.savefig_by_dlg`` 同名同义）."""
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption='\u8bf7\u9009\u62e9\u4fdd\u5b58\u8def\u5f84',
            directory=os.getcwd(),
            filter='Png\u56fe\u7247(*.png);;Jpg\u56fe\u7247(*.jpg);;'
                   '\u6240\u6709\u6587\u4ef6(*.*)')
        if fname:
            self.savefig(fname)

    def copy_to_clipboard(self):
        """把当前图复制到剪切板（复制的是**图片**）."""
        try:
            QtWidgets.QApplication.clipboard().setPixmap(
                self.render_pixmap(dpi=self._export_dpi()))
        except Exception as err:
            print(f'Error (when copy figure to clipboard): {err}')

    def save_file(self, open_dir=False, open_fig=False):
        """按当前时间自动保存到默认目录（**主窗口菜单「保存」会调它**）。

        与 ``MatplotWidget.save_file`` 同名同义，所以主窗口的
        「文件 → 保存」在本控件上也能用。

        Args:
            open_dir: 是否打开保存目录。
            open_fig: 是否用系统默认程序打开刚存的文件。

        Returns:
            str: 实际写入的路径；失败返回 ``None``。
        """
        try:
            if not isinstance(self._folder_save, str):
                return None
            now = datetime.datetime.now()
            name = now.strftime('%Y-%m-%d-%H-%M-%S-') + \
                f'{now.microsecond:06d}.png'
            path = os.path.join(self._folder_save, name)
            if not self.savefig(path):
                return None
            if open_dir:
                from zmlx.algs import startfile
                startfile(self._folder_save)
            if open_fig:
                from zmlx.algs import startfile
                startfile(path)
            return path
        except Exception as err:
            print(f'Error when save figure auto: {err}')
            return None

    def export_data(self):
        """接菜单命令：导出图片（同 :meth:`savefig_by_dlg`）."""
        self.savefig_by_dlg()

    # ------------------------------------------------------------------
    # 右键菜单
    # ------------------------------------------------------------------

    def get_context_menu(self):
        """构造右键菜单（能力与原 ``MatplotWidget.get_context_menu`` 对齐）.

        Returns:
            QtWidgets.QMenu: 菜单。
        """
        from zmlx.ui.alg import create_action

        menu = QtWidgets.QMenu(self)
        menu.addAction(create_action(
            self, '\u5bfc\u51fa\u56fe', icon='export',
            slot=self.savefig_by_dlg))
        menu.addAction(create_action(
            self, '\u590d\u5236\u56fe\u7247\u5230\u526a\u5207\u677f',
            icon='export', slot=self.copy_to_clipboard))

        selected = self._tooltip_text(self._selected_index)
        if selected:
            menu.addSeparator()
            menu.addAction(create_action(
                self,
                '\u590d\u5236\u9009\u4e2d\u503c\uff08%s\uff09' % selected,
                icon='export',
                slot=lambda: self._copy_text(selected)))

        if isinstance(self._folder_save, str):
            def open_dir():
                from zmlx.algs import startfile
                startfile(self._folder_save)

            menu.addAction(create_action(
                self, '\u6253\u5f00\u56fe\u7247\u4fdd\u5b58\u76ee\u5f55',
                slot=open_dir))

        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                if isinstance(action, dict):
                    name = action.get('name', None)
                    if name is not None:
                        sub = menu.addMenu(name)
                        for item in action.get('items', []):
                            sub.addAction(item)
                elif isinstance(action, str):
                    if action == '':
                        menu.addSeparator()
                else:
                    menu.addAction(action)
        return menu

    def contextMenuEvent(self, event):
        """右键菜单。

        Args:
            event: 右键事件。
        """
        self.get_context_menu().exec(event.globalPos())


class CheckCountView(QtWidgets.QWidget):
    """查询次数统计控件：一个邮箱 + 一段区间 → 按天的柱状图。

    首次显示时会自动查一次（见 :meth:`showEvent`），并在构造时预填邮箱与区间：
    默认查的是**本机自己**绑定的那个邮箱与最近 :data:`DEFAULT_DAYS` 天。

    ⚠️ 与 ``license_register`` 的自动查询有一处**关键差别**：那边只是自检，
    失败了安静作罢；这边查的是**统计**，所以失败也照常把服务端的原话显示出来
    （``Not permitted.`` 这类答复本身就是要给人看的）。
    """

    #: :meth:`_log` 最多保留多少行（只在内存里，见那个方法）
    MAX_LOG_LINES = 500

    def __init__(self, parent=None, *, email=None, days=DEFAULT_DAYS):
        """初始化控件。

        Args:
            parent: Qt 父对象。
            email: 预填的邮箱；``None`` 表示尝试从本机已绑定的授权里取
                （取不到就留空，用户自己填）。
            days: 预填区间的天数（见 :data:`DEFAULT_DAYS`）。
        """
        super(CheckCountView, self).__init__(parent)

        self._log_lines = []       # 日志（只留内存，见 _log：不能 print）

        self._worker = None        # 后台查询线程（持有引用，防被 GC）
        self._prefill_worker = None  # 后台取邮箱的线程（同上）
        self._user_list_worker = None  # 后台取名单的线程（同上）
        self._busy = False         # 有请求在飞：按钮禁用，防连点
        self._auto_checked = False  # 首次显示时的「查一次」是否已跑过
        self._last_query = None    # 上一次真正发出去的 (email, from, to)
        self._bound_email = None   # 本机绑定的邮箱（预填线程拿到后回填）
        self._server_emails = None  # 服务端名单；None = 本次运行还没拿到
        #: 名单里的**姓名**：邮箱（小写）-> 姓名（★ 服务端 v3.35 才有；
        #: 老服务端 / 非管理员时是空字典，界面就只显示邮箱）。
        self._server_names = {}
        #: 查询代次：每发起一次 +1。旧线程回来时若代号对不上就**丢弃它的结果**
        #: —— 用于「用户在左侧列表里连点了几个邮箱」的情形，见
        #: :meth:`CheckCountView._abandon_current_query`。
        self._query_generation = 0

        self.setWindowTitle('登录记录')

        self._build_ui()
        self._prefill_dates(days)
        if email is not None:
            self.email_edit.setText(str(email))
            self._bound_email = str(email).strip() or None
        self._refresh_email_list()
        self._update_buttons()

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------

    def _build_ui(self):
        """搭出整个界面（只在这里创建控件）。

        尺寸策略：**内容直接铺在控件上，不套滚动区**
        --------------------------------------------

        内容直接挂在控件的布局上，全屏只有一个弹性元素：

        - **柱状图**是唯一的伸缩项（``stretch=1`` + ``Expanding``）——窗口变高时
          它变高，变矮时它**先缩**，缩到 :data:`CHART_MIN_HEIGHT` 为止；
        - 其余各行（横幅 / 表单 / 原始答复）都是固定高度，**永不参与拉伸**。

        ⚠️ **为什么这里不需要滚动区**（而 matplotlib 版需要一个兜底）：
        ``QScrollArea`` 判「要不要滚」看的是内容的 ``sizeHint``，而 matplotlib 那个
        内层画布会把 ``sizeHint`` 顶到约 660 px，于是窗口稍矮就冒滚动条，怎么调都
        下不来（实测五种办法全失败，见模块文档）。原生 ``_BarChart`` 的
        ``sizeHint`` 就是它自己的方法（260 px），所以
        **「够大就铺满、太小才缩图」这条直接成立**，不需要滚动区来兜底。

        ⚠️ 也**不要**去覆写别的控件的 ``sizeHint``、更不要改 ``__class__``
        （早先踩过，会偶发卡死）：柱状图这里只需要
        ``setMinimumHeight`` + ``Expanding``。
        """
        shell = QtWidgets.QHBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # ---- 左：邮箱列表（默认隐藏，拿到名单才显示）----
        shell.addWidget(self._build_email_list())

        # ---- 右：原有内容，原封不动 ----
        right = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(right)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        outer.setSpacing(GAP)

        # ⚠️ 这里**不放**标题与说明文字：标签页顶部已经有「授权记录」这个标题，
        #    控件内再写一遍是重复的。首屏直接给横幅 + 表单 + 图。
        outer.addWidget(self._build_status_banner())
        outer.addWidget(self._separator())
        outer.addWidget(self._build_form())
        # ⚠️ 这个 1 是关键：**只有柱状图**吃多余高度，其余各行保持自身高度
        outer.addWidget(self._build_canvas(), 1)
        outer.addWidget(self._build_status_detail())
        # ⚠️ 右侧吃满剩余宽度（左侧列表是固定宽）
        shell.addWidget(right, 1)
        self._right_panel = right

    # ------------------------------------------------------------------
    # 左侧邮箱列表
    # ------------------------------------------------------------------

    def _build_email_list(self):
        """左侧邮箱列表（**默认隐藏**）。

        ⚠️⚠️ **启动时隐藏，只有真的拿到名单才显示**。这正是「非管理员看到的界面
        与没有这个功能时**完全一致**」的实现方式：列表为空 -> 整个左侧不占空间，
        右侧照旧铺满。

        ⚠️ 用 ``itemClicked`` 而不是 ``currentItemChanged``：后者在**程序填充列表
        时也会发**，会导致「打开页面就自动查第一个邮箱」—— 那不是用户的意图。
        ``itemClicked`` 只在**用户真的点了某一项**时才发。

        Returns:
            QtWidgets.QWidget: 左侧面板（标题 + 列表 + 刷新按钮）。
        """
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(LIST_WIDTH)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(MARGIN, MARGIN, GAP, MARGIN)
        layout.setSpacing(GAP)

        title = QtWidgets.QLabel('用户')
        title.setEnabled(False)      # 置灰跟随主题，不写死颜色
        layout.addWidget(title)

        self.email_list = QtWidgets.QListWidget()
        self.email_list.setMinimumHeight(LIST_MIN_HEIGHT)
        # ★ 条目是**两行**（姓名在上、邮箱在下）：不打开换行的话，Qt 会把换行
        #   当空白压成一行，长邮箱又会把列表撑宽 —— 两者都正是要避免的。
        self.email_list.setWordWrap(True)
        self.email_list.setToolTip(
            '点一个邮箱，右侧就会去查它的许可查询次数。\n'
            '名单由服务端维护，仅管理员可见。')
        self.email_list.itemClicked.connect(self._on_email_item_clicked)
        layout.addWidget(self.email_list, 1)

        self.refresh_list_button = QtWidgets.QPushButton('刷新名单')
        self.refresh_list_button.setFlat(True)   # 扁平 = 视觉上的次级按钮
        self.refresh_list_button.setToolTip('重新向服务端要一次用户名单。')
        self.refresh_list_button.clicked.connect(
            lambda: self._start_user_list_query(force=True))
        layout.addWidget(self.refresh_list_button)

        panel.setVisible(False)      # ⚠️ 默认隐藏，见 docstring
        self.email_list_panel = panel
        return panel

    def _refresh_email_list(self):
        """重建左侧列表 = 服务端名单 ∪ {本机绑定邮箱}（本机邮箱置顶、去重）。

        ⚠️ **本机绑定邮箱排最前**：非管理员拿不到名单时，列表里至少还有它自己那
        一个；管理员则一眼看到「我自己」在最上面。

        ⚠️⚠️ **列表为空时把整个左侧隐藏**（不是只藏列表）：这样非管理员看到的
        界面与「没有这个功能」时**逐像素一致**，不会凭空少掉一块。

        ⚠️ 填充期间 ``blockSignals(True)``：虽然用的是 ``itemClicked``（填充不会
        触发它），但多一道保险 —— 万一将来有人把信号换成 ``currentItemChanged``，
        这道保险能挡住「打开页面就自动查询」。

        Returns:
            None
        """
        panel = getattr(self, 'email_list_panel', None)
        if panel is None:
            return

        emails = merge_emails(
            [self._bound_email] if self._bound_email else [],
            self._server_emails or [])
        names = getattr(self, '_server_names', None) or {}

        self.email_list.blockSignals(True)
        try:
            self.email_list.clear()
            for email in emails:
                # ★ 姓名在上、邮箱在下（用户 2026-10-18 的要求）：控件宽度是固定的，
                #   把邮箱塞到第二行才不会把列表撑宽。没有姓名时只显示邮箱。
                name = str(names.get(email.strip().lower()) or '').strip()
                # ⚠️ 有些用户的「姓名」字段填的就是邮箱（注册时图省事），两行会变成
                #   同一串重复 —— 那种情况按「没有姓名」处理，只显示一行。
                if name.lower() == email.strip().lower():
                    name = ''
                # ⚠️ 面板只有 LIST_WIDTH 宽，长邮箱一行放不下 —— Qt 的默认委托只在
                #   空格处折行，邮箱没有空格，结果是右边被硬裁掉。按像素宽度先折好。
                viewport = self.email_list.viewport()
                width = max(60, (viewport.width() if viewport is not None
                                 else LIST_WIDTH) - 12)
                email_text = wrap_text_to_width(email, width, self.email_list.font())
                text = '%s\n%s' % (name, email_text) if name else email_text
                item = QtWidgets.QListWidgetItem(text)
                # ⚠️ 邮箱**单独存一份**：条目文字已经掺了姓名，取 text() 会拿到
                #   「姓名\n邮箱」，拿它去查是错的。
                item.setData(QtCore.Qt.ItemDataRole.UserRole, email)
                item.setToolTip(text)        # 太长时悬停看全称
                self.email_list.addItem(item)
        finally:
            self.email_list.blockSignals(False)

        # ⚠️ 空 -> 整块隐藏；有内容 -> 显示
        panel.setVisible(bool(emails))

    def _on_email_item_clicked(self, item):
        """用户点了左侧列表里的某个邮箱：让右侧去查它。

        Args:
            item: 被点击的列表项。
        """
        if item is None:
            return
        # ⚠️ 条目文字可能是「姓名\n邮箱」，邮箱以 UserRole 为准（见 _refresh_email_list）
        email = item.data(QtCore.Qt.ItemDataRole.UserRole) or item.text()
        self.query_email(str(email))

    # ------------------------------------------------------------------
    # 服务端名单（后台拉取）
    # ------------------------------------------------------------------

    def _start_user_list_query(self, force=False):
        """在后台拉一次服务端名单（**每次运行最多一次**，除非强制刷新）。

        ⚠️⚠️ **必须在后台线程**：``user_list`` 不做缓存、每次真的发出去，单次最长
        阻塞 30 秒。在 UI 线程里调就等于「点开授权记录卡 30 秒」—— 而本控件的要求
        正是**立即显示**。

        ⚠️ 拉取期间**界面照常可用**（不置忙、不禁用查询按钮）：名单只是左侧列表的
        装饰，不该拦住用户查询。

        Args:
            force: 忽略「已经拉过」的记录，强制再拉一次（「刷新名单」按钮用）。
        """
        if self._user_list_worker is not None:
            return                      # 已经在拉了，不叠加
        if self._server_emails is not None and not force:
            return                      # 本次运行已经拿到过（含「确认拿不到」）
        # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见 _Worker
        #    那一处的说明（关标签时控件会被销毁，parent 设成控件会连着线程一起删）。
        worker = _UserListWorker()
        worker.sig_done.connect(self._on_user_list)
        worker.finished.connect(lambda: self._on_user_list_finished(worker))
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._user_list_worker = worker
        _RUNNING_WORKERS.append(worker)
        worker.start()

    def _on_user_list_finished(self, worker):
        """名单线程结束（主线程调用）：释放引用。

        Args:
            worker: 刚结束的线程。
        """
        if _is_deleted(self):
            return          # 控件已随标签页关闭被销毁
        if self._user_list_worker is worker:
            self._user_list_worker = None

    def _on_user_list(self, reply):
        """名单回来了（主线程调用）：解析并刷新左侧列表。

        ⚠️ **失败一律静默**：``Not permitted.``（非管理员）是 HTTP 200 的
        **正常业务答复**，不是错误 —— 不弹窗、不改横幅、不写进日志正文。
        列表退回到「只有本机绑定邮箱」（再没有就整块隐藏），界面与没有这个功能时
        **完全一致**。

        ⚠️ **名单不落盘、也不写进日志内容**：那是**别人的**邮箱，服务端刻意连
        日志都不写。这里只记条数。

        ⚠️ **绝不在这里主动发起查询**：名单是异步回来的，用户可能早就不在看这个
        页面了。查询只由**用户点击列表项**触发。

        Args:
            reply: ``user_list_detail`` 的服务端答复正文（老服务端是 ``user_list``
                的答复 —— 两条在这里都要认）。
        """
        entries = parse_user_list_detail(reply)
        if entries is None:
            # ★ 不是新动作的答复：可能是**老服务端**（< 3.35，把未知 action 当查询
            #   回了一句 ``Yes``，此时 parse 也是 None）或者拿到了旧格式 ``Users:``。
            #   后者在这里兜底；前者拿不到东西，退回「只用本机邮箱」。
            emails = parse_user_list(reply)
            if emails is None:
                # 没拿到（越权 / 故障 / 老服务端）—— 记成空列表，避免反复重试
                self._server_emails = []
                self._server_names = {}
                self._log('用户名单不可用（可能不是管理员），左侧列表只用本机邮箱')
                self._refresh_email_list()
                return
            entries = [('', email) for email in emails]
        self._server_emails = [email for _, email in entries]
        self._server_names = {email.lower(): name for name, email in entries if name}
        named = len(self._server_names)
        self._log(f'取到用户名单：{len(entries)} 个邮箱'
                  + (f'（其中 {named} 个带姓名）' if named else
                     '（这次没拿到姓名，可点「刷新名单」重试）')
                  + '（不落盘）')
        self._refresh_email_list()

    def query_email(self, email, *, force=True):
        """把邮箱填进输入框并发起一次查询（**给左侧列表 / 外部调用**）。

        ⚠️ 复用 :meth:`start_query`：它已经处理好「有请求在飞时不叠加」、
        后台线程、以及各种失败分支的文案。这里**不要**另写一套查询流程。

        ⚠️⚠️ **``force=True``（默认）时会取消正在飞的那个查询，立刻换成本次点击
        的目标**。理由：用户在列表里连点几个邮箱是很自然的动作，如果每次都因为
        「上一个还没回来」而被忽略，他会以为界面卡了 —— 而**他要看的明明是最后
        点的那个**。旧的那次结果回来时会被 :meth:`_on_reply` 按「是否还是当前
        目标」丢掉（见那里的说明）。

        Args:
            email: 要查的邮箱；空串直接返回（不查询）。
            force: ``True`` = 换目标（默认）；``False`` = 有请求在飞就不发起。

        Returns:
            bool: 真的发起了查询返回 True。
        """
        email = str(email or '').strip()
        if not email:
            return False
        if self._busy:
            if not force:
                self._log('上一个查询还没结束，这次点击被忽略')
                return False
            # ⚠️ 让位给新的目标：把旧的标记成「作废」，并放开 _busy。
            #    旧线程还在跑（QThread 不能强行杀掉），但它回来时会被丢掉。
            self._log('切换到新的查询目标，放弃上一个未完成的结果')
            self._abandon_current_query()
        self.email_edit.setText(email)
        self.start_query()
        return True

    def _abandon_current_query(self):
        """放弃当前正在飞的查询（旧结果回来时会被丢掉）。

        ⚠️ **不杀线程**：``QThread`` 不能安全地强制终止（``terminate()`` 会让
        资源泄漏、甚至崩）。正确做法是**只放开闸门、并把旧结果标记为作废** ——
        线程自己跑完、结果回来时按代次丢掉即可。

        Returns:
            None
        """
        self._query_generation += 1     # 旧结果靠这个代号失效
        self._busy = False
        self._update_buttons()

    def _build_status_banner(self):
        """顶部「一句话结论」提示条。

        Returns:
            QtWidgets.QLabel: 状态提示条。
        """
        self.status_label = QtWidgets.QLabel('准备就绪。')
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(10, 7, 10, 7)
        # ⚠️ 只设边框粗细与圆角，**色值一律交给主题**（见模块文档的版式约定）
        self.status_label.setStyleSheet(BANNER_QSS)
        return self.status_label

    @staticmethod
    def _separator():
        """一条 1px 水平细线（用留白 + 细线划分区域，不画分组框）。

        Returns:
            QtWidgets.QFrame: 水平细线。
        """
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        return line

    def _build_form(self):
        """「邮箱 + 区间 + 查询」表单区。

        ⚠️ **控件不做任何日期校验**：形态（``YYYY-MM-DD``，10 字符）、区间顺序、
        366 天上限的文案全都归服务端拥有（它的最准）。本地复写一份必然漂，而漂了
        会表现为「本地放过去的请求被服务端拒」或反过来 —— 两种都查半天。
        所以下面只有「快捷按钮」，没有校验。

        Returns:
            QtWidgets.QWidget: 配置好的表单。
        """
        box = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(GAP)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                               QtCore.Qt.AlignmentFlag.AlignVCenter)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(GAP)
        self.email_edit = QtWidgets.QLineEdit()
        self.email_edit.setPlaceholderText(EMAIL_PLACEHOLDER)
        self.email_edit.setToolTip(
            '要统计谁的邮箱。\n'
            '非管理员只能查自己绑定的那个邮箱，查别人的会得到 Not permitted.。')
        self.email_edit.returnPressed.connect(self.start_query)
        row.addWidget(self.email_edit, 1)

        self.query_button = QtWidgets.QPushButton('查询')
        self.query_button.setMinimumHeight(BUTTON_HEIGHT)
        self.query_button.setDefault(True)
        self.query_button.setToolTip(
            '向服务端要一次统计数据。\n'
            '两个日期都留空时，服务端回最近 60 天（含今天）。')
        self.query_button.clicked.connect(self.start_query)
        row.addWidget(self.query_button)
        form.addRow('邮箱', row)

        date_row = QtWidgets.QHBoxLayout()
        date_row.setSpacing(GAP)
        self.from_edit = QtWidgets.QLineEdit()
        self.from_edit.setPlaceholderText('YYYY-MM-DD')
        self.from_edit.setToolTip('起始日（闭区间含这一天）；留空表示不发该字段。')
        self.from_edit.returnPressed.connect(self.start_query)
        date_row.addWidget(self.from_edit, 1)

        date_row.addWidget(QtWidgets.QLabel('至'))

        self.to_edit = QtWidgets.QLineEdit()
        self.to_edit.setPlaceholderText('YYYY-MM-DD')
        self.to_edit.setToolTip('结束日（闭区间含这一天）；留空表示不发该字段。')
        self.to_edit.returnPressed.connect(self.start_query)
        date_row.addWidget(self.to_edit, 1)

        for days in DAY_CHOICES:
            btn = QtWidgets.QPushButton(f'最近{days}天')
            btn.setFlat(True)       # 扁平 = 视觉上的次级按钮
            btn.setToolTip(f'把区间设为「{days} 天前 至 今天」，然后点「查询」。')
            btn.clicked.connect(
                lambda checked=False, d=days: self.set_range_days(d))
            date_row.addWidget(btn)
        form.addRow('区间', date_row)
        return box

    def _build_canvas(self):
        """柱状图区（用模块内的原生 :class:`_BarChart`）。

        ⚠️ **不再套 QGroupBox**（用户要求）：那圈带标题的边框是多余的装饰，标题
        （「每日查询次数」）本身也重复 —— 图自己已经有一个更准确的标题
        （含区间与天数）。直接把柱状图控件作为这一行。

        ⚠️ **尺寸只设下限**（``_BarChart.__init__`` 里已经设好），**不要**再设
        ``maximumHeight``：那会把它钉死、上方留出一片空白（在 matplotlib 版上
        实测踩过）。它的 ``sizeHint`` 由自己给出，布局会正确地压 / 放。

        Returns:
            _BarChart: 柱状图控件。
        """
        from zmlx.ui.pyqt import QAction

        self.canvas = _BarChart(self)

        # 右键菜单的扩展点（``_BarChart`` 已经预留，与原 MatplotWidget 同一套写法）
        actions = []
        for days in DAY_CHOICES:
            action = QAction(f'最近{days}天', self)
            action.triggered.connect(
                lambda checked=False, d=days: self.set_range_days(d, query=True))
            actions.append(action)
        actions.append('')                  # 空串 = 一条分隔线
        copy_action = QAction('复制原始答复', self)
        copy_action.triggered.connect(self.copy_reply)
        actions.append(copy_action)
        self.canvas.context_actions = actions

        self.canvas.set_placeholder(
            '还没有数据。填写邮箱与区间后点击「查询」。')
        return self.canvas

    def _build_status_detail(self):
        """「服务器原始答复」可折叠区（**默认收起**，沿用 ``QGroupBox``）。

        ⚠️ **默认收起**（用户要求）：这里显示的是服务端原话 + 往返耗时，属于
        「想深究时才看」的排错信息，平时占着一块地方反而挤压柱状图。结论已经由
        上方横幅用一句话给出来了（失败时 ``Not permitted.`` 这类原话**照样**
        会出现在横幅里，不会被藏起来）。想看原始报文点一下标题即可展开。

        ⚠️ **保留 ``QGroupBox``**（用户要求）：它的「可勾选 + 扁平」用法正好就是
        「一个可折叠的小节」，勾选框本身就是展开 / 收起的开关，不必自造按钮。
        （被去掉的是**绘图区**外面那个组合框 —— 那个纯属多余的装饰。）

        Returns:
            QtWidgets.QGroupBox: 可勾选的容器（勾选 = 展开，扁平样式）。
        """
        box = QtWidgets.QGroupBox('服务器原始答复')
        box.setCheckable(True)
        box.setChecked(False)   # ⚠️ 默认收起，见 docstring
        box.setFlat(True)       # 去掉会与卡片风格重复的那条标题线
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)

        self.status_view = QtWidgets.QPlainTextEdit()
        self.status_view.setReadOnly(True)
        self.status_view.setFixedHeight(STATUS_VIEW_HEIGHT)
        self.status_view.setPlaceholderText(
            '查询后这里显示服务器的原话，以及本次往返耗时。')
        layout.addWidget(self.status_view)

        # ⚠️ **连接必须放在 ``status_view`` 建好之后**：``setVisible`` 那条槽要用
        #    到它。若在它被创建之前连上，槽函数一跑就抛 ``AttributeError`` ——
        #    而 PyQt 会把槽里的异常**静默吞掉**，表现为「标题能勾，但内容区纹丝
        #    不动」（真踩过）。
        box.toggled.connect(self.status_view.setVisible)
        # ⚠️ 必须**显式**设为不可见：``setChecked(False)`` 是在连接之前调的，
        #    那个信号没有发出，光靠它藏不住这个控件。
        self.status_view.setVisible(False)
        return box

    # ------------------------------------------------------------------
    # 取值与状态
    # ------------------------------------------------------------------

    def get_query(self):
        """返回当前要查的 ``(邮箱, 起始日, 结束日)``（都已去掉首尾空白）.

        ⚠️ **只做去空白，不做形态判断**：这里取到的值原样交给服务端（空串表示
        「不发该字段」），任何本地校验都会成为一份会漂的副本。

        Returns:
            tuple: ``(email, from_date, to_date)``。
        """
        return (self.email_edit.text().strip(),
                self.from_edit.text().strip(),
                self.to_edit.text().strip())

    def set_range_days(self, days, *, query=False):
        """把区间输入框设为「最近 ``days`` 天」（本地计算，不联网）。

        Args:
            days: 天数；区间是 ``days - 1`` 天前 至 今天（含两端），所以
                ``days=7`` 得到 7 个数字。
            query: 是否顺手发起一次查询。``False``（默认）只改输入框，让用户可以
                先把邮箱改对再点「查询」。
        """
        self.from_edit.setText(days_ago_str(max(int(days), 1) - 1))
        self.to_edit.setText(today_str())
        if query:
            self.start_query()

    def _prefill_dates(self, days):
        """把区间输入框预填成「最近 ``days`` 天」."""
        self.set_range_days(days)

    def _prefill_email(self):
        """尝试从本机已绑定的授权里取邮箱填进输入框（**在后台线程里调用**）。

        判据完全复用 ``license_register`` 那一套（``check_web`` → ``bound_info``）：
        **只有真正绑定了邮箱才返回内容**，未绑定 / 查询失败一律返回空串 —— 那种
        情况下把答复里的邮箱填进去等于谎称「你在查你自己」。

        ⚠️ 取不到是**常态**（没联网、没绑定、老授权里没有这个字段），安静返回
        空串即可，不弹窗、不报错。

        ⚠️ 用 ``read_cache=True``：这只是「填个表单初值」，不是自检 —— 与状态栏
        的取舍一致；注册页那两处传 ``False`` 是因为它们要确认「现在」的状态。

        Returns:
            str: 已绑定的邮箱；取不到时返回空串。
        """
        try:
            from zmlx.ui.utils.lic_utils import (
                CHECK_FEATURE, bound_info, check_web)

            text, _ = check_web(CHECK_FEATURE, read_cache=True)
            return str(bound_info(text).get('email') or '').strip()
        except Exception as err:
            print(f'Error (when prefill email): {err}')
            return ''

    def _log(self, message):
        """记一行日志（排错用）。

        ⚠️ **本控件没有日志区**（不像 ``feedback_tool`` 那样有 ``log_view``），
        所以这里**只把内容留在内存里**（``self._log_lines``）—— 界面上的
        「服务器原始答复」区（``status_view``）显示的是服务端原话，不是日志。

        ⚠️ **不要用 ``print()``**：GUI 模式下 ``MainWindow`` 把 ``sys.stdout``
        换成了自己，输出面板没开着时它会**把 print 的内容显示到状态栏** ——
        于是本控件的日志会冒到状态栏上去（``查询响应：Count: 0 0 0 …`` 那一串
        就是这么来的，真踩过）。

        ⚠️ 写内存那一句必须兜住异常（列表理论上不会抛，但保持防御性）。
        """
        text = str(message)
        try:
            self._log_lines.append(text)
            del self._log_lines[:-CheckCountView.MAX_LOG_LINES]
        except Exception:
            pass

    def _show_status(self, text, ok=None):
        """在顶部提示条里显示一句话结论。

        Args:
            text: 结论文本（可以是服务端原话）。
            ok: ``True`` 成功 / ``False`` 失败 / ``None`` 中性。
                ⚠️ 只用来决定**是否置灰**，不写死颜色。
        """
        text = str(text or '').strip()
        self.status_label.setText(text if text else '准备就绪。')
        self.status_label.setEnabled(ok is not False)

    def _update_buttons(self):
        """按「是否正在查询」刷新按钮可用性（防连点排起一队请求）."""
        idle = not self._busy
        for btn in (self.query_button,):
            btn.setEnabled(idle)
        for edit in (self.email_edit, self.from_edit, self.to_edit):
            edit.setReadOnly(not idle)

    # ------------------------------------------------------------------
    # 查询编排
    # ------------------------------------------------------------------

    def showEvent(self, event):
        """控件首次显示时，自动查一次（并在后台取本机绑定的邮箱）。

        ⚠️ 放在 :meth:`showEvent` 而不是 ``__init__``：本控件由 TabWidget
        **创建后立刻挂到标签页**，不一定马上显示；而且构造期间起网络线程会让
        「打开窗口」这件事变得不可预期。用 :attr:`_auto_checked` 保证**只跑
        一次** —— 切换标签页会反复触发本事件，不能每次都发一次请求。
        """
        super(CheckCountView, self).showEvent(event)
        if self._auto_checked:
            return
        self._auto_checked = True
        # 延后一拍：showEvent 期间控件还没画出来，此时起线程 / 改按钮状态
        # 在某些平台会看到界面闪一下
        QtCore.QTimer.singleShot(0, self._auto_start)

    def _auto_start(self):
        """首次显示时的自动动作：**在后台**补邮箱 + 拉名单，然后再查一次。

        ⚠️ **两个请求都在后台线程**（``_PrefillWorker`` 取本机绑定邮箱、
        ``_UserListWorker`` 取服务端名单），主线程**从不等待**它们 —— 这正是
        「点开授权记录立即显示」的实现方式。

        ⚠️ 两者**分开成两个线程**：取绑定邮箱失败不该连带把名单也丢掉，反之亦然。
        名单那一路即使失败也只是「左侧列表不显示」，不影响本方法的主体流程。

        ⚠️ **本方法不等待名单**：先把主流程（补邮箱 -> 查询）跑起来，名单回来了
        再单独刷新左侧列表（见 :meth:`_on_user_list`）。所以「立即显示」这条在
        名单很慢（最长 30 秒）时依然成立。
        """
        # 名单那一路：起了就不管它，结果经信号回来自己处理
        self._start_user_list_query()

        if not self.email_edit.text().strip():
            # ⚠️ 取邮箱本身要联网（最长 30 秒），**不能在 UI 线程里做**
            self._show_status('正在读取本机已绑定的邮箱...', ok=None)
            # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见 _Worker
            #    那一处的说明（关标签时控件会被销毁，parent 设成控件会连着线程一起删）。
            #    ⚠️ 第一个参数是**取值用的 owner 引用**，不是 Qt parent —— 不要写
            #    _PrefillWorker(self, self)。
            worker = _PrefillWorker(self)
            worker.sig_done.connect(self._on_prefill)
            worker.finished.connect(lambda: self._prefill_worker_done(worker))
            worker.finished.connect(lambda w=worker: _forget_worker(w))
            worker.finished.connect(worker.deleteLater)
            self._prefill_worker = worker
            _RUNNING_WORKERS.append(worker)
            worker.start()
            return
        self.start_query()

    def _prefill_worker_done(self, worker):
        """邮箱预取线程结束：释放引用（主线程调用）."""
        if _is_deleted(self):
            return          # 控件已随标签页关闭被销毁
        if self._prefill_worker is worker:
            self._prefill_worker = None

    def _on_prefill(self, email):
        """邮箱取回来了（主线程调用）：填进输入框、刷新列表、并开始查询。

        ⚠️ **只在输入框为空时填**：用户可能已经在敲字了（查询要联网，回来得比人
        慢），覆盖掉他刚输入的内容是最讨厌的一类交互。填不填得上，都照样发起
        首次查询（查不到邮箱时服务端会回一句可读的失败文案）。

        ⚠️ 把它同时记为 :attr:`_bound_email` 并刷新左侧列表：**非管理员拿不到
        服务端名单时，列表里就只有它自己那一个** —— 这正是「至少显示它关联的那个
        邮箱」那条要求。绑定邮箱**不写进任何历史**（没有历史这回事了）。
        """
        email = str(email or '').strip()
        if email:
            self._bound_email = email
        if email and not self.email_edit.text().strip():
            self.email_edit.setText(email)
            self._log(f'预填邮箱：{email}')
        self._refresh_email_list()
        self.start_query()

    def start_query(self):
        """发起一次查询（**不等结果**，请求在后台线程 :class:`_Worker` 里跑）。

        本方法只做三件事：本地拦一下「邮箱为空」、禁用按钮、起线程。

        ⚠️ **本地只拦「邮箱为空」** —— 它连一次往返都不值得。日期形态、区间顺序、
        366 天上限、越权，全都由服务端拥有答复文案，本地复写只会漂。
        """
        if self._busy:
            # 理论上按钮已禁用，点不到；这里是第二道保险（例如回车键触发）
            self._log('上一个查询还没结束，请稍候')
            return

        email, from_date, to_date = self.get_query()
        if not email:
            self._show_status('请先填写要统计的邮箱。', ok=False)
            self.email_edit.setFocus()
            return

        self._last_query = (email, from_date, to_date)
        self._log(f'查询次数统计：email={email} '
                  f'from={from_date or "(默认)"} to={to_date or "(默认)"}')
        self._show_status('正在查询...', ok=None)

        # ⚠️ 把「代号」一并绑进信号处理：这次查询属于哪一代，回来时就按哪一代判。
        #    这样即使用户中途改查了别的邮箱（代号 +1），旧结果回来也会被丢掉。
        generation = self._query_generation

        # ⚠️ parent **留空**（不是 ``parent=self``）：本控件会随标签页被
        #    deleteLater 销毁，parent 设成自己的线程会被连带析构 —— 请求还在飞
        #    时就是进程崩溃（"QThread: Destroyed while thread is still running"）。
        #    改由模块级 _RUNNING_WORKERS 持有强引用。
        worker = _Worker(email, from_date, to_date, parent=None)
        worker.sig_done.connect(
            lambda reply, elapsed, g=generation:
                self._on_reply(reply, elapsed, generation=g))
        worker.finished.connect(lambda: self._on_worker_finished(worker))
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()

    def _on_worker_finished(self, worker):
        """后台线程结束（主线程调用）：放开按钮、释放引用。

        ⚠️ 只释放**当前**那个 worker 的引用；若它已经被新的查询顶替掉
        （``self._worker`` 已经是别人），就什么都不做 —— 否则会把新查询的引用
        清掉，让那个线程失去引用而被 GC。
        """
        if _is_deleted(self):
            return          # 控件已随标签页关闭被销毁：没什么可释放的
        if self._worker is worker:
            self._worker = None
            self._busy = False
            self._update_buttons()

    def _on_reply(self, reply, elapsed_text, *, generation=None):
        """答复回来了（**在主线程里跑**）：画图 + 显示原始答复。

        ⚠️ 判定用的是本模块的 :func:`parse_count_reply`（**只看开头是不是
        ``Count:``**），不是 ``reply == ...`` 之类：成功正文后面还跟着
        ``| Email: … | Range: …`` 两段，严格比较是一条会随服务端演进而失效的
        隐含假设。

        ⚠️ 失败时**原样显示服务端原话**（``Not permitted.`` / ``dll not found``
        / 连不上的描述），绝不替换成含糊的「失败」，也**绝不**替服务端编一句
        「这个邮箱不存在」—— 那句话是服务端刻意不说的。

        ⚠️⚠️ **代号对不上的答复会被丢弃**：用户在左侧列表里连点了几个邮箱时，
        :meth:`query_email` 会把旧的那次标记作废（``_query_generation += 1``）。
        旧线程仍然会跑完并送答复回来，这里按代号丢掉它 —— 否则会出现
        「点了 A 又点 B，最后显示的却是 A 的结果」这种错乱。

        Args:
            reply: 服务端答复正文。
            elapsed_text: 已格式化好的往返耗时（可能为空串）。
            generation: 这次查询属于哪一代（``None`` = 不检查，直接显示）。
        """
        # ⚠️ 控件可能已随标签页关闭被销毁，而本槽是 lambda 连的（Qt 不会自动断连）
        #    —— 迟到的答复必须直接丢掉，否则碰 status_view / 图表会抛
        #    "wrapped C/C++ object ... has been deleted"。
        if _is_deleted(self):
            return
        if generation is not None and generation != self._query_generation:
            self._log('丢弃一个已作废的查询结果（用户已经改查别的邮箱）')
            return

        text = str(reply if reply is not None else '').strip()
        # ⚠️ 日志里**不重复整条答复**（那可能很长、还会被状态栏截断成看不懂的一串）：
        #    原始答复马上就由下面的 status_view 原样显示出来，这里只记长度与耗时，
        #    用来对照「哪一次请求、回了多长」。
        self._log(f'查询响应：{len(text)} 字符'
                  f'{f" [{elapsed_text}]" if elapsed_text else ""}')

        # 原始答复区始终显示原话 + 耗时（失败时也要显示 —— 那正是最该看的时候）
        lines = [text or '(空响应)']
        if elapsed_text:
            lines.append(elapsed_text)
        self.status_view.setPlainText('\n'.join(lines))

        parsed = parse_count_reply(text)

        if parsed is None:
            self._draw_placeholder('没有可显示的数据。')
            if not text:
                self._show_status('没拿到任何答复（可能是网络中断）。', ok=False)
            elif is_user_list(text):   # ★ 原来写的是 USER_LIST_TAG，而这个名字
            #   在本模块**从未定义**（也没 import）—— 任何一次失败的查询都会在这里抛
            #   NameError，用户看到的是控制台红字而不是下面那句提示。改用已导入的
            #   is_user_list()，语义完全相同。
                # ⚠️ 只有一种情况会走到这里：服务端的动作与记号对不上了。
                #    明说出来，免得用户对着一条 "Users: ..." 的答复找不到北
                self._show_status(
                    '服务端回的是用户名单（Users:），不是查询次数统计。', ok=False)
            else:
                self._show_status(f'查询失败：{text}', ok=False)
            return

        label, values = parsed
        if not values:
            # 服务端认了这个请求，但区间里没有可画的数据
            self._draw_placeholder('区间内没有数据。')
            if label:
                self._show_status(f'查询成功，但区间内没有数据。区间：{label}',
                                  ok=False)
            else:
                self._show_status('查询成功，但区间内没有数据。', ok=False)
            return

        self._draw_counts(label, values)
        span = f'区间：{label}，' if label else ''
        self._show_status(
            f'查询成功。{span}共 {len(values)} 天，'
            f'合计 {sum(values)} 次（最多的一天 {max(values)} 次）。', ok=True)

    # ------------------------------------------------------------------
    # 绘图（交给模块内的原生 _BarChart，这里只做「数据 -> 图」的翻译）
    # ------------------------------------------------------------------

    @staticmethod
    def _tick_labels(label, indexes, n):
        """把 ``Range:`` 段换算成每个刻度的日期标签。

        ``Range:`` 段是 ``'<起> ~ <止>'``（也兼容 ``to``），拆开之后**按位置
        线性内插**即可 —— 服务端保证逐日连续不跳号，所以「第 i 根柱子」与
        「区间第 i 天」是一一对应的。

        ⚠️ 万一 ``Range:`` 段缺失或形态变了（服务端演进），就退回到纯序号标签，
        **绝不**抛异常：标签难看总比整张图画不出来好。

        Args:
            label: ``Range:`` 段的原文。
            indexes: 要标注的柱子序号。
            n: 柱子总数。

        Returns:
            list: 与 ``indexes`` 等长的标签列表。
        """
        start = end = None
        for sep in ('~', ' to '):
            if sep in label:
                head, tail = label.split(sep, 1)
                try:
                    start = datetime.datetime.strptime(
                        head.strip(), DATE_FORMAT).date()
                    end = datetime.datetime.strptime(
                        tail.strip(), DATE_FORMAT).date()
                except ValueError:
                    start = end = None
                break
        if start is None or end is None or n <= 1:
            if n <= 1:
                return [label] if label else ['1']
            return [str(i + 1) for i in indexes]
        total = (end - start).days
        if total < 0:
            return [str(i + 1) for i in indexes]
        return [(start + datetime.timedelta(
            days=round(total * i / float(n - 1)))).strftime('%m-%d')
            for i in indexes]

    @classmethod
    def _make_labels(cls, label, n):
        """为 ``n`` 根柱子生成完整的横轴标签表.

        原生 :class:`_BarChart` 需要「每根柱子一个标签」（刻度由它自己挑），
        而 :func:`parse_count_reply` 只给出区间的两端 —— 这里按天线性展开。

        ⚠️ ``Range:`` 段缺失 / 形态不对时**退回序号**，不猜日期（见
        :meth:`_tick_labels` 的说明）。

        Args:
            label: 服务端答复里的 ``Range:`` 段。
            n: 柱子总数。

        Returns:
            list: 长度为 ``n`` 的标签列表。
        """
        return cls._tick_labels(label, list(range(n)), n)

    def _draw_counts(self, label, values):
        """把每天的次数交给柱状图画出来。

        Args:
            label: 服务端答复里的 ``Range:`` 段（横轴标签的唯一来源）。
            values: 每天的次数（最早 -> 最新）。
        """
        n = len(values)
        title = '查询次数'
        if label:
            title = f'查询次数（{label}，共 {n} 天）'
        self.canvas.set_data(
            self._make_labels(label, n), values, title=title)

    def _draw_placeholder(self, message):
        """没有数据时在图上写一句话（而不是留一片空白）。

        Args:
            message: 要显示的提示文本。
        """
        self.canvas.set_placeholder(message)

    # ------------------------------------------------------------------
    # 其它
    # ------------------------------------------------------------------

    def copy_reply(self):
        """把「服务器原始答复」区里的文本复制到剪切板。"""
        try:
            QtWidgets.QApplication.clipboard().setText(
                self.status_view.toPlainText())
            self._show_status('原始答复已复制到剪切板。', ok=None)
        except Exception as err:
            self._log(f'Error (when copy reply): {err}')

    def refresh(self):
        """重新查一次（**菜单「操作 → 刷新」的接口**）。

        主窗口的 ``MainWindow.refresh`` 会 duck-typing 地调用**当前页面**的
        ``refresh()``（见 ``hasattr(current, "refresh")``），本方法就是那个接口。

        ⚠️ **只重放上一次查询**，绝不在「用户还没查过」时自动联网：主窗口在
        切标签页、执行菜单命令时都会调 ``refresh``，若在这里无条件发请求，
        页面会被动地一次次打服务端 —— 而这个接口本来就是「每次调用都真的发
        出去、不缓存」的那一类（见模块文档）。
        """
        if self._busy:
            return              # 上一次还没回来，不叠加
        if self._last_query is None:
            return              # 还没查过：什么都不做
        email, from_date, to_date = self._last_query
        # 用户可能在期间改了输入框 —— 以输入框为准，但只在它能构成一次查询时
        current = self.get_query()
        if current[0]:
            email, from_date, to_date = current
        self.email_edit.setText(email)
        self.from_edit.setText(from_date)
        self.to_edit.setText(to_date)
        self.start_query()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用（``TabWidget.close_tab``）：**不等**在飞的请求。

        ⚠️ **刻意不 ``wait()``**：每个请求最长 30 秒，在这里同步等会把「关标签」
        变成冻结界面；线程本来就没有 parent（见 :data:`_RUNNING_WORKERS`），
        因此**不会**随控件一起被销毁 —— 关标签只是让结果失去接收者，线程照旧
        跑完，然后被 :func:`_forget_worker` 摘掉。迟到的结果由 :func:`_is_deleted`
        在各槽里拦掉。

        ⚠️ 与 :meth:`closeEvent` 的分工：那个只在控件被**单独** ``close()`` 时
        触发（走标签页关闭用的是 ``deleteLater()``，**不会**触发 ``closeEvent``）
        —— 那条路径由本方法负责，两者缺一不可。
        """
        for name in ('_worker', '_prefill_worker', '_user_list_worker'):
            setattr(self, name, None)
        self._busy = False

    def closeEvent(self, event):
        """窗口关闭时等后台请求收尾，避免线程还在跑时对象被销毁。

        ⚠️ 三个线程都要等：查询（``_worker``）、取绑定邮箱（``_prefill_worker``）、
        取名单（``_user_list_worker``）。**漏掉任何一个**，那个线程就会在解释器
        退出时还活着，进程带着 ``QThread: Destroyed while thread is still
        running`` **崩在退出阶段**（真踩过）。

        ⚠️ **本方法只覆盖「控件被单独 close()」这一条路径**（例如直接运行
        :func:`test_1`）：走**标签页关闭**（``TabWidget.close_tab``）用的是
        ``deleteLater()``，**不发** ``closeEvent``，那条路径由
        :meth:`cleanup_before_tab_close` 负责。``wait(3000)`` 也兜不住长请求（最长 30 秒）
        —— 所以线程本身没有 parent、能活到自然结束。
        """
        for worker in (self._worker, self._prefill_worker,
                       self._user_list_worker):
            if worker is not None and worker.isRunning():
                worker.wait(3000)
        event.accept()


class _PrefillWorker(QtCore.QThread):
    """在后台线程里取「本机已绑定的邮箱」（**绝不碰界面**）。

    取邮箱要联网（``web_license.check``，最长 30 秒），放进 UI 线程会让「打开
    本页面」直接卡住。取不到就发空串 —— 那是常态（没联网 / 没绑定）。

    Attributes:
        sig_done: 信号，携带邮箱（可能为空串）。
    """

    sig_done = QtCore.pyqtSignal(str)

    def __init__(self, owner=None, parent=None):
        """初始化。

        Args:
            owner: 提供 :meth:`CheckCountView._prefill_email` 的控件。
                ⚠️ 这只是**取值用的引用**，不是 Qt parent。
            parent: Qt 父对象。⚠️ 正常调用应当**留空** —— 线程的 parent 设成控件
                会让它在控件被销毁时连带析构 = 进程崩溃（见
                :data:`_RUNNING_WORKERS`）。
        """
        super(_PrefillWorker, self).__init__(parent)
        self._owner = owner
        self.setObjectName('CheckCountViewPrefillWorker')

    def run(self):
        """线程体：取邮箱并发回主线程（任何异常都变成空串）。"""
        try:
            email = self._owner._prefill_email()
        except Exception as err:      # 防御性：正常路径不会触发
            print(f'Error (when prefill email): {err}')
            email = ''
        self.sig_done.emit(str(email or ''))


class _UserListWorker(QtCore.QThread):
    """在后台线程里取「服务端用户名单」（**绝不碰界面**）。

    ⚠️⚠️ **必须在后台线程**：``user_list`` **不做缓存、每次调用都真的发出去**，
    单次最长阻塞 30 秒。放进 UI 线程的话，
    「点开授权记录」会直接卡住 —— 而本控件的要求正是**立即显示**。

    ⚠️ **非管理员拿到的是 ``Not permitted.``**（HTTP 200 的**正常业务答复**），
    所以这里**不发错误信号**：结果一律通过 :attr:`sig_done` 交回文本，
    由主线程用 :func:`parse_user_list` 判定；判不出就静默忽略。

    ⚠️ 与 :class:`_PrefillWorker` 分开成两个线程，是因为两者**失败互不影响**：
    取绑定邮箱失败不该连带把名单也丢掉，反之亦然。

    Attributes:
        sig_done: 信号，携带服务端答复正文（可能是失败文案）。
    """

    sig_done = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象。
        """
        super(_UserListWorker, self).__init__(parent)
        self.setObjectName('CheckCountViewUserListWorker')

    def run(self):
        """线程体：取名单并发回主线程（任何异常都变成一句文本）。"""
        try:
            # ★ v3.35：优先要「邮箱 + 姓名」。⚠️ **必须判断答复**再决定是否退回旧
            #   动作：老服务端不认识 ``user_list_detail``，会把它当成一次许可查询
            #   回一句 ``Yes``（服务端的宽松兜底）—— 那时只有旧动作能拿到名单。
            reply = web_license.user_list_detail()
            if not is_user_list_detail(reply):
                # ⚠️ 实测偶发**空答复**（2026-10-18：十次里约一两次，串行并发都遇到，
                #    24 次连打又完全不复现 —— 是链路/SDK 层的偶发，不是稳定复现的缺陷）。
                #    列表是**装饰**，不值得为它失败一次就退化成只有邮箱，所以重试一次。
                retry = web_license.user_list_detail()
                reply = retry if is_user_list_detail(retry) else web_license.user_list()
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：user_list 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        self.sig_done.emit(text)


def _quiet(widget):
    """让一个测试用的控件**不许联网**（自检专用）.

    ⚠️ **必须在 ``show()`` 之前调**：否则 ``showEvent`` 会起后台查询 / 取名单纯程，
    那些线程在解释器退出时还活着，进程会带着
    ``QThread: Destroyed while thread is still running`` **崩在退出阶段**
    （真踩过）。

    Args:
        widget: :class:`CheckCountView` 实例。

    Returns:
        CheckCountView: 同一个对象（便于链式调用）。
    """
    widget._auto_checked = True     # 关掉「首次显示自动查询」
    return widget


def test_1():
    """交互式查看本控件（会真的联网查询）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = CheckCountView()
    w.resize(900, 640)
    w.show()
    sys.exit(app.exec())


def test_2():
    """离线自检：解析 + 标签 + 柱状图几何（不联网、不起交互界面）."""
    import os
    import sys

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QtWidgets.QApplication(sys.argv)

    cases = [
        ('Count: 3 0 5 | Email: a@b.c | Range: 2026-10-03 ~ 2026-10-05',
         ('2026-10-03 ~ 2026-10-05', [3, 0, 5])),
        ('count: 1', ('', [1])),            # 记号大小写不敏感；没有说明段也能解析
        ('Count: | Range: 2026-10-05 ~ 2026-10-05',
         ('2026-10-05 ~ 2026-10-05', [])),
        ('Not permitted.', None),
        ('Users: 2 | List: a@b.c; d@e.f', None),   # ⚠️ 绝不能与 Count: 串味
        ('dll not found', None),
        ('', None),
        (None, None),
    ]
    for reply, expect in cases:
        got = parse_count_reply(reply)
        flag = 'ok  ' if got == expect else 'FAIL'
        print(f'{flag} {reply!r} -> {got!r} (expect {expect!r})')

    # 标签展开：30 天区间的首尾必须落在区间的两端
    labels = CheckCountView._make_labels('2026-09-06 ~ 2026-10-05', 30)
    print('labels[0] =', labels[0], ' labels[-1] =', labels[-1],
          ' len =', len(labels))
    assert labels[0] == '09-06' and labels[-1] == '10-05'

    # 柱状图几何：每根柱子都能被点中
    # ⚠️ ``_quiet`` 必须在 ``show()`` 之前：否则会起真实的后台查询线程
    w = _quiet(CheckCountView(email='a@b.c'))
    w.resize(900, 600)
    w.show()
    app.processEvents()
    w._on_reply('Count: ' + ' '.join(str(v) for v in range(1, 31))
                + ' | Range: 2026-09-06 ~ 2026-10-05', '')
    app.processEvents()
    chart = w.canvas
    plot = chart._plot_rect()
    slot = plot.width() / 30.0
    miss = 0
    for i in range(30):
        x = int(plot.left() + i * slot + slot / 2)
        if chart._index_at(QtCore.QPoint(x, plot.bottom() - 5)) != i:
            miss += 1
    print('30 根柱子点击命中失败数 =', miss, '(应为 0)')
    assert miss == 0
    print('柱数 =', len(chart._values), ' 选中 =', chart._selected_index)

    # ---- 左侧邮箱列表 ----
    print()
    ulist_cases = [
        # Dropped/Truncated 只在非零时出现 -> 段数不固定，别假设
        ('Users: 3 | List: a@b.c; d@e.f; g@h.i', ['a@b.c', 'd@e.f', 'g@h.i']),
        ('Users: 2 | List: a@b.c; d@e.f | Dropped: 1', ['a@b.c', 'd@e.f']),
        ('Users: 1 | List: a@b.c | Truncated: 9', ['a@b.c']),
        ('Users: 0 | List:', []),               # 拿到了，但名单是空的
        ('Users: 1 | List: not-an-email', []),  # 脏数据被过滤
        ('The user list is empty.', None),
        ('Not permitted.', None),               # 非管理员：正常业务答复
        ('The user list is not available.', None),
        ('The user list is malformed.', None),
        ('Service temporarily unavailable', None),
        # ⚠️ 绝不能与 Count: 串味（两者都是 6 字符带冒号）
        ('Count: 3 0 5 | Range: 2026-10-03 ~ 2026-10-05', None),
        ('dll not found', None),
        ('', None),
        (None, None),
    ]
    for reply, expect in ulist_cases:
        got = parse_user_list(reply)
        flag = 'ok  ' if got == expect else 'FAIL'
        print(f'{flag} parse_user_list {str(reply)[:40]!r} -> {got!r}')
        assert got == expect, (reply, got, expect)
    assert merge_emails(['A@x.com', 'a@X.com'], ['b@y.org']) == [
        'A@x.com', 'b@y.org']
    assert not is_user_list('Count: 1')
    print('merge_emails / is_user_list: OK')

    # 列表：空 -> 整块隐藏；有名单 -> 显示
    wl = _quiet(CheckCountView())
    wl.resize(1000, 600)
    wl.show()
    app.processEvents()
    wl._bound_email = None
    wl._server_emails = None
    wl._refresh_email_list()
    assert not wl.email_list_panel.isVisible(), '无数据时列表该隐藏'
    print('无数据 -> 列表隐藏: OK')

    wl._on_user_list('Users: 2 | List: x@a.cn; y@b.cn')
    app.processEvents()
    assert wl.email_list_panel.isVisible()
    assert [wl.email_list.item(i).text()
            for i in range(wl.email_list.count())] == ['x@a.cn', 'y@b.cn']
    print('名单到达 -> 列表显示: OK')

    # 非管理员 -> 依旧隐藏（界面与「没这功能」时一致）
    wl._on_user_list('Not permitted.')
    app.processEvents()
    assert not wl.email_list_panel.isVisible()
    print('非管理员 -> 列表隐藏: OK')

    # ⚠️ 填充列表**不许**触发查询（打开页面不能自己查第一个邮箱）
    fired = []
    wl.start_query = lambda: fired.append(wl.email_edit.text())
    wl._on_user_list('Users: 3 | List: a@x.cn; b@y.cn; c@z.cn')
    app.processEvents()
    assert not fired, f'填充列表时擅自查询了: {fired}'
    print('填充列表不触发查询: OK')

    # 点击列表项 -> 查询该邮箱
    fired.clear()
    wl._on_email_item_clicked(wl.email_list.item(1))
    assert fired == ['b@y.cn'], fired
    print('点击列表项 -> 查询:', fired)

    # 版式：套了左侧列表之后，柱状图高度与原来完全一致
    wl.resize(1000, 700)
    app.processEvents()
    assert wl.canvas.height() == 520, wl.canvas.height()
    assert wl._right_panel.x() == LIST_WIDTH, wl._right_panel.x()
    print('版式未被左侧列表破坏（canvas=520, 右侧 x=200）: OK')

    print('OK')


if __name__ == '__main__':
    import sys
    if '--self-test' in sys.argv:
        test_2()
    else:
        test_1()


if __name__ == '__main__':
    import sys
    if '--self-test' in sys.argv:
        test_2()
    else:
        test_1()

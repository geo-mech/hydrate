"""用户反馈工具：把一段文本提交给作者（``web_license.feedback``）.

界面只剩「一个输入框 + 一个按钮」::

    web_license.feedback(text)     # 机器码由 C++ 侧自己算，不收参数

姓名 / 单位 / 邮箱在注册时就已经提交过，不必再问一遍。

三条必须守住的契约
------------------

1. **成功记号是 ``Succeed``，不是 ``Yes``** —— 判定一律用 :func:`is_succeed`，
   绝不能用 ``is_yes``（``Succeed`` 不以 ``yes`` 开头，会把成功读成失败）。
2. **限流那条答复要原样显示**：答复里带着**精确的剩余等待时间**，直接给用户看，
   别自己编一句「稍后再试」。
3. **超长是「截断后成功」**：服务端截断后仍然算成功。
   ⚠️ **本地绝不做截断** —— 服务端要按原文算「被截掉多少」并回报，本地先截一刀
   会让那个数字撒谎。同理界面上的字数提示只是**提示**，不是硬限制。

耗时的活在线程里
----------------

一次提交是一次真实的网络往返（最长 60 秒超时），所以提交走
:class:`FeedbackWorker`（QThread），提交期间按钮禁用；结果经信号回到主线程再显示。
**绝不**在界面线程里直接调 ``web_license.feedback``。

为什么【没有】自动保存草稿
--------------------------

早先版本把输入内容逐键写进一个临时文件、重开本页自动恢复。**已彻底删除**：那份
草稿只有**一个槽位**，而反馈的来源可能有多个（用户手写的、别处用
``gui.show_feedback(text=...)`` 塞进来的现场信息），它们会互相覆盖。所以本控件
现在**不持久化任何输入**：关掉页面即丢弃。

要留下来的内容，走**显式的**文件命令（菜单「文件 → 导入 / 保存 / 导出」）：

====================  ========================================================
``import_data()``     从 ``.txt`` 读入正文（菜单「文件 → 导入」）
``need_save()``       正文非空就返回 True（菜单据此点亮/置灰「保存」）
``save_file()``       存到上次记住的路径，没有则弹框询问（「文件 → 保存」）
``export_data()``     另存为（「文件 → 导出」）
====================  ========================================================

⚠️ 这四个方法是**给主窗口的菜单按名字调的**，所以名字与签名不能改。

「反馈版本号」按钮（★ 仅管理员可见）
------------------------------------

底部次要按钮里还有一个 **「反馈版本号」**：把**本机内核版本号**
（``core.version``，6 位 ``yymmdd``）拼成一句 ``LatestVersion: <6 位数字>`` 提交。

``LatestVersion`` 是**服务端自己用的记号**（客户端侧的解析见
``zmlx/ui/widget/license_button.py`` 的 ``LATEST_TAG``）：服务端在许可答复里用它
报告「最新版本」，而本按钮的用途就是**让管理员把这个数字改掉** —— 改完之后所有
客户端下次查询就会看到新数字，于是被提示更新。

⚠️ **服务端的实现不在本仓库**（``projects/system/`` 是**客户端**用的通信库），
所以「提交这句 ⇒ 服务端改最新版本」这条链路**无法在本仓库内自证**。因此命令文本
只由 :data:`VERSION_CMD_LABEL` **一处**定义 —— 若服务端认的是别的写法，改那一个
常量即可，界面与线程逻辑都不用动。

⚠️⚠️ **它只在确认本机是管理员时才显示**（张老师的原话：「仅仅在确定为管理员的
时候显示」）。判据**复用** :func:`zmlx.ui.utils.lic_utils.is_admin_by_web_license`
（= 服务端答复里的绑定邮箱等于 ``lic_utils.ADMIN_EMAIL``），本模块**不自己写一份判据**。
⚠️ **不要**改用 ``lic.is_admin`` —— 那个是**本机 Windows 管理员**权限，换台机器
就失效，与服务端的「管理员」完全是两件事。

★ 判定要**联网**（最长 60 秒），所以放在**本页首次显示时**（:meth:`FeedbackTool.showEvent`
—— 这就是「适当时刻」）的后台线程里跑（:class:`AdminCheckWorker`），拿到结论再决定
按钮露不露面 —— 界面线程一次都不等。

⚠️ 「只在管理员时显示」是**体验**上的照顾（免得点一个必然失败的按钮），
**不是**安全边界：真正的门在服务端。所以这里判错方向的代价只是「少显示一个按钮」。

版式约定（与 ``license_register.py`` 同一套）
---------------------------------------------

**不写 ``color`` / ``background``**：本程序会加载用户可编辑的
``zml_window_style.qss``，并且有暗色模式。需要「次要文字」就用
``setEnabled(False)``，需要边框就用 ``palette(mid)``（见 :data:`BANNER_QSS`）。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-09-28: 改走服务端 feedback（不再直连 SMTP 发邮件）
Modified by DeepSeek, 2026-09-28: 删除自动保存（单槽位草稿会让多来源反馈互相覆盖）
Modified by DeepSeek, 2026-10-02: 该接口随网络功能迁到 web_license.feedback
Modified by WorkBuddy, 2026-10-16: 新增「反馈版本号」按钮（仅管理员可见）
"""

import os

from zmlx.exts import web_license
from zmlx.system import make_parent, read_text, write_text
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

#: 界面上的字数提示阈值（**不是**硬限制）。这里取 2000 字符只是提醒用户
#: 「写这么长就够了」；真正的上限由服务端说了算，所以本地永不截断。
SOFT_LIMIT = 2000

#: 少于这个长度就不发（服务端只拦「空 / 全空白」，但一两个字的反馈没法处理）。
MIN_LENGTH = 5

#: 「反馈版本号」那条命令的**标签**（★ 服务端认的记号，见模块文档）。
#:
#: ⚠️ **只此一处定义**，命令文本就是 ``f'{VERSION_CMD_LABEL}: {版本号}'``。
#: 与 ``license_button.py`` 的 ``LATEST_TAG`` 是同一个记号的两端：那边**读**
#: 服务端报出来的最新版本，这边**写**进去。刻意不 import 那个常量 —— 两个控件
#: 之间没有别的耦合，为四个字符的字符串建一条依赖不划算；而且 ``license_button``
#: 会连带 import ``license_register``，容易绕进环形 import。
VERSION_CMD_LABEL = 'LatestVersion'

#: 正在后台跑的 :class:`FeedbackWorker`（模块级强引用）。
#:
#: ⚠️ **线程的 parent 绝不能是本控件**：标签页关闭时控件会被
#: ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，parent 是本控件的线程会
#: **跟着一起被析构**；而 Qt 规定「正在运行的 QThread 不能被销毁」，提交还没
#: 回来时就会直接 abort::
#:
#:     QThread: Destroyed while thread is still running
#:
#: 这是**进程级崩溃**，不是异常。控件里的 ``closeEvent`` 兜不住 —— ``close_tab``
#: 走 ``deleteLater()``，**根本不发** ``closeEvent``（那条路径由
#: :meth:`FeedbackTool.cleanup_before_tab_close` 负责）。
#:
#: 挂在这里线程一定能跑完；控件销毁后槽自动断连（槽都是绑定方法），
#: 迟到结果被安全丢弃。
_RUNNING_WORKERS = []


def _forget_worker(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）。"""
    try:
        _RUNNING_WORKERS.remove(worker)
    except ValueError:
        pass


def is_succeed(text) -> bool:
    """判断 ``web_license.feedback`` 的答复是否为「反馈已收下」。

    判据：去掉首尾空白后，**前 7 个字符**忽略大小写等于 ``succeed``。超长时
    服务端会在成功记号后面追加一段说明，所以不能要求整串相等。

    ⚠️ 本判定**本地实现**（``zmlx.exts._lic`` 不提供判定函数），与
    ``zmlx.ui.utils.lic_utils`` 里的 ``is_sent`` /
    ``is_bound`` 是同一条纪律。

    ⚠️⚠️ **不要改用 ``is_yes``**：反馈的成功记号是 ``Succeed``，不以 ``yes``
    开头，``is_yes`` 会把**成功读成失败**。两个动作的记号是**两套**。

    ⚠️ 刻意**宽松**（``Succeedingly`` 也算成功），安全性来自同一条纪律：
    **任何失败文案都不以 ``succeed`` 开头**。

    Args:
        text: 答复（任意对象，会被转成字符串）。

    Returns:
        bool: 反馈已收下返回 True。
    """
    return str(text if text is not None else '').strip()[:7].lower() == 'succeed'


def version_command_text() -> str:
    """把**本机内核版本号**拼成「反馈版本号」的命令文本（纯函数）.

    ★ 版本号取自**内核**（``core.version``，6 位 ``yymmdd``）—— 它就是「关于」页
    「版本号」那一行显示的值，也正是服务端 ``LatestVersion`` 要的形态
    （与 ``license_button._get_local_version()`` 取的是同一个值）。

    ⚠️ **不是** ``zmlx.__version__``：那是 ``1.10.x`` 这种**包**版本，位数与形态
    都不对 —— 发过去只会被服务端当一条普通反馈收下（命令没生效，还白占一次反馈）。

    ⚠️ 本地判一道形态（6 位数字）**只是为了给出一句人话**，而不是把注定失败的请求
    发出去；真正的合法性由服务端裁断。

    Returns:
        str: 形如 ``LatestVersion: 261010``；**拿不到合法版本号时返回空串**
        （缺少内核库、或版本号不是 6 位数字），调用方据此拒绝提交。
    """
    try:
        from zmlx import core

        if not core.has_dll():
            return ''
        value = core.version
    except Exception:
        return ''
    # ⚠️ 只认 int：``core.version`` 是 int（``_dll.py`` 的 property）；万一将来
    #    变成别的东西，宁可返回空串（按钮报一句「没拿到版本号」）也不要瞎拼。
    if not isinstance(value, int) or not (100000 <= value <= 999999):
        return ''
    return f'{VERSION_CMD_LABEL}: {value}'


MARGIN = 12
GAP = 8
BUTTON_HEIGHT = 34

#: 状态下方的提示条样式：**只含边框与内边距，没有任何 color / background**。
#: 颜色由当前主题的调色板决定，因此亮色与暗色都能正常显示。
BANNER_QSS = 'border: 1px solid palette(mid); border-radius: 6px;'


class FeedbackWorker(QtCore.QThread):
    """在后台线程里提交一次反馈（**绝不碰界面**）。

    Qt 的规则是「界面只能在主线程碰」，所以线程里只发请求，结果通过信号回主线程。

    ⚠️ 异常绝不允许逃出 :meth:`run`：真逃出去的话线程会静默死掉、信号永不发出，
    按钮就永远停在禁用状态 —— 看起来像程序卡死。（``web_license.feedback`` 按契约
    不抛异常，这里只是防御。）

    Attributes:
        sig_done: 信号，携带服务端答复正文。
    """

    sig_done = QtCore.pyqtSignal(str)

    def __init__(self, text, parent=None):
        """初始化。

        Args:
            text: 反馈正文（原样发出，不截断）。
            parent: Qt 父对象。
        """
        super(FeedbackWorker, self).__init__(parent)
        self._text = text
        self.setObjectName('FeedbackWorker')

    def run(self):
        """线程体：提交反馈并发回答复（任何异常都要变成一句文本）。"""
        try:
            reply = web_license.feedback(self._text)
        except Exception as err:
            reply = f'提交反馈时出错：{type(err).__name__}: {err}'
        self.sig_done.emit(str(reply if reply is not None else ''))


class AdminCheckWorker(QtCore.QThread):
    """在后台线程里判定「本机是不是**服务端管理员**」（**绝不碰界面**）。

    ★ 判据**只有一处实现**：:func:`zmlx.ui.utils.lic_utils.is_admin_by_web_license`
    （= ``web_license.check`` 答复里的绑定邮箱等于 ``lic_utils.ADMIN_EMAIL``）。
    ⚠️ **不要**改用它旁边的 ``lic.is_admin`` —— 那个是**本机 Windows 管理员**
    权限，换台机器就失效，与服务端的「管理员」是两件事。

    ⚠️ 判定要**联网**（最长 60 秒），所以必须在本线程里跑；结论经信号回主线程，
    由界面决定「反馈版本号」按钮露不露面。

    Attributes:
        sig_result: 信号，携带判定结论（``True`` = 管理员）。
    """

    sig_result = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象（⚠️ 调用方**留空**，理由见 :data:`_RUNNING_WORKERS`）。
        """
        super(AdminCheckWorker, self).__init__(parent)
        self.setObjectName('AdminCheckWorker')

    def run(self):
        """线程体：判定管理员并发回结论（任何异常都算「不是」）。"""
        try:
            # ⚠️ 延迟 import：``about`` 会连带 import ``license_register``，两者与
            #    本模块同在 ``ui.widget`` 包里 —— 放模块顶层会绕进环形 import
            #    （``about.py`` 自己那几处也是这个写法）。
            from zmlx.ui.utils.lic_utils import is_admin_by_web_license

            result = bool(is_admin_by_web_license())
        except Exception:
            # 判不出来（没网 / 没授权 / 没 DLL）就**当作不是**：失败方向安全 ——
            # 按钮本来就是给管理员看的，少显示一个不会有任何损失。
            result = False
        self.sig_result.emit(result)


class FeedbackTool(QtWidgets.QWidget):
    """反馈控件：一个多行输入框 + 一个「提交反馈」按钮。

    提交后按服务端答复分三种收尾（见 :meth:`_on_done`）：成功 / 限流 / 失败。
    成功时清空输入；失败时**保留**内容，让用户可以直接重试。

    ⚠️ **不持久化任何输入**（详见模块文档「为什么没有自动保存草稿」）：关掉本页
    即丢弃。反馈的来源可能有多个（用户手写 + ``gui.show_feedback(text=...)``
    塞进来的现场信息），单槽位的草稿会让它们互相覆盖。
    """

    def __init__(self, parent=None):
        super(FeedbackTool, self).__init__(parent)
        self._worker = None       # 后台提交线程（持有引用，防被 GC）
        self._busy = False        # 有请求在飞：按钮禁用，防连点
        # 「是不是管理员」的判定状态：只在**首次显示**本页时判一次（见 showEvent）
        self._admin_worker = None       # 后台判定线程（持有引用，防被 GC）
        self._admin_checked = False     # 起过判定线程了吗（不重复判）
        # 在飞的那次提交是「反馈版本号」还是普通反馈：决定答复措辞，
        # 以及**要不要清空输入框**（见 _on_done）
        self._reporting_version = False
        # 「保存」的目标路径：由导入或上次保存记住；空 = 还没定，保存时弹框问
        self.filename = None

        self.setWindowTitle('问题反馈')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(GAP)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_status_banner())
        layout.addWidget(self._separator())
        layout.addWidget(self._build_editor(), 1)
        layout.addWidget(self._build_buttons())

        self._update_counter()
        self._update_buttons()

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------

    def _build_header(self):
        """顶部标题区（取代原先 QGroupBox 的标题）。"""
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title = QtWidgets.QLabel('反馈')
        font = title.font()
        font.setPointSize(font.pointSize() + 5)     # 相对放大，不写死磅值
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        hint = QtWidgets.QLabel(
            '写下遇到的问题或建议，直接提交给作者。\n'
            '反馈会记在本机所属的登录邮箱下，无需再填姓名与联系方式。')
        hint.setWordWrap(True)
        hint.setEnabled(False)      # 置灰跟随主题，不写死颜色
        layout.addWidget(hint)
        return box

    def _build_status_banner(self):
        """顶部「一句话结论」提示条（提交后在这里给结论）。"""
        self.status_label = QtWidgets.QLabel('')
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(BANNER_QSS)
        self.status_label.setContentsMargins(GAP, GAP, GAP, GAP)
        self.status_label.hide()    # 还没提交过：不占地方
        return self.status_label

    def _separator(self):
        """一条 1px 水平细线（用留白 + 细线划分区域，不画分组框）。"""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        return line

    def _build_editor(self):
        """反馈内容输入区（自适应高度）。

        ⚠️ **不设** ``setMaxLength`` 之类：本地截断会让服务端回报的 original
        字节数撒谎（见模块文档第 3 条）。字数提示只是提示。
        """
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GAP)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(GAP)
        label = QtWidgets.QLabel('反馈内容')
        row.addWidget(label)
        row.addStretch(1)
        self.counter_label = QtWidgets.QLabel('')
        self.counter_label.setEnabled(False)     # 次要文字：置灰，不写死颜色
        row.addWidget(self.counter_label)
        layout.addLayout(row)

        self.feedback_edit = QtWidgets.QTextEdit()
        self.feedback_edit.setPlaceholderText(
            '请详细描述您遇到的问题或建议。\n'
            '例如：做了什么操作、期望的结果、实际看到的结果、报错信息等。')
        self.feedback_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.feedback_edit, 1)
        return box

    def _build_buttons(self):
        """底部按钮区：主按钮「提交反馈」通栏，次要动作放右边。"""
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(GAP)

        self.submit_button = QtWidgets.QPushButton('提交反馈')
        self.submit_button.setMinimumHeight(BUTTON_HEIGHT)
        self.submit_button.setDefault(True)
        self.submit_button.setToolTip(
            '把上面的内容提交给作者。\n'
            '提交过于频繁时服务端会回一句「请稍后再试」，并告诉你还要等多少秒。')
        self.submit_button.clicked.connect(self.submit_feedback)
        layout.addWidget(self.submit_button)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(GAP)
        row.addStretch(1)
        self.clear_button = QtWidgets.QPushButton('清空')
        self.clear_button.setFlat(True)      # 扁平 = 视觉上的次级按钮
        self.clear_button.setToolTip('清空输入框')
        self.clear_button.clicked.connect(self.clear_input)
        row.addWidget(self.clear_button)

        # ★ 「反馈记录」：**打开另一个控件**（「帮助 → 查询 → 反馈记录」那一页），
        #    不是在本页做查询 —— 本页只管**提交**，查看归那一页。
        #
        # ⚠️ **走 GUI 命令而不是直接 import 那个控件类**：``gui.show_feedbacks_view()``
        #    正是菜单「帮助 → 查询 → 反馈记录」执行的那一句（登记在
        #    ``extra_setups/license_query.py`` 的 ``setup_ui`` 里，菜单项的 ``slot``
        #    就是它）。这样「怎么打开 / 开在哪 / 复用已有标签页」全部由那一个函数
        #    决定，本控件不重复实现一遍；而且与 ``license_button`` /
        #    ``readme_browser`` 里 ``gui.show_reg_tool()`` 的写法**完全一致**。
        #    ⚠️ 若改成直接 ``FeedbacksView(...)`` 自己造一个窗口，就会绕过
        #    ``get_widget`` 的「已开则切过去」逻辑，点两次会出现两个页面。
        #
        # ⚠️ **无头模式自动 no-op**（``gui.*`` 在 ``--no-gui`` 下都是空操作），
        #    所以这里不必判 ``gui.exists()``。
        self.query_button = QtWidgets.QPushButton('反馈记录')
        self.query_button.setFlat(True)
        self.query_button.setToolTip(
            '打开「反馈记录」页面：查看本机（或管理员指定邮箱）已提交的反馈内容。')
        self.query_button.clicked.connect(
            lambda: gui.show_feedbacks_view())
        row.addWidget(self.query_button)

        # ★★ 「反馈版本号」：把本机内核版本号作为命令提交给服务端
        #    （见模块文档「「反馈版本号」按钮」一节）。
        #    ⚠️⚠️ **只在确认本机是管理员时才显示** —— 所以这里建好就 ``hide()``，
        #    等 :meth:`_on_admin_checked` 拿到结论再 ``show()``。
        #    ⚠️ 刻意**先建好、立刻藏**（而不是等确认了再 addWidget）：按钮的**位置**
        #    由布局决定，一次定好就不会因为「晚一步出现」把别的按钮挤来挤去。
        self.version_button = QtWidgets.QPushButton('反馈版本号')
        self.version_button.setFlat(True)       # 扁平 = 与「清空」「反馈记录」同级的次要按钮
        self.version_button.setToolTip(
            '把本机版本号报告给服务器（仅管理员）。\n'
            '服务器会把它当作「最新版本」提示，所有客户端查询时都会看到这个数字。')
        self.version_button.clicked.connect(self.report_version)
        self.version_button.hide()
        row.addWidget(self.version_button)

        layout.addLayout(row)
        return box

    # ------------------------------------------------------------------
    # 状态提示
    # ------------------------------------------------------------------

    def _show_status(self, text, ok=None):
        """在顶部提示条里显示一句话结论。

        Args:
            text: 结论文本（可以是服务端原话）。
            ok: ``True`` 成功 / ``False`` 失败 / ``None`` 中性（只是提示）。
                ⚠️ 只用来决定**是否显示**这条提示的背景，不写死颜色。
        """
        text = str(text or '').strip()
        if not text:
            self.status_label.hide()
            return
        self.status_label.setText(text)
        # 不写颜色：用「置灰与否」表达次要信息，主色由主题给
        self.status_label.setEnabled(ok is not False)
        self.status_label.show()

    def _log(self, message):
        """往标准输出记一行（排错用）。

        ⚠️ **必须兜住异常**：Windows 控制台默认是 GBK，装不下一些符号
        （真踩过：UnicodeEncodeError 直接把控件构造打断）。
        """
        try:
            print(message)
        except Exception:
            pass

    def _update_counter(self):
        """刷新右下角的字数提示（**只是提示**，不是硬限制）."""
        n = len(self.feedback_edit.toPlainText())
        self.counter_label.setText(f'{n} / {SOFT_LIMIT} 字符（超长由服务器截断）')

    def _update_buttons(self):
        """按「是否正在提交」刷新按钮可用性。"""
        idle = not self._busy
        self.submit_button.setEnabled(idle)
        self.clear_button.setEnabled(idle)
        # ⚠️ 只管「可用性」，**不管可见性**：本按钮露不露面只由「是不是管理员」
        #    决定（见 :meth:`_on_admin_checked`），与忙不忙无关。
        self.version_button.setEnabled(idle)

    def _on_text_changed(self):
        """输入变化：刷新字数提示 + 让主窗口重算菜单可用性.

        ⚠️ **必须通知主窗口**：菜单「文件 → 保存」的灰/亮由 ``need_save()`` 决定，
        而那个回调**只在主窗口调** ``refresh_action()`` **时才重新求值**（切标签页、
        执行完菜单命令时才会调）。输入框里敲字本身不触发它 —— 不通知的话，
        「保存」会一直灰着，直到用户碰巧切一次标签页（真踩过）。
        """
        self._update_counter()
        # 无 GUI 时 gui.command 静默返回 None，可以放心调
        gui.refresh_action()

    def clear_input(self):
        """清空输入框。"""
        self.feedback_edit.clear()      # 会触发 _on_text_changed -> 刷新字数
        self._show_status('')

    def get_text(self):
        """返回输入框里的反馈正文（未去首尾空白）。"""
        return self.feedback_edit.toPlainText()

    def set_text(self, text):
        """设置输入框里的反馈正文（预先填好一段内容）。

        用途：别的功能发现异常时，可以把自己收集到的信息（例如出错时的操作、
        版本、日志片段）先塞进来，用户只需要补充两句就能提交 —— 这也是
        ``MainWindow.show_feedback(text=...)`` 的落点。

        ⚠️ **本方法会无条件覆盖输入框**。调用方必须自己保证「现在覆盖是安全的」：
        ``show_feedback`` 只在**新建控件**时（``init``）调它，控件已存在时就不调
        —— 那里面可能是**用户正在写的东西**，为了塞一段新文本而覆盖掉，比
        「这次没预填上」糟糕得多。别处的调用请同样谨慎（例如只在该输入框为空时调）。

        Args:
            text: 要填进输入框的文本；``None`` 或空串等同于清空。
        """
        self.feedback_edit.setPlainText(
            '' if text is None else str(text))
        # setPlainText 只在内容真的变了时才发 textChanged；这里再显式刷一次，
        # 保证字数提示与菜单可用性一定跟得上（本控件不落盘，没有草稿要同步）
        self._update_counter()
        gui.refresh_action()
        self._show_status('')       # 换内容了：上一轮的结论不再适用
        self.feedback_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.feedback_edit.setFocus()

    # ------------------------------------------------------------------
    # 文件命令（菜单「文件 → 导入 / 保存 / 导出」按名字调用）
    # ------------------------------------------------------------------

    def import_data(self):
        """从文本文件读入反馈正文（菜单「文件 → 导入」）.

        ⚠️ 会**覆盖**当前输入框（与 :meth:`set_text` 同一取舍）—— 菜单是用户
        主动点的，覆盖是他自己的决定，不需要再拦一道。
        """
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '导入反馈文本', os.getcwd(), '文本文件 (*.txt);;所有文件 (*)')
        if not fname:
            return
        self.set_text(read_text(path=fname, encoding='utf-8'))
        # 记住路径：接着按「保存」应当写回同一个文件，而不是再问一遍
        self.filename = fname
        self._show_status(f'已从 {os.path.basename(fname)} 导入。', ok=None)

    def need_save(self):
        """「保存」是否可用（主窗口据此点亮/置灰菜单项）.

        判据只有一条：**正文非空**。本控件不跟踪「改过没有」—— 它没有自动保存，
        每次保存都是用户显式点的，多问一句「真的要保存吗」只会添乱。

        Returns:
            bool: 正文非空返回 True。
        """
        return len(self.get_text().strip()) > 0

    def save_file(self):
        """保存正文到文件（菜单「文件 → 保存」，关闭标签页时也会被调）.

        路径策略：**优先写回上次那个文件**（导入或上次保存记住的），没有才弹框
        询问 —— 与 ``TextFileEdit`` 的「Ctrl+S 直接落盘」一致，避免每次保存都
        弹一次对话框。

        ⚠️ **没有内容就直接返回，什么都不做**。关标签页那条路已经会先问
        :meth:`need_save`（见 ``TabWidget.close_tab``），但菜单「文件 → 保存」
        与本方法都可能被别处直接调用，所以这里再判一道 —— 空内容写出去只会得到
        一个空文件，没有任何意义。

        Returns:
            str: 实际写入的路径；没有内容 / 用户取消 / 失败时返回 ``None``。
        """
        if not self.need_save():
            return None
        fname = self.filename
        if not fname:
            fname = self._ask_save_name()
            if not fname:
                return None
        try:
            write_text(path=make_parent(fname), text=self.get_text(),
                       encoding='utf-8')
        except Exception as err:
            self._show_status(f'保存失败：{err}', ok=False)
            return None
        self.filename = fname
        self._show_status(f'已保存到 {fname}', ok=None)
        return fname

    def export_data(self):
        """另存为（菜单「文件 → 导出」）.

        与 :meth:`save_file` 的差别只有一条：**每次都弹框**问路径，且**不改**
        :attr:`filename` —— 「导出」是「拷一份到别处」，不该把「保存」的目标
        路径也带走。

        Returns:
            str: 实际写入的路径；用户取消或失败时返回 ``None``。
        """
        fname = self._ask_save_name()
        if not fname:
            return None
        try:
            write_text(path=make_parent(fname), text=self.get_text(),
                       encoding='utf-8')
        except Exception as err:
            self._show_status(f'导出失败：{err}', ok=False)
            return None
        self._show_status(f'已导出到 {fname}', ok=None)
        return fname

    def _ask_save_name(self):
        """弹框问保存路径（默认 ``feedback.txt``）.

        Returns:
            str: 用户选定的路径；取消时返回空串。
        """
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '保存反馈文本',
            self.filename or os.path.join(os.getcwd(), 'feedback.txt'),
            '文本文件 (*.txt);;所有文件 (*)')
        return fname

    # ------------------------------------------------------------------
    # 提交
    # ------------------------------------------------------------------

    def submit_feedback(self):
        """提交反馈（**不等待网络结果**，请求在后台线程 :class:`FeedbackWorker` 里跑）.

        本方法只做三件事：本地拦一下「空白 / 太短」、把按钮禁掉、起线程。

        ⚠️ **本地只拦「太短 / 空白」** —— 它连一次往返都不值得。空文本与超长都由
        服务端拥有答复文案（``The feedback text is required.`` / 截断说明），
        本地复写一份只会随服务端演进而漂；更要紧的是**本地绝不截断**（见模块
        文档第 3 条）。
        """
        if self._busy:
            return
        text = self.feedback_edit.toPlainText().strip()
        if not text:
            self._show_status('请先写下反馈内容。', ok=False)
            self.feedback_edit.setFocus()
            return
        if len(text) < MIN_LENGTH:
            self._show_status(f'反馈内容太短了（至少 {MIN_LENGTH} 个字符）。',
                              ok=False)
            self.feedback_edit.setFocus()
            return

        self._log(f'提交反馈（{len(text)} 字符）')
        self._show_status('正在提交...', ok=None)

        # ⚠️ parent **留空**（不是 ``parent=self``）：本控件会随标签页被
        #    deleteLater 销毁，parent 设成自己的线程会被连带析构 —— 请求还在飞
        #    时就是进程崩溃（"QThread: Destroyed while thread is still running"）。
        #    改由模块级 _RUNNING_WORKERS 持有强引用。
        worker = FeedbackWorker(text, parent=None)
        worker.sig_done.connect(self._on_done)
        worker.finished.connect(self._on_worker_finished)
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()

    def report_version(self):
        """把**本机版本号**作为「反馈版本号」命令提交（**仅管理员**）.

        ★ 提交的内容不是「反馈正文」，而是服务端的一条命令
        （``LatestVersion: <6 位数字>``，见 :func:`version_command_text`）。
        它会改掉那个**全局**的「最新版本」提示 —— 所以这里**先弹一次确认**：
        误点一下会影响所有客户端看到的数字，值得多问一句。

        ⚠️ 与 :meth:`submit_feedback` 走**同一条**后台线程、同一套收尾逻辑，
        区别只有两处（都在 :meth:`_on_done` 里）：答复按「版本号」措辞显示，
        且**绝不清空输入框** —— 那里的文字是用户写的反馈，不是这条命令。

        ⚠️ 本方法是**给管理员用的**入口，但它**不自己判管理员**：门在服务端
        （非管理员会拿到服务端的拒绝文案，那句话会被原样显示出来）。
        界面上「确认是管理员才显示按钮」只是为了不让人点一个必然失败的按钮。
        """
        if self._busy:
            return
        text = version_command_text()
        if not text:
            self._show_status(
                '没拿到本机版本号（可能是缺少内核库），暂时无法反馈版本号。',
                ok=False)
            return

        reply = QtWidgets.QMessageBox.question(
            self, '反馈版本号',
            '要把本机版本号报告给服务器吗？\n\n'
            f'{text}\n\n'
            '服务器会把它当作「最新版本」提示，所有客户端查询时都会看到这个数字。')
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self._log(f'反馈版本号（{text}）')
        self._show_status('正在提交...', ok=None)

        # ⚠️ parent 留空 + 挂进 _RUNNING_WORKERS：与 submit_feedback 同一条理由
        worker = FeedbackWorker(text, parent=None)
        worker.sig_done.connect(self._on_done)
        worker.finished.connect(self._on_worker_finished)
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        self._reporting_version = True
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用（``TabWidget.close_tab``）：**不等**在飞的提交。

        ⚠️ **刻意不 ``wait()``**：线程本来就没有 parent（见
        :data:`_RUNNING_WORKERS`），因此**不会**随控件一起被销毁 —— 关标签只是
        让结果失去接收者，线程照旧跑完再被 :func:`_forget_worker` 摘掉。

        ⚠️ 提交反馈是**有副作用**的动作（服务端已经收下了），所以这里绝不做任何
        「取消」：只是不再更新界面而已。

        ⚠️ 管理员判定线程同理：结论只用来决定按钮露不露面，控件没了就该丢掉
        （控件销毁后槽自动断连，迟到的结论不会打到已析构的对象上）。
        """
        self._worker = None
        self._admin_worker = None
        self._busy = False

    def _on_worker_finished(self):
        """后台线程结束（主线程调用）：放开按钮、释放引用。"""
        self._busy = False
        self._worker = None
        self._update_buttons()

    def _on_done(self, reply):
        """后台答复回来了（**在主线程里跑**）：按结论收尾。

        ⚠️ 判定用的是本模块的 :func:`is_succeed`（**只看开头 7 个字符**），
        不是 ``reply == 'Succeed'``：超长时服务端会在后面追加截断说明段。
        ⚠️ **绝不能**改用 ``is_yes`` —— 反馈的成功记号是 ``Succeed``，不以
        ``yes`` 开头，``is_yes`` 会把成功读成失败。

        Args:
            reply: 服务端答复正文。
        """
        text = str(reply or '').strip()
        reporting_version = self._reporting_version
        self._reporting_version = False
        self._log(f'反馈响应：{text or "(空响应)"}')

        if is_succeed(text):
            if reporting_version:
                # 「反馈版本号」：把服务端回的新值原样转达。
                # ⚠️ **绝不清空输入框**：那里的文字是用户写的反馈，不是这条命令
                #    （这是它与普通反馈在收尾上**唯一**的差别）。
                detail = text[len('Succeed'):].lstrip(' |').strip()
                self._show_status(
                    f'版本号已反馈到服务器（{detail}）。' if detail
                    else '版本号已反馈到服务器。', ok=True)
                return

            # 成功。⚠️ 超长时正文里带「被截断了」的说明 —— 原样转达给用户，
            #    别自己吞掉（他以为都送达了才是最糟的）。
            detail = text[len('Succeed'):].lstrip(' |').strip()
            if detail:
                self._show_status(f'反馈已提交（{detail}）', ok=True)
            else:
                self._show_status('反馈已提交，感谢您的支持！', ok=True)
            self.feedback_edit.clear()
            return

        if not text:
            self._show_status('没拿到任何答复（可能是网络中断）。内容已保留，'
                              '可以稍后重试。', ok=False)
            return

        # 失败 / 限流：**原样显示服务端原话**。
        # ⚠️ 限流那条（"please wait 217s and try again."）里的秒数是精确的剩余
        #    等待时间，是最有用的信息 —— 绝不替换成含糊的「稍后再试」。
        # 内容保留在输入框里，用户可以直接重试。
        self._show_status(f'提交失败：{text}', ok=False)

    def showEvent(self, event):
        """**首次显示**本页时，在后台判一次「本机是不是管理员」。

        ★ 这就是「**适当时刻**」：本页一露面就问一次，拿到结论再决定
        「反馈版本号」按钮露不露面（见模块文档）。判定要联网（最长 60 秒），
        所以走 :class:`AdminCheckWorker`，**界面线程一次都不等**。

        ⚠️ 只判**一次**（:attr:`_admin_checked`）：本页在标签页里会反复
        ``show`` / ``hide``，每露一次脸都给服务端发一遍请求既慢又没必要。
        ⚠️ 判不出来 / 连不上时**只是不显示按钮** —— 用户不需要知道
        「你不是管理员」，那既没用又冒犯人。
        """
        super(FeedbackTool, self).showEvent(event)
        if self._admin_checked:
            return
        self._admin_checked = True
        self._start_admin_check()

    def _start_admin_check(self):
        """起一个后台线程判定管理员（结论见 :meth:`_on_admin_checked`）."""
        # ⚠️ parent **留空**并挂进模块级的 _RUNNING_WORKERS —— 与
        #    :meth:`submit_feedback` 同一条理由：线程绝不能跟着控件被析构。
        worker = AdminCheckWorker(parent=None)
        worker.sig_result.connect(self._on_admin_checked)
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._admin_worker = worker
        _RUNNING_WORKERS.append(worker)
        worker.start()

    def _on_admin_checked(self, is_admin):
        """管理员判定回来了（主线程）：决定「反馈版本号」按钮露不露面。

        Args:
            is_admin: ``True`` 表示服务端认这个绑定邮箱是管理员。
        """
        self._admin_worker = None
        if is_admin:
            self._log('确认本机是管理员：显示「反馈版本号」')
            self.version_button.show()
        else:
            self.version_button.hide()

    def closeEvent(self, event):
        """窗口关闭时给后台线程一点收尾时间，避免对象没了线程还在跑。

        ⚠️ **本方法只覆盖「控件被单独 close()」这一条路径**：走**标签页关闭**
        （``TabWidget.close_tab``）用的是 ``deleteLater()``，**不发** ``closeEvent``
        —— 那条路径由 :meth:`cleanup_before_tab_close` 负责。``wait(3000)`` 也只是碰运气，
        真正的防护是线程没有 parent（见 :data:`_RUNNING_WORKERS`）。
        """
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.wait(3000)
        event.accept()


def test_1():
    """独立运行本控件（不依赖主窗口）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = FeedbackTool()
    w.resize(600, 420)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()

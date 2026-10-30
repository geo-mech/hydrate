"""状态栏登录状态按钮（LicenseButton）.

::

    |  已登录：张召彬  |         ← 已绑定（悬停可看姓名 / 单位 / 邮箱 / 有效期）
    |  未登录          |         ← 没有登录
    |  登录状态未知    |         ← 没查到（离线 / 超时 / 已过期 / 无 DLL）
    |  登录查询中...   |         ← 查询还没回来

**固定就是一个按钮**，无论什么状态，点击都执行 ``gui.show_reg_tool()``（打开登录
页面）；只有文字与悬停提示随状态变化。宽度上限见 :data:`MAX_BUTTON_WIDTH`
（⚠️ 中英文不等宽，**不要**按汉字数去调它，理由见那里）。

★ **界面上一律说「登录」，不说「注册」**：注册听起来像要先取得授权，而实际只是
用邮箱把本机认下来。措辞约定见 ``zmlx/_private/AUTHORIZATION_NOTES.md``。

⚠️ 「没查到」与「没登录」是**两种不同的状态**，绝不能合并（理由与判据见
``zmlx/_private/AUTHORIZATION_NOTES.md`` §11）—— 失败原因放在悬停提示里。

耗时查询一律走 :class:`LicenseStateThread`，**绝不放在 UI 线程里**。

「有没有更新版本」由本控件的 ``sig_update`` 信号转给
:class:`~zmlx.ui.widgets.version_button.VersionButton`（那件事和登录状态无关）。

Created by DeepSeek, 2026-10-08: 从 system_state_label.py 拆出
Modified by DeepSeek, 2026-10-29: 本机版本号改读 core.version（zmlx.exts.version 已弃用）
"""

from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets

#: 按钮**整体**的宽度上限（像素），超出用省略号、悬停看全名。
#:
#: ⚠️ **别再按「中文字数」定这个值**（真踩过）：本值原先取 110，理由是「2~4 个
#: 汉字够放」。可**同一个宽度对中文和英文根本不等价** —— 实测（100% 缩放）：
#: 「已登录：张召彬」= 84 px 完整显示，而「已登录：Wang Xiaoming」= 204 px，
#: 在 110 px 下只能显示成「已登录：Wang Xia…」—— 英文用户看到的名字永远是残的，
#: 而中文用户完全没事。同名的中文 84 px / 英文 204 px，差 2.4 倍，
#: 按中文调出来的上限对英文就是不够用。
#:
#: 现取 360：覆盖「已登录：」前缀（约 60 px）加绝大多数显示名的完整形态
#: （邮箱 zhangzhaobin@mail.iggcas.ac.cn 的整串是 408 px，是最长的一类，
#: 仍会被省略号截断，但已能认出是谁）。它同时兜住**任何一种状态**的完整文案 ——
#: 包括 `pending` 的「登录查询中...」（96 px）：不再有「状态文字自己就把省略号
#: 挤出来」这种自相矛盾的显示。
#:
#: 是不是**真的**不挤状态栏，看的是常见情形下的宽度，不是这个上限：短名（中文、
#: 或 Jane Doe 这类英文名，原型约 100~150 px）时按钮宽度是由 sizeHint 决定的，
#: 上限根本用不到。只有异常长的显示名才会吃掉状态栏右端。
MAX_BUTTON_WIDTH = 360

#: 尚未查出结果时的占位文本（查询在后台线程里跑，最长 60 秒）
PENDING_TEXT = '登录查询中...'

#: 确定未登录时按钮上的文字。
#: ⚠️ 界面上一律说「登录」而不是「注册」—— 详细的措辞约定见
#: ``zmlx/_private/AUTHORIZATION_NOTES.md``。
UNREGISTERED_TEXT = '未登录'

#: 查不到（离线 / 超时 / 无 DLL）时的文字。刻意**不**用「未登录」。
UNKNOWN_TEXT = '登录状态未知'

#: 服务端在「本机没登记过（未登录）」时回的正文**开头**
#: （``Please register with your email first.``）。这才是**确定**「没登录」的判据。
#: ⚠️ 这是**服务端**的原文，不是界面文案，**不要**跟着界面一起改。
#: 只认开头、忽略大小写。
NO_LICENSE_REPLY = 'please register with your email first'

#: 答复里「最新版本」那一段的标签。
LATEST_TAG = 'LatestVersion:'


def _get_local_version():
    """取本机软件的版本号（6 位整数，``yymmdd``，例如 ``260928`` = 2026-09-28）。

    就是 ``core.version``（由内核导出，与 ``zmlx.exts.lic`` 同源）。

    ⚠️ 2026-10-29 起改读 :attr:`core.version`：模块级的 ``zmlx.exts.version``
    已弃用（2027-10-29 删除）。⚠️ 它**不是** ``zmlx.__version__`` —— 后者是包
    版本（如 ``'1.9.3'``），服务端比较用的是前者这套 ``yymmdd`` 整数。

    Returns:
        int: 版本号；取不到时返回 ``None``（那时一律不提示更新）。
    """
    try:
        from zmlx.exts import core
        return int(core.version)
    except Exception:
        return None


def _parse_latest_version(reply):
    """从服务端答复里取出「最新版本」号。

    取不到的**情形很多，全都是正常的**，一律返回 ``None``（= 不提示更新）：
    答复里本来就没有这一段（服务端没配）、连不上、没授权、格式不是数字……

    ⚠️ 返回 ``None`` 时**绝不能**当成「有更新」——那会让每个离线用户都看到
    一个假提示。

    Args:
        reply: 服务端答复正文。

    Returns:
        int: 最新版本号；没有或不可解析时返回 ``None``。
    """
    for part in str(reply or '').split('|'):
        part = part.strip()
        if part.startswith(LATEST_TAG):
            text = part[len(LATEST_TAG):].strip()
            try:
                return int(text)
            except ValueError:
                # 该段存在但内容不是数字（服务端将来改了格式）——当作没有
                return None
    return None


def has_update(reply):
    """答复是否表明**本机版本落后于服务端的最新版本**。

    两端都是 ``yymmdd`` 形式的 6 位整数，所以直接比大小即可（同世纪内日期与
    数值同序）。

    ⚠️ 只有**两端都拿到了**、且最新版**严格大于**本机版才算有更新：
    服务端没给这一段、本机版本取不到、或版本相同/更新，都返回 ``False``。
    宁可漏报，也不能把「查不到」显示成「有更新」—— 用户点开「关于」一看没有
    新版，就再也不信这个提示了。

    Args:
        reply: 服务端答复正文。

    Returns:
        bool: 有更新返回 True。
    """
    local = _get_local_version()
    latest = _parse_latest_version(reply)
    if local is None or latest is None:
        return False
    return latest > local


#: 正在后台跑的 :class:`LicenseStateThread`（模块级强引用）。
#:
#: ⚠️ **线程的 parent 绝不能是控件** —— 否则关窗时会连带析构它，触发
#: ``QThread: Destroyed while thread ... is still running``（**进程级崩溃**）。
#: 完整理由与纪律见 ``zmlx/_private/AUTHORIZATION_NOTES.md`` §12。
_RUNNING_THREADS = []


def _forget_thread(thread):
    """把已经跑完的线程从登记表里摘掉（主线程调用）。"""
    try:
        _RUNNING_THREADS.remove(thread)
    except ValueError:
        pass


class LicenseStateThread(QtCore.QThread):
    """在后台线程里查一次「本机登录状态」（**绝不碰界面**）。

    复用登录页那套现成的判据（``web_license.check`` 取服务端原话 →
    ``bound_info`` 解析出「绑定到了谁」），避免同一件事在两处各写一遍。

    ⚠️ 异常绝不允许逃出 :meth:`run`：真逃出去的话线程会静默死掉、信号永不
    发出，状态栏就会永远停在 :data:`PENDING_TEXT`。任何异常都翻成
    ``'unknown'`` 的结果。

    Attributes:
        sig_state: 信号，携带 ``(状态, 姓名, 详情)``；状态取 ``'bound'`` /
            ``'unbound'`` / ``'unknown'``。
        sig_update: 信号，携带「服务端是否有比本机更新的版本」这一个布尔。
            ⚠️ 单独一个信号、而不是塞进 ``sig_state`` 的第 4 个参数：更新与否
            与登录状态**无关**（没登录时服务端照样可能报出新版本），分开传就
            不必去改既有槽函数的签名。
    """

    sig_state = QtCore.pyqtSignal(str, str, str)
    sig_update = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, read_cache=True):
        """初始化线程。

        Args:
            parent: Qt 父对象。
            read_cache: 是否允许直接读结果缓存，转交给
                :func:`query_license_state`（默认 True）。
        """
        super(LicenseStateThread, self).__init__(parent)
        self.read_cache = bool(read_cache)
        self.setObjectName('LicenseStateThread')

    def run(self):
        """线程体：查一次登录状态并发回主线程。"""
        try:
            state, name, detail, update = query_license_state(
                read_cache=self.read_cache)
        except Exception as err:  # 防御性：正常路径不会触发
            state = 'unknown'
            name = ''
            detail = f'查询登录状态时出错：{type(err).__name__}: {err}'
            update = False
        self.sig_state.emit(state, name, detail)
        self.sig_update.emit(bool(update))


def _classify(reply):
    """把服务器的一次答复归类成状态（**纯函数**，不联网、不碰界面）.

    单独拆出来是为了能离线测：只喂文本、看结论，不必真去连一次服务器。

    判据**只看开头**，绝不能整串比较 —— 有效的答复后面可能追加说明段。

    Args:
        reply: 服务端的原始答复（任意对象，会被转成字符串）。

    Returns:
        str: ``'bound'`` / ``'unbound'`` / ``'unknown'``。
    """
    from zmlx.ui.utils.lic_utils import bound_info, is_yes

    text = str(reply or '').strip()
    if not text:
        # 空响应：连不上或服务端没回话，这属于「没查到」
        return 'unknown'

    if not is_yes(text):
        # 失败文案里只有一种能**确定**是「没授权」
        if text.lower().startswith(NO_LICENSE_REPLY):
            return 'unbound'
        return 'unknown'

    # 答复是 Yes：能确定授权有效。再看是不是绑定到了邮箱 ——
    # bound_info 只在**真正绑定**时才返回内容（结论来自兜底文件也算没绑定）
    return 'bound' if bound_info(text) else 'unbound'


def query_license_state(read_cache=True):
    """查一次本机登录状态（**后台线程专用**，本函数绝不碰界面）。

    三种结论（与 :meth:`LicenseButton.set_license_state` 的取值一一对应）：

    ==================  ==================================================
    返回值               含义
    ==================  ==================================================
    ``'unbound'``       服务端明确回了 ``Please register with your email
                        first.``（本机没登记过），或授权能用但没绑定到邮箱
    ``'bound'``         已绑定到某个用户 / 邮箱
    ``'unknown'``       其它失败文案（连不上、超时、过期、该功能不可用…）
    ==================  ==================================================

    ⚠️ ``'unbound'`` 与 ``'unknown'`` 不能混（理由见
    ``zmlx/_private/AUTHORIZATION_NOTES.md`` §11）。

    Args:
        read_cache: 是否允许直接读结果缓存；转交给 ``check_web`` →
            ``web_license.check``。
            - ``True``（默认）：本机已有结论时**不再发网络请求**；
            - ``False``：强制向服务端要最新结果。**刚登录完的自检必须
              用它** —— 读缓存会把刚绑定好的机器判成「未绑定」。

    Returns:
        tuple: ``(状态, 姓名, 详情, 是否有更新)``。姓名只在 ``'bound'`` 时可能
        非空；详情是多行文本，用于悬停提示；「是否有更新」见 :func:`has_update`
        —— 它只回答「服务端报的最新版比本机新吗」，与本机有没有授权无关。
    """
    from zmlx.ui.utils.lic_utils import (
        CHECK_FEATURE,
        bound_info,
        check_web,
        detail_of,
        find_field,
    )

    text, elapsed = check_web(CHECK_FEATURE, read_cache=read_cache)
    state = _classify(text)
    reply = str(text or '').strip()
    update = has_update(reply)      # 与登录状态无关，单独算

    if state == 'unknown':
        if not reply:
            return 'unknown', '', '未拿到任何答复（可能是网络中断）。', update
        return 'unknown', '', (
            '未能确认登录状态（可能离线或超时）。\n\n'
            f'服务器原话：\n{reply}\n\n'
            f'往返耗时：{elapsed:.2f} s'
        ), update

    if state == 'unbound':
        if reply.lower().startswith(NO_LICENSE_REPLY):
            # 本机根本没登记过 —— 这是最彻底的「没登录」
            return 'unbound', '', (
                '本机尚未登录。\n点击打开登录页面。\n\n'
                f'服务器原话：{reply}'
            ), update
        # 服务端认这台机器，只是没绑定到邮箱（结论来自兜底记录），随时可能失效
        return 'unbound', '', '本机尚未登录。\n点击打开登录页面。', update

    # ---- 已绑定 ----
    info = bound_info(text)
    email = info.get('email') or ''
    user = info.get('user') or ''
    name = user or email  # 没有姓名就退回邮箱，总之要能认出「是谁」

    lines = []
    if user:
        lines.append(f'姓名：{user}')
    if info.get('org'):
        lines.append(f'单位：{info["org"]}')
    if email:
        lines.append(f'邮箱：{email}')
    expires = find_field(detail_of(text), 'Expires')
    if expires:
        lines.append(f'有效期至：{expires}')
    if update:
        latest = _parse_latest_version(reply)
        lines.append(f'有新版本可用：{latest}')
    lines.append('')
    lines.append('点击可打开登录页面查看/刷新详情。')

    return 'bound', name, '\n'.join(lines), update


class LicenseButton(QtWidgets.QToolButton):
    """状态栏上的登录状态按钮：显示本机登录情况，点击打开登录页面。

    首次显示时会自动查一次（见 :meth:`showEvent`）。

    ⚠️ 2026-10-26：控件由 ``QPushButton`` 改为 ``QToolButton``（与状态栏里的
    ``VersionButton`` / ``RunStateLight`` 一致），**尺寸交给 Qt 默认**
    （不重写 ``sizeHint``、不写 padding QSS）。唯一保留的尺寸约束是
    :data:`MAX_BUTTON_WIDTH` 这个**上限**（超长显示名不能把状态栏撑宽），
    它不是"写死高度/宽度"，与"去尺寸策略"并不冲突。

    Attributes:
        sig_update: 信号，携带「服务端是否报了更新的版本」这一个布尔。
            ⚠️ 由 :class:`LicenseStateThread` 原样转发出来，供
            :class:`~zmlx.ui.widgets.version_button.VersionButton` 显示「有更新」
            后缀（在 ``MainWindow`` 里连一行）；本控件自己不消费它。
    """

    #: 查询结果里「是否有更新」的转发信号（见类文档）
    sig_update = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super(LicenseButton, self).__init__(parent)

        self._thread = None            # 后台查询线程（持有引用，防被 GC）
        self._license_state = None     # 当前展示的状态；None = 还没查过
        self._license_started = False  # 是否已经起过一次查询（showEvent 只起一次）

        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        # 状态栏在窗口角落，不抢键盘焦点：鼠标可点即可
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.clicked.connect(lambda: gui.show_reg_tool())

        # 宽度上限：状态栏是很窄的一条，不能让超长显示名把它撑宽。
        # 用 maximumWidth（不是 fixedWidth）—— 短文本时宽度自动收缩，不留空档。
        # ⚠️ 这个上限卡的是**整体宽度**，不是姓名的像素宽度：见 MAX_BUTTON_WIDTH
        self.setMaximumWidth(MAX_BUTTON_WIDTH)

        self.set_license_state('pending')

    # ------------------------------------------------------------------
    # 状态显示
    # ------------------------------------------------------------------

    def set_license_state(self, state, name='', detail=''):
        """按查询结果刷新按钮的文字与提示（**只在主线程调用**）。

        只改文字与悬停提示 —— 控件本身固定是那个按钮，动作固定是打开登录页面。

        Args:
            state: ``'pending'``（还没结果）/ ``'bound'``（已登录）/
                ``'unbound'``（没登录）/ ``'unknown'``（没查到）。
            name: 已登录时的显示名（姓名优先，取不到则邮箱）。
            detail: 悬停提示的多行详情。
        """
        self._license_state = state
        if state == 'bound':
            text = f'已登录：{self._elide(name)}'
        elif state == 'unbound':
            # 「没查到」绝不能显示成「没登录」—— 详见模块文档
            text = UNREGISTERED_TEXT
        elif state == 'unknown':
            text = UNKNOWN_TEXT
        else:  # pending
            text = PENDING_TEXT
        self.setText(text)
        self.setToolTip(detail or f'{text} —— 点击打开登录页面')
        # 兜底再显示一次：右侧固定就是这个按钮，任何状态下都该看得见
        self.show()

    def get_license_state(self):
        """返回当前展示的登录状态（``'bound'`` / ``'unbound'`` /
        ``'unknown'`` / ``'pending'``）."""
        return self._license_state

    def _elide(self, name):
        """把过长的姓名截断成「带省略号」的短串.

        ⚠️ 预算 = :data:`MAX_BUTTON_WIDTH` **减去**「已登录：」前缀占掉的宽度 ——
        省略号截的是**整串文本**、而上限卡的是**整个按钮**，两者不是同一个量。
        若拿上限直接当姓名宽度，英文名会按「还剩 360-60=300 px」却只用 360 判，
        白白少显示一截；更要紧的是**显示出来的整串**一旦超过上限，Qt 就会把
        尾巴整个裁掉（收不到省略号，看起来像文字被砍断）。取不到字体度量时
        退回整个上限（宁可少显示，也不能让文字溢出）。

        Args:
            name: 显示名（姓名优先，取不到则邮箱兜底）。

        Returns:
            str: 可安全放进按钮的短串。
        """
        text = str(name or '')
        metrics = self.fontMetrics()
        lead = 0
        try:
            lead = metrics.horizontalAdvance(f'已登录：')
        except Exception:  # 防御性：度量失败时退回整个上限
            lead = 0
        room = max(MAX_BUTTON_WIDTH - lead, 1)
        return metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, room)

    # ------------------------------------------------------------------
    # 后台查询（耗时的活一律在这里，绝不占 UI 线程）
    # ------------------------------------------------------------------

    def showEvent(self, event):
        """首次显示时启动后台线程去查登录状态（只启动一次）."""
        super(LicenseButton, self).showEvent(event)
        # ⚠️ 判据是「有没有起过查询」，不是「状态是不是 None」：构造时状态就已经
        #    被设成 'pending' 了，拿 _license_state 判空会让查询永远不启动
        #    （真踩过：状态栏一直停在「授权查询中...」）
        if self._license_started:
            return
        # 延后一拍：showEvent 期间控件还没画出来，此时起线程会让「窗口弹出来」
        # 这件事变得不可预期（同 tabs.license_register.LicenseRegister.showEvent）
        QtCore.QTimer.singleShot(0, self.start_license_query)

    def start_license_query(self, read_cache=True):
        """启动后台线程查询登录状态（**主线程调用**；重复调用无副作用）.

        QThread 的创建与启动固定在主线程进行，因此本方法只应由主线程调用
        （``showEvent`` / :meth:`update_license_state` 都满足这一点）。

        Args:
            read_cache: 是否允许直接读结果缓存，原样转交给
                :func:`query_license_state`（默认 True）。语义见
                :meth:`update_license_state`。
        """
        if self._thread is not None:
            return  # 上一次查询还没回来
        self._license_started = True
        self.set_license_state('pending')
        # ⚠️ parent **留空**（不是 ``self``）：本控件随主窗口一起被销毁时，
        #    parent 设成自己的线程会被连带析构 = 进程崩溃（见 _RUNNING_THREADS）。
        thread = LicenseStateThread(parent=None, read_cache=read_cache)
        thread.sig_state.connect(self._on_license_state)
        thread.sig_update.connect(self.sig_update)  # 转发给版本按钮（外部连接）
        thread.finished.connect(self._on_thread_finished)
        thread.finished.connect(lambda t=thread: _forget_thread(t))
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        _RUNNING_THREADS.append(thread)
        thread.start()

    def update_license_state(self, read_cache=True):
        """更新登录状态显示（先复位为「查询中...」再起后台线程）.

        联网查询在后台线程（:class:`LicenseStateThread`）里跑，本函数**从不等待
        联网结果**（那最长 60 秒），因此界面不会被网络超时卡住。

        ⚠️ **推荐的调用入口是 ``gui.update_system_state()``**，不要自己跨线程调
        本方法：它经 ``gui.command`` 把 ``MainWindow.update_system_state`` 放到
        GUI 线程里执行（信号跨线程排队投递），所以走到这里时**已经在主线程**，
        走下面第一个分支 —— 调用方无论是脚本线程还是主线程，效果一样。

        「立即返回」的准确含义：在主线程里调用只有起线程的零点几毫秒；在别的
        线程里经 ``gui.command`` 调用，则要等 GUI 线程把这个调用取走才返回
        （实测约 5 ms）—— 那是 ``gui.command`` 自身的约定，与本函数无关。

        本方法之所以还留着第二个分支，只是为了「有人直接在非主线程里调它」时
        不至于踩 Qt 的线程规则（QThread 对象属于创建它的线程，跨线程起线程不
        合法）：那种情况用 ``gui.call(...)`` 把「起线程」这件**操作**投递给 GUI
        线程执行 —— ``GuiApi`` 自带 ``call`` 这个函数，它同样经信号排队到主线程，
        所以回调里可以安全地碰界面 / 起线程。

        Args:
            read_cache: 是否允许直接读结果缓存（默认 True），见
                :func:`query_license_state`。**刚绑定完机器要核实「服务端是否
                真的认了这份授权」时必须传 False**，否则会读回绑定之前的旧结论。
        """
        # 主线程（含经 gui.update_system_state 投递过来的调用）：直接起线程
        if QtCore.QThread.currentThread() is self.thread():
            self.start_license_query(read_cache=read_cache)
            return
        # 兜底：非主线程直接调用 —— 把「起线程」交给 GUI 线程执行
        # ⚠️ read_cache 必须一起带过去：gui.call 会把参数原样转交，漏掉它就会
        #    悄悄退回默认值，让「强制联网」的调用变成「读缓存」。
        try:
            gui.call(self.start_license_query, read_cache=read_cache)
        except Exception as err:
            print(f'Error (update_license_state): {err}')

    def _on_license_state(self, state, name, detail):
        """查询结果回来了（主线程调用）：刷新显示."""
        self.set_license_state(state, name, detail)

    def _on_thread_finished(self):
        """后台线程结束（主线程调用）：释放引用."""
        self._thread = None

    def closeEvent(self, event):
        """控件销毁前给后台线程一点收尾时间，避免对象没了线程还在跑.

        ⚠️ **本方法的 ``wait`` 只是「碰运气等一小会」**，不是崩溃防护：查询最长
        60 秒，等 100 毫秒基本等不到；真正的防护是**线程没有 parent**
        （见 :data:`_RUNNING_THREADS`）—— 线程不会随控件被销毁，关窗后它会自己
        跑完再被 :func:`_forget_thread` 摘掉。这里保留等待只是让「刚好查完」的
        常见情况更干净。
        """
        thread = self._thread
        if thread is not None:
            thread.wait(100)
        super(LicenseButton, self).closeEvent(event)


def test_1():
    """交互式查看：几个状态各显示一遍（不联网）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(w)

    status_bar = QtWidgets.QStatusBar(w)
    btn = LicenseButton(status_bar)
    btn._license_started = True  # 交互查看时不联网
    status_bar.addPermanentWidget(btn)
    layout.addWidget(status_bar)

    row = QtWidgets.QHBoxLayout()
    for text, state, name in [
        ('待查询', 'pending', ''),
        ('已登录', 'bound', '张召彬'),
        ('英文名', 'bound', 'Wang Xiaoming'),
        # ⚠️ 英文名比中文名宽得多（同长度的整串能差 2.4 倍），专门留一格看它会不会
        #    被截断 —— 见 MAX_BUTTON_WIDTH
        ('超长名', 'bound', '中国科学院地质与地球物理研究所-张召彬'),
        ('未登录', 'unbound', ''),
        ('未知', 'unknown', ''),
    ]:
        b = QtWidgets.QPushButton(text)

        def apply(state=state, name=name):
            btn.set_license_state(state, name, '这是悬停详情\n第二行')

        b.clicked.connect(apply)
        row.addWidget(b)
    layout.addLayout(row)

    w.resize(760, 120)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()

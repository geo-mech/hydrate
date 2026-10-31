"""许可服务答复的解析与查询工具（``zmlx.ui.utils.lic_utils``）.

本模块是「问服务端 -> 读答复」这一层的**公共工具**，原先长在
``zmlx/ui/widget/license_register.py`` 里、与 :class:`LicenseRegister` 控件同处一个
文件；2026-10-16 把这一整段下沉出来（当时落在 ``zmlx/ui/lic_utils.py``），
同日随 ``zmlx/ui/utils.py`` 改成 ``zmlx/ui/utils/`` 包而**一并移入本包**。

为什么单独成一个模块
--------------------

这段工具**不只被登录控件用** —— 同一份答复要回答好几个不同的问题，于是有多个
调用方，分处两个包::

    zmlx/ui/tabs/license_register.py     登录表单：绑定状态、机器码、答复耗时
    zmlx/ui/plugins/builtin/user_admin.py  查询记录页：表单初值（已绑定的邮箱）
    zmlx/ui/plugins/builtin/user_admin.py 反馈记录页：同上
    zmlx/ui/tabs/about.py                「关于」页：管理员权限判定
    zmlx/ui/widget/license_button.py     状态栏：这一格该显示哪句话

控件分层改造（``tabs/`` 收「有标签生命周期钩子的重量级页面」、``widget/`` 留通用
控件）之后，这段工具若跟着 ``license_register`` 一起进 ``tabs/``，那么留在
``widget/`` 的 ``license_button.py`` 就会**反向依赖** ``tabs/`` —— 即「通用控件
目录依赖标签页目录」。下沉成独立模块后，两边都向上引用它，依赖方向恢复单向。

⚠️ 本模块**不依赖 Qt**（只用 stdlib 与 :mod:`zmlx.exts.web_license`），所以任何层
都可以安全导入，不会引入 GUI 依赖。

⚠️ **它是本包（``zmlx/ui/utils/``）里唯一不依赖 Qt 的模块** —— 这完全没问题：本包的
定位是「服务于 ``zmlx.ui`` 的工具集合」，**是否依赖 Qt 由各子模块自己的需要决定，不是
入选门槛**。它**刻意不被 ``zmlx/ui/utils/__init__.py`` 转发**，理由不是「不配」，而是
克制：它 import 了 :mod:`zmlx.exts.web_license`（扩展层），转发它等于让每一次
``import zmlx.ui.utils`` 都连带拉起扩展层。它保持按需导入：
``from zmlx.ui.utils.lic_utils import ...``。

⚠️ 这里的所有函数都是**纯文本解析 / 薄封装**，不认识界面；凡是要动界面的逻辑一律
留在各控件里。

Created by DeepSeek, 2026-10-16: 自 ``zmlx/ui/widget/license_register.py`` 下沉。
Modified by DeepSeek, 2026-10-16: 由 ``zmlx/ui/lic_utils.py`` 移入 ``zmlx/ui/utils/`` 包.
"""

import time

from zmlx.exts import web_license


#: 服务端的成功正文（本控件只会收到这两个 —— 只发码，不单独注册邮箱）。
#:
#: ⚠️ 判定**不要**拿它们做 ``==`` 比较，请用 :func:`is_sent` / :func:`is_bound`
#:    （只看开头）：严格相等是一条会随服务端演进而失效的隐含假设。
SUCCESS_SENT = 'Sent'
SUCCESS_BOUND = 'Bound'

#: 姓名的最大长度。与服务端的上限一致，超出会被拒。
MAX_USER_LEN = 128

#: 单位的最大长度。与服务端的上限一致，超出会被拒。
MAX_ORG_LEN = 128

#: 发码时可以声明的用途 —— **只影响邮件正文的措辞，不影响任何判定**。
PURPOSE_REGISTER = '登录新邮箱 / sign in a new email'

#: 发码时可以声明的用途（绑定一台新设备）。同上，只影响邮件措辞。
PURPOSE_BIND = '绑定一台新设备 / bind a new device'

#: 答复里说明段的分隔符。
DETAIL_SEP = ' | '

#: 说明段的取值：结论**不是**来自本机自己的那条记录，说明本机尚未真正注册。
#: 任何查不到的名字都会被它兜住。
DEFAULT_SOURCE = 'default.json'

#: 说明段里「实际来源」那一项的标签。
SOURCE_TAG = 'Source: '

#: 自检时问服务器的那一问：``'*'`` = 「这份许可到底授了什么」（与「关于」页面
#: 用的是同一个记号）。查它时必须带 ``read_cache=False``，理由见模块文档。
CHECK_FEATURE = '*'

#: :func:`pack_elapsed` / :func:`unpack_elapsed` 用的分隔符（NUL：不可能出现在
#: 服务器答复里，所以不会切错位置）。
ELAPSED_SEP = '\x00'


#: 作者邮箱 —— 判定「管理员权限」的**唯一**依据（见 :func:`is_admin_by_web_license`）。
#:
#: ⚠️ 这个地址同时也是「关于」页面上显示的「联系邮箱」，两处必须是同一个值；所以它
#:    只在本模块定义一次，``zmlx/ui/tabs/about.py`` 从本模块 import。
ADMIN_EMAIL = 'zhangzhaobin@mail.iggcas.ac.cn'

#: ``user_list`` 接口的成功记号。
#:
#: ⚠️ **与 ``user_admin.COUNT_TAG``（``'Count:'``）刻意分开** —— 两者都是 6 个
#:    字符、都带冒号，只差前面那个词；拿混了会把**成功读成失败**（最容易踩的一类事故）。
#:    判据见 :func:`is_user_list`。
USER_LIST_TAG = 'Users:'

#: ``user_list_detail`` 的成功记号（★ 服务端 v3.35，**仅管理员**）。
#:
#: ⚠️ 与 :data:`USER_LIST_TAG`（``Users:``）**只差一个词**，但它们是**两个动作**：
#: 老动作只给邮箱（``Users:``），新动作给邮箱 + 姓名（``UsersDetail:``）。
#: 拿混的后果两个方向都错 —— 新答复会被判成「没拿到」，老答复会被当成新格式
#: 解析出空仓库。两者都只差半句话，读代码时**数清字符**。
USER_DETAIL_TAG = 'UsersDetail:'

#: ``user_list_detail`` 里「姓名」那一段的记号（与 ``List:`` **一一对应**）。
NAMES_TAG = 'Names:'

#: 服务端对「这个用户没写姓名」的**占位**（空串会被 ``strip()`` 吃掉，所以用记号）。
#: 客户端解析时把它还原成**空串**，界面据此只显示邮箱。
NAME_PLACEHOLDER = '(none)'

#: ``user_list`` 答复里名单段的标签；名单是 ``; `` 分隔的邮箱串（**不是 JSON**）。
LIST_TAG = 'List:'


def _leading_word(text, word) -> bool:
    """判断正文去掉首尾空白后是否以 ``word`` 开头（不区分大小写）。

    **只认开头**，不要求该词后面是空格或串尾。

    为什么只认开头（而不是严格相等）：服务端的成功正文目前恰好就是那三个字、
    没有说明段，所以严格相等**目前**成立 —— 但那是一条会随服务端演进而失效的
    隐含假设。将来服务端在成功正文后追加说明段时，「只看开头」仍然安全。

    ⚠️ 只查开头、**不查整句**：``'a code was sent recently, please wait 412s'``
    （限流答复）是**失败**文案，它含 ``sent`` 却不以它开头 —— 用「包含」判断
    会把这条正常的限流提示误判成「已发出」。

    Args:
        text: 服务端回应正文（任意对象，会被转成字符串）。
        word: 要比对的开头词（例如 ``'Sent'``）。

    Returns:
        bool: 以该词开头返回 True。
    """
    return str(text if text is not None else '').strip()[
        :len(word)].lower() == str(word).lower()


def is_sent(text) -> bool:
    """判断 ``web_license.send_code`` 的答复是否为「验证码已发出」。

    Args:
        text: :meth:`zmlx.exts.web_license.send_code` 返回的正文。

    Returns:
        bool: 已发出返回 True。
    """
    return _leading_word(text, SUCCESS_SENT)


def is_bound(text) -> bool:
    """判断 ``web_license.submit`` 的答复是否为「注册 + 绑定成功」。

    Args:
        text: :meth:`zmlx.exts.web_license.submit` 返回的正文。

    Returns:
        bool: 绑定成功返回 True。
    """
    return _leading_word(text, SUCCESS_BOUND)


def is_yes(text) -> bool:
    """判断答复算不算「授权有效」。

    判据：去掉首尾空白后，**前 3 个字符忽略大小写等于 ``yes``** —— 成功时后面
    可能跟 `` | `` 说明段，所以不能要求整串相等。

    Args:
        text: 服务器答复（任意对象，会被转成字符串）。

    Returns:
        bool: 有效返回 True。
    """
    return str(text or '').strip()[:3].lower() == 'yes'


def detail_of(text) -> str:
    """取答复里 `` | `` 之后的说明段（没有则为空串）。

    Args:
        text: 服务器答复。

    Returns:
        str: 说明段。
    """
    parts = str(text or '').split(DETAIL_SEP, 1)
    return parts[1] if len(parts) > 1 else ''


def find_field(detail, key) -> str:
    """从说明段里取出 ``<key>: <value>`` 中的值。

    Args:
        detail: `` | `` 之后的说明段。
        key: 字段名前缀，例如 ``'Source'``。

    Returns:
        str: 字段值；没有该字段时返回空串。
    """
    prefix = f'{key}: '
    for part in str(detail or '').split(DETAIL_SEP):
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix):].strip()
    return ''


def source_of(text) -> str:
    """从答复里取出「结论实际来自哪份记录」。

    答复里只有在**结论不是来自请求的那一项**时才会附 ``Source:`` 段，
    所以这里按 `` | `` 切开逐段比对、取第一个匹配。

    Args:
        text: ``web_license.check`` 的答复（可能带 `` | `` 说明段）。

    Returns:
        str: 来源名；没有 ``Source:`` 段时返回空串。
    """
    for part in str(text or '').split(DETAIL_SEP):
        part = part.strip()
        if part.startswith(SOURCE_TAG):
            return part[len(SOURCE_TAG):].strip()
    return ''


def is_bound_to_email(text=None, feature=CHECK_FEATURE, read_cache=False) -> bool:
    """判断本机是否已经成功绑定了邮箱。

    判据**完全来自服务端的答复**，本函数不额外读存储：

    ====================================  ==================================
    答复                                  含义
    ====================================  ==================================
    带 ``Source:`` 且**不是**兜底来源      **已绑定**
    带 ``Source:`` 且是兜底来源            **未绑定**
    没有任何 ``Source:`` 段                **未绑定**（只有作者直接签发的机器）
    ====================================  ==================================

    ⚠️ 本函数只回答「有没有绑定」，**不回答「是否还在有效期」**：绑定存在但授权
    已过期时仍然返回 ``True``。查询失败（网络错误、无 DLL、没有 ``Source:`` 段
    的情况）一律返回 ``False``。

    ⚠️ ``read_cache`` 默认给 ``False``：本函数要的正是「现在」的状态，读缓存会
    让人看到注册之前的旧结论（理由见模块文档）。

    Args:
        text: ``web_license.check`` 的答复；``None`` 表示本函数自己去查一次
            （用下面的 ``feature`` / ``read_cache``）。
        feature: 查询用的功能名，默认 ``'*'``。
        read_cache: 是否允许直接读结果缓存（``False`` = 强制重新连一次服务器）。
            只有 ``text`` 为 ``None`` 时才用得上。

    Returns:
        bool: 已经绑定到邮箱返回 ``True``，否则返回 ``False``。
    """
    if text is None:
        text = check_web(feature, read_cache=read_cache)
    source = source_of(text)
    return bool(source) and source.lower() != DEFAULT_SOURCE


def bound_info(text) -> dict:
    """从答复里取出「这台机器绑定到了谁」。

    ⚠️ **只有真正绑定了邮箱才返回内容**：判据与 :func:`is_bound_to_email` 完全
    一致。未绑定 / 查询失败一律返回空字典 —— 那种情况下答复里的姓名等内容并不
    属于本机用户，拿去填输入框就是错的。

    ⚠️ **本函数刻意不再返回 ``note``**：备注自服务端 v3.27 起移出了登录记录
    （改存普通用户文件 ``note.txt``，见 :data:`_ProfileBox.NOTE_FILE_NAME`），
    于是查询答复里**不再有 ``Note:`` 段**，那个键恒为空串、且全仓库无人读取
    —— 留着只会让人以为「备注从许可答复里读」。备注请走
    :meth:`LicenseRegister._fetch_note`。

    Args:
        text: ``web_license.check`` 的答复。

    Returns:
        dict: ``{'source', 'email', 'user', 'org'}``，取不到的键为空串；
        未绑定时返回 ``{}``。
    """
    if not is_bound_to_email(text):
        return {}
    detail = detail_of(text)
    return {
        'source': find_field(detail, 'Source'),
        'email': find_field(detail, 'Email'),
        'user': find_field(detail, 'User'),
        'org': find_field(detail, 'Org'),
    }


def fingerprint_sha() -> str:
    """取本机硬件码（= ``zmlx.exts.web_license.machine_id()``）。

    绑定与查询必须用同一个值，而这个值由 C++ 侧自己算。

    ⚠️ 它**只用于内部判断**：控件不显示它、也不传给服务端。现在唯一的用途是
    :meth:`LicenseRegister.__init__` 拿它判断「zml.dll 到底加载成功没有」——
    取不到就是空串，那时一切网络请求都发不出去，按钮要禁用。

    Returns:
        str: 机器码字符串；无 DLL 或调用失败时返回空串。
    """
    try:
        # ⚠️ machine_id 是**函数**，必须带括号（见 WebLicense.machine_id）。
        return str(web_license.machine_id() or '').strip()
    except Exception as err:
        print(f'Error (fingerprint_sha): {err}')
        return ''


def check_web(feature, read_cache=True):
    """调 ``zmlx.exts.web_license.check`` 查授权，并兜住任何异常。

    ⚠️ **耗时必须在后台线程里量**，所以这里把 ``(答复, 耗时秒数)`` 一起返回，
    而不是在外面另计一次：外面拿到结果的时刻还包含「信号跨线程回到主线程」的
    排队延迟，那样量出来的是「界面等了多久」，不是「服务器用掉多久」—— 后者
    才是用户想看的连接速度。

    ⚠️ 计时的**起止覆盖整个调用**，因此失败路径（连不上、超时、``dll not
    found``）同样有耗时 —— 那恰恰是最该看耗时的时候（连不上时它约等于超时值）。

    Args:
        feature: 功能名（本控件用 :data:`CHECK_FEATURE`）。
        read_cache: 是否允许直接读结果缓存。**自检必须传 False**，
            否则会拿到「绑定之前」的旧结果（理由见模块文档）。

    Returns:
        tuple: ``(答复, 耗时秒数)``。答复是服务器文本；``web_license.check`` 自己
        已把网络异常翻成文本，这里再兜一层（例如无 DLL 时模块内其它环节出错）。
    """
    start = time.perf_counter()
    try:
        # web_license 已在模块顶部从 ``zmlx.exts`` 导入，这里直接用。
        text = str(web_license.check(feature, read_cache=read_cache))
    except Exception as err:
        text = f'Failed to query the license server: {type(err).__name__}: {err}'
    return text, time.perf_counter() - start


def format_elapsed(seconds) -> str:
    """把耗时格式化成给用户看的一行字。

    ⚠️ 这个数字**同时包含**本机到服务器的网络往返与服务器内部处理的时间；
    两段没有分开上报，所以文案只说「往返耗时」，不要写成「服务器处理时间」
    —— 那会把网络慢误报成服务器慢。

    Args:
        seconds: 耗时秒数；``None`` 或负数返回空串（调用方据此跳过该行）。

    Returns:
        str: 例如 ``'往返耗时：0.42 s'``；无法计算时返回空串。
    """
    if seconds is None:
        return ''
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return ''
    if value < 0:
        return ''
    # 一秒以内给毫秒：命中缓存或网络极快时只有几十毫秒，用秒看不出差别
    if value < 1:
        return f'往返耗时：{value * 1000:.0f} ms'
    return f'往返耗时：{value:.2f} s'


def pack_elapsed(text, elapsed) -> str:
    """把耗时**附在**答复正文后面，好让它在信号里穿过线程边界。

    ``_Worker.finished_with`` 只发 ``(key, 状态码, 正文)`` 三个参数，而耗时是
    第三个值；与其改信号签名（会牵动 send_code / bind 两路），不如把它编码进
    正文，回到主线程再 :func:`unpack_elapsed` 拆开。

    ⚠️ 分隔符用 ``\\x00``（NUL）：它**不可能**出现在服务器答复里（答复是
    JSON 字符串，NUL 在 JSON 里必须转义），所以不会切错位置。

    Args:
        text: 答复正文。
        elapsed: 耗时秒数；``None`` 表示不记录。

    Returns:
        str: 编码后的正文。
    """
    if elapsed is None:
        return str(text)
    return f'{text}{ELAPSED_SEP}{float(elapsed):.6f}'


def unpack_elapsed(text):
    """:func:`pack_elapsed` 的逆操作。

    Args:
        text: 信号里收到的正文。

    Returns:
        tuple: ``(答复, 耗时秒数)``；没有耗时段时秒数为 ``None``。
    """
    raw = str(text or '')
    head, sep, tail = raw.rpartition(ELAPSED_SEP)
    if not sep:
        return raw, None
    try:
        return head, float(tail)
    except ValueError:
        # 不是我们打包的（理论上不会发生）—— 原样返回，别把正文吃掉
        return raw, None


def is_admin_by_web_license(reply=None, feature='*', read_cache=False) -> bool:
    """判断本机是否拥有管理员权限（判据来自 ``web_license``）.

    判据**只有一条**：``web_license.check`` 的答复里报告的绑定邮箱等于
    :data:`ADMIN_EMAIL`。

    ==========================================  ==========================
    答复                                          判定
    ==========================================  ==========================
    带 ``Email: <ADMIN_EMAIL>``（大小写不敏感）    **管理员**
    邮箱是别的地址 / 没有 ``Email:`` 段            **不是管理员**
    未授权、未绑定、连不上、无 DLL                 **不是管理员**
    ==========================================  ==========================

    ⚠️ 这里**不看** ``lic.is_admin``: 那个判据是本机判据，换一台机器就失效。
    绑定邮箱则跟着授权走，换机器也有效。

    ⚠️ 邮箱必须**在服务端的答复里**核对（而不是读本地配置文件）: 本地文件
    用户可改，服务端答复才是绑定关系本身。服务端只对「判定通过就展示」的
    版本回这个字段，所以取不到就等于没有权限 —— 失败方向是安全的。

    ⚠️ ``read_cache`` 默认给 ``False``（强制向服务端要最新结果）: 结果缓存
    按查询名长期保留，读缓存会拿到「绑定之前」的旧结论，那会把刚绑定到管理员
    邮箱的用户判成没有权限。传 ``False`` 只跳过「读」、不跳过「写」，新结果
    照旧被记住。

    Args:
        reply: ``web_license.check`` 的答复；``None`` 表示本函数自己联网查一次
            （用下面的 ``feature`` / ``read_cache``）。正常调用都用 ``None``。
        feature: 传给 ``web_license.check`` 的功能名，默认 ``'*'``
            （= 「这份许可是谁授的」，而不是「买了哪个模块」）。
        read_cache: 是否允许直接读结果缓存；只有 ``reply`` 为 ``None`` 时才用得上。

    Returns:
        bool: 绑定到 :data:`ADMIN_EMAIL` 返回 True，其余一切情况返回 False。

    Added by DeepSeek, 2026-09-18
    Moved here by DeepSeek, 2026-10-16: 自 ``zmlx/ui/tabs/about.py`` 下沉 —— 原先
    ``ui/tabs/feedback_tool.py`` 要跨控件 import 它，违反「tabs 内控件相互独立」。
    """
    if reply is None:
        try:
            reply = web_license.check(feature, read_cache=read_cache)
        except Exception:
            return False
    try:
        # 解析函数就在本模块（原先是跨模块从 license_register 借用）。
        email = str(bound_info(reply).get('email') or '').strip()
        return email.lower() == ADMIN_EMAIL.lower()
    except Exception:
        return False


def looks_like_email(text):
    """粗判一个字符串像不像邮箱（**只用于筛掉明显不是的**）.

    ⚠️ **刻意极宽松**：只要求「有且仅有一个 ``@``、两边都非空、右边含一个点」。
    真正的邮箱合法性由**服务端**拥有（它才是权威），本地做严格校验只会把将来
    合法的新形式（例如带 ``+`` 的、新顶级域）误杀掉。

    ⚠️ 这里的作用是**过滤脏数据**（名单里混入表头、答复被截断之类），**不是**
    校验用户输入 —— 用户手输的邮箱不经过这个函数，原样发给服务端。

    Args:
        text: 待检查的字符串。

    Returns:
        bool: 像邮箱返回 True。
    """
    text = str(text or '').strip()
    if text.count('@') != 1 or len(text) > 254:
        return False
    local, _, domain = text.partition('@')
    if not local or not domain or '.' not in domain:
        return False
    if domain.startswith('.') or domain.endswith('.'):
        return False
    # 邮箱里不可能有空白
    return not any(ch.isspace() for ch in text)


def merge_emails(*sources):
    """把多组邮箱合并成一份列表：**清洗 + 去重 + 保序**.

    ==============  ====================================================
    规则             说明
    ==============  ====================================================
    清洗             去首尾空白，丢掉不像邮箱的（见 :func:`looks_like_email`）
    去重             比较用 ``lower()``，**大小写不敏感**
    保序             **保留首次出现的原始写法**（用户可能就想用大写）
    顺序             按传入的 ``sources`` 顺序逐个追加
    ==============  ====================================================

    实测::

        ['b@y.org', 'A@X.com', 'a@x.com', 'B@Y.ORG', '  c@z.net  ']
        -> ['b@y.org', 'A@X.com', 'c@z.net']    # 后三个与前面重复

    Args:
        *sources: 若干可迭代对象（列表 / 元组 / ``None``）。``None`` 会被跳过。

    Returns:
        list: 去重后的邮箱列表（顺序 = 首次出现的顺序）。
    """
    seen = set()
    out = []
    for source in sources:
        if not source:
            continue
        for item in source:
            text = str(item or '').strip()
            if not looks_like_email(text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(text)
    return out


def is_user_list(reply) -> bool:
    """判断答复是否为 ``user_list`` 的**成功**正文。

    判据：去掉首尾空白后，**前 6 个字符**忽略大小写等于 ``users:``。

    ⚠️⚠️ **绝不能拿判 ``Count:`` 的那段来判本接口** —— 两者都是 6 个字符、都带
    冒号，只差前面那个词，拿混了会把**成功读成失败**（这是最容易踩的一类事故，
    容易拿混的一对）。

    Args:
        text: 服务端回应正文（任意对象，会被转成字符串）。

    Returns:
        bool: 是 ``user_list`` 的成功正文返回 True。
    """
    return str(reply if reply is not None else '').strip()[
        :len(USER_LIST_TAG)].lower() == USER_LIST_TAG.lower()


def parse_user_list(reply):
    """从 ``user_list`` 的答复里取出邮箱列表.

    成功正文形如（``Dropped:`` / ``Truncated:`` **只在非零时才出现**，所以
    **不要**假设段数固定）::

        Users: 3 | List: a@b.c; d@e.f; g@h.i

    ==================================================  ==================
    答复                                                 返回
    ==================================================  ==================
    以 ``Users:`` 开头且带 ``List:`` 段                   邮箱列表（可能为空）
    其余一切（``Not permitted.`` / ``not available`` /    ``None``
    ``malformed`` / 服务端故障 / 空响应 / 旧 DLL）
    ==================================================  ==================

    ⚠️ 返回 ``None`` 与返回 ``[]`` **含义不同**：``None`` = 「这次没拿到」
    （越权 / 故障），``[]`` = 「拿到了，但名单是空的」。两者在界面上都表现为
    「列表不显示」，但分开能让将来排错时说得清。

    ⚠️ 名单段是 ``; `` 分隔的**字符串**（不是 JSON），这里按 ``;`` 切分即可。

    Args:
        reply: :meth:`zmlx.exts.WebLicense.user_list` 的返回值。

    Returns:
        list | None: 邮箱列表；不是成功答复时返回 ``None``。

    Moved here by DeepSeek, 2026-10-16: 自原 ``zmlx/ui/tabs/check_count_view.py`` 下沉 ——
    原先 ``ui/tabs/feedbacks_view.py``（现并入插件）要跨控件 import 它，违反「tabs 内控件相互独立」。
    """
    text = str(reply if reply is not None else '').strip()
    if not is_user_list(text):
        return None
    for part in text.split(DETAIL_SEP):
        part = part.strip()
        if part.lower().startswith(LIST_TAG.lower()):
            return merge_emails(part[len(LIST_TAG):].split(';'))
    # 以 Users: 开头但一个邮箱段都没有（例如 "The user list is empty."）
    return []


def wrap_text_to_width(text, width_px, font=None):
    """把一段**没有空格可断**的文本（典型是邮箱）按**像素宽度**折成多行.

    ★ 为什么需要它：左侧用户名单是**固定宽度**的小面板（200px），一条邮箱三四十
    个字符一行放不下，而 **Qt 的默认委托只在空格处折行** —— 邮箱里没有空格，于是
    右边被硬裁掉（界面上看到 ``zhangzhaobin@mail.iggcas.ac`` 这种断头串，而真正的
    地址只藏在 tooltip 里）。这里按**字符**量着字宽折，折出来的 ``'\n'`` 是默认
    委托认识的（多行文本的高度它算得对）。

    ⚠️ Qt 在**函数内**才 import：本模块是纯解析/数据工具，模块级拉 Qt 会让每一次
    ``import zmlx.ui.utils.lic_utils`` 都连带拉起界面层（见模块文档的「按需导入」）。

    ⚠️ 只用等宽无关的 ``horizontalAdvance`` 逐个字符累加 —— 中文 / 全角字符的宽度
    自然被算对，不必按「一行多少字」拍一个魔法数。

    Args:
        text: 要折的文本（不含 ``'\n'``；调用方自己拼接多段）。
        width_px: 可用宽度（像素）。小于 1 时原样返回。
        font: 用来量字宽的字体；``None`` 时用应用默认字体。

    Returns:
        str: 用 ``'\n'`` 连接的多行文本；原本一行放得下时**原样返回**。
    """
    text = str(text if text is not None else '')
    if not text or not width_px or width_px < 1:
        return text
    try:
        from zmlx.ui.pyqt import QtGui
        metrics = QtGui.QFontMetrics(font) if font is not None \
            else QtGui.QFontMetrics(QtGui.QFont())
    except Exception:
        # 无界面环境（如纯逻辑自检）：不折行，返回原文 —— 那里也不需要排版
        return text
    lines, line = [], ''
    for ch in text:
        if line and metrics.horizontalAdvance(line + ch) > width_px:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return '\n'.join(lines)


def is_user_list_detail(reply) -> bool:
    """判断答复是否为 ``user_list_detail`` 的**成功**正文（★ 服务端 v3.35）。

    判据：去掉首尾空白后，前 ``len('UsersDetail:')`` 个字符忽略大小写等于它。

    ⚠️ 与 :func:`is_user_list`（``Users:``）**不能互相替代**：前者多 6 个字符，
    拿 ``users:`` 去判新答复会**恒假**（第 6 个字符是 ``d`` 而不是 ``:``）。

    Args:
        reply: 服务端回应正文（任意对象，会被转成字符串）。

    Returns:
        bool: 是 ``user_list_detail`` 的成功正文返回 True。
    """
    return str(reply if reply is not None else '').strip()[
        :len(USER_DETAIL_TAG)].lower() == USER_DETAIL_TAG.lower()


def parse_user_list_detail(reply):
    """从 ``user_list_detail`` 的答复里取出 ``[(姓名, 邮箱)]``（★ 服务端 v3.35）。

    成功正文形如（``Dropped:`` / ``Truncated:`` / ``NamesLimited:`` **只在非零时
    才出现**，所以**不要**假设段数固定）::

        UsersDetail: 3 | List: a@x.com; b@x.com; c@z.net | Names: 张; (none); 李四

    ==================================================  ==================
    答复                                                 返回
    ==================================================  ==================
    以 ``UsersDetail:`` 开头                              ``[(姓名, 邮箱)]``
                                                        （姓名可能是空串）
    其余一切（``Not permitted.`` / 老动作的 ``Users:`` /   ``None``
    服务端故障 / 空响应）                                 
    ==================================================  ==================

    ★ **两段按位置一一对应**：``List:`` 的第 *i* 项配 ``Names:`` 的第 *i* 项。
    姓名段缺失 / 比邮箱段短时，缺的那些项按**空串**处理；多出来的姓名**直接忽略**
    （它们没有对应的邮箱，留着也没有用）。

    ⚠️ 占位 ``(none)`` 还原成**空串** —— 那是服务端的「没写姓名」，不是一个人的
    名字叫 ``(none)``。界面据此只显示邮箱（见 ``CheckCountView._refresh_email_list``）。

    ⚠️ 返回 ``None`` 与返回 ``[]`` 含义不同：``None`` = 「这次没拿到」（越权 /
    故障 / 老服务端），``[]`` = 「拿到了，但名单是空的」。

    Args:
        reply: :meth:`zmlx.exts.WebLicense.user_list_detail` 的返回值。

    Returns:
        list | None: ``[(name, email), ...]``；不是本动作的成功答复时返回 ``None``。
    """
    text = str(reply if reply is not None else '').strip()
    if not is_user_list_detail(text):
        return None

    raw_emails, names = [], []
    for part in text.split(DETAIL_SEP):
        part = part.strip()
        if part.lower().startswith(LIST_TAG.lower()):
            raw_emails = part[len(LIST_TAG):].split(';')
        elif part.lower().startswith(NAMES_TAG.lower()):
            names = part[len(NAMES_TAG):].split(';')

    out, seen = [], set()
    for i, token in enumerate(raw_emails):
        email = token.strip()
        # ⚠️ 与 merge_emails 同一条判据：不像邮箱的直接丢（服务端永远不会给这种，
        #    但解析器不该因为一个脏条目就把整份名单丢掉）。
        if not looks_like_email(email) or email.lower() in seen:
            continue
        seen.add(email.lower())
        name = names[i].strip() if i < len(names) else ''
        if name == NAME_PLACEHOLDER:
            name = ''
        out.append((name, email))
    return out

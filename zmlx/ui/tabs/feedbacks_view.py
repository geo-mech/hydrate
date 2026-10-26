"""反馈记录控件（列出某天的反馈文件名 + 查看单条内容）.

数据来自 ``web_license.list_feedbacks`` 与 ``web_license.get_feedback``
（**本人或管理员**可用）。

界面
----

::

    ┌──────────────────────────────────────────────────────────────┐
    │ 一句话横幅（成功时是条数摘要 / 失败时是服务端原话）            │
    └──────────────────────────────────────────────────────────────┘
    ────────────────────────────────────────────────────────────────
      日期 [2026-10-05] [今天][昨天][刷新文件]
      文件 ┌────────────────────────────┐   内容 ┌────────────────┐
           │ 20261005223007.json        │        │ { "text": ... }│
           │ 20261005110412.json        │        │                │
           └────────────────────────────┘        └────────────────┘
    ▸ 服务器原始答复      ← QGroupBox，**默认收起**：原话 + 往返耗时

★★ **两个动作、两个记号，只差一个 ``s``**（拿混会把成功读成失败）：

- :meth:`zmlx.exts.WebLicense.list_feedbacks` → ``'Feedbacks:'``（**复数**）
- :meth:`zmlx.exts.WebLicense.get_feedback` → ``'Feedback:'``（**单数**）

⚠️ **绝不能**拿提交反馈的记号 ``'Succeed'`` 去判它们 —— **同名不同义**。
判定与解析由本控件的 :class:`_Parsers` 负责（谁用谁实现）。

⚠️ **``Not permitted.`` 是正常业务答复**（HTTP 200）：它刻意抹平了两种含义，
所以本控件**绝不**替服务端编一句「这个邮箱不存在」。

权限模型、响应分段形态与 ``Truncated`` 的含义见
``zmlx/_private/AUTHORIZATION_NOTES.md`` §3 / §9。

耗时的活一律在线程里
--------------------

两个查询各走一个 ``QThread`` 子类，期间按钮全部禁用；结果经信号回到主线程。
⚠️ **不做缓存** —— 每次都是真的发出去。

版式约定
--------

**不在控件里 ``setStyleSheet`` 写 ``color`` / ``background``**（理由同
``check_count_view``）：需要「次要文字」就用 ``setEnabled(False)``，需要边框就用
``palette(mid)``。

Modified by DeepSeek, 2026-10-08
Modified by DeepSeek, 2026-10-10: 控件类 `LicenseFeedback` → `FeedbacksView`，文件
`license_feedback.py` → `feedbacks_view.py`（旧名在 `license_feedback.py` 里留了
转发层）。
"""

import datetime
import json
import time

from zmlx.exts import web_license
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


class _Marks:
    """记号、段名与各种上限（**不实例化**，纯粹当命名空间用）.

    ⚠️ 收进类里而不是平铺在模块级：见 ``widget/AGENTS.md`` 的「模块级内容」——
    模块级只留 import / 类定义 / ``test_1()``，常量带着归属才不会被别的模块
    import 走后改不动。
    """

    #: ``list_feedbacks`` 的成功记号（**复数** = 文件名列表）。
    #: ⚠️ 与 :data:`FILE_TAG` **只差一个 ``s``**；判定实现见
    #: :meth:`_Parsers.list_ok`。
    LIST_TAG = 'Feedbacks:'

    #: ``get_feedback`` 的成功记号（**单数** = 一条反馈的内容）。
    FILE_TAG = 'Feedback:'

    #: 提交反馈（``feedback``）的成功记号。**本模块从不使用它**，只在这里留一条
    #: 对照：它的存在是为了让「不要拿判提交的那段来判读取」这件事在代码里看得见。
    #: ⚠️ 谁都别拿 ``succeed`` 去判 :data:`LIST_TAG` / :data:`FILE_TAG`。
    SUBMIT_TAG = 'Succeed'

    #: 答复里说明段的分隔符（与服务端 ``check.DETAIL_SEP`` 是同一个）。
    DETAIL_SEP = ' | '

    #: ``FileBase64:`` 段的标签 —— 反馈内容的来源。
    #:
    #: ⚠️ **本控件不自己切这一段、也不解 base64**：解码在
    #: :meth:`zmlx.exts.WebLicense.get_feedback_bytes` 里（那是全项目唯一一处
    #: 解码反馈内容的地方，见那个方法的文档）。这里留着它只为了在写日志 / 排错
    #: 时能一眼认出那一段。
    B64_TAG = 'FileBase64:'

    #: 截断标记。
    #:
    #: ⚠️ **它的含义随动作不同**：在 ``list_feedbacks`` 里是「对象超过一页
    #: （1000 个），列表不完整」，在 ``get_feedback`` 里是「内容超过 40 KiB，
    #: 尾巴被丢掉了」。本控件**两个地方都要提示**，但措辞不同（见
    #: :meth:`FeedbacksView._on_list_reply` / ``_on_read_reply``）。
    TRUNCATED = 'Truncated: true'

    #: ``Dropped:`` 段（列举时丢掉了几个不符合命名的对象）。**只有非零才出现**。
    DROPPED_TAG = 'Dropped:'

    #: 日期一律 ``YYYY-MM-DD``（10 个字符）—— 服务端**不收** 8 位紧凑写法。
    DATE_FORMAT = '%Y-%m-%d'

    #: 反馈文件名里的日戳格式（14 位：``YYYYMMDDHHMMSS``）。
    #:
    #: ⚠️ 只用于**显示**（把 ``20260928223007.json`` 显示成更好读的形式），
    #: **绝不**用它拼请求 —— 发给服务端的永远是**原样的裸文件名**。
    STAMP_FORMAT = '%Y%m%d%H%M%S'

    #: 邮箱输入框的初始占位文本。
    EMAIL_PLACEHOLDER = 'you@example.com'

    #: 二进制内容在界面上最多显示多少字节的 hex（再多就没人看了）。
    HEX_PREVIEW_BYTES = 256

    #: 附带说明的最大长度（超过就截断显示 —— 那是**别人的**反馈正文）。
    TEXT_PREVIEW_CHARS = 200000


class _Parsers:
    """反馈答复的解析与格式化（**全是纯函数**，不联网、不碰界面）.

    ★ 放在这里是为了**可离线单测**：喂一段文本、看结论，不需要 DLL、不需要网络。

    ★★ **判定与解析的实现就在这里**（而不在 ``zmlx.exts._lic``）：它们的唯一
    消费者是本控件，按项目「谁用谁实现」的分工收在这里。

    ⚠️⚠️ **唯一不在本类的是 base64 的解码**：那一步在
    :meth:`zmlx.exts.WebLicense.get_feedback_bytes` 里，因为
    ``FileBase64:`` 段是**服务端协议的一部分**，该关在协议层里 —— 控件只拿到
    **已解码的字节**，从头到尾看不见 base64。所以本类的 :meth:`decode` 是个
    薄封装（它的价值在于把「没拿到」与「空文件」两种返回**分开解释**）。

    ⚠️ **记号判定的写法只有一种**：去掉首尾空白后看**开头那几个字符**（不区分
    大小写），绝不 ``==`` 整串 —— 成功正文后面还跟着若干 `` | `` 段，严格比较
    是一条会随服务端演进而失效的隐含假设。
    """

    @staticmethod
    def list_ok(reply):
        """答复是否为 ``list_feedbacks`` 的成功正文。

        判据：去掉首尾空白后，前 **10** 个字符忽略大小写等于 ``feedbacks:``。

        ⚠️⚠️ **不要改用 ``feedback:``**（``get_feedback`` 的记号，只有 9 个
        字符）：拿混了会把**成功读成失败**。也**不要**用 ``succeed``（那是提交
        反馈的记号，同名不同义）。

        ⚠️ 只查开头、**不查整句**：失败文案里也可能出现 ``feedbacks`` 这个词，
        用「包含」判断会把它们误判成成功。

        Args:
            reply: 服务端答复正文（任意类型，会被转成字符串）。

        Returns:
            bool: 是 ``list_feedbacks`` 的成功正文返回 True。
        """
        text = reply if isinstance(reply, str) else str(reply)
        tag = _Marks.LIST_TAG
        return text.strip()[:len(tag)].lower() == tag.lower()

    @staticmethod
    def read_ok(reply):
        """答复是否为 ``get_feedback`` 的成功正文。

        判据：去掉首尾空白后，前 **9** 个字符忽略大小写等于 ``feedback:``。

        ⚠️⚠️ 与 :meth:`list_ok` **只差一个 ``s``**，且与提交反馈的
        ``Succeed`` **完全不同**（同名不同义）—— 这两个是最容易拿混的一对。

        Args:
            reply: 服务端答复正文（任意类型，会被转成字符串）。

        Returns:
            bool: 是 ``get_feedback`` 的成功正文返回 True。
        """
        text = reply if isinstance(reply, str) else str(reply)
        tag = _Marks.FILE_TAG
        return text.strip()[:len(tag)].lower() == tag.lower()

    @staticmethod
    def parse_files(reply):
        """从列举答复里取出**裸文件名列表**。

        ``Files:`` 段是 ``; `` 分隔的**裸文件名**串（不是 JSON）。

        ★ **0 条时那一段整段不出现**（服务端刻意如此：光秃秃的 ``Files:`` 会让人
        以为渲染坏了，而首段的 ``Feedbacks: 0`` 已经把话说清楚了），所以这里回
        **空列表** —— 那不是错误，是「那天没有反馈」。

        ⚠️ 段数**不固定**（``Dropped:`` / ``Truncated:`` 只在异常时出现），所以
        必须**按段名找**，不能按下标取。

        Args:
            reply: ``list_feedbacks`` 的答复正文。

        Returns:
            list: 裸文件名列表（如 ``['20260928223007.json']``）；答复不是成功
            正文时返回 ``[]``。
        """
        if not _Parsers.list_ok(reply):
            return []
        text = str(reply if reply is not None else '').strip()
        for seg in text.split(_Marks.DETAIL_SEP):
            seg = seg.strip()
            if seg.lower().startswith('files:'):
                body = seg[len('files:'):].strip()
                return [n for n in (x.strip() for x in body.split(';')) if n]
        return []

    @staticmethod
    def is_truncated(reply):
        """答复里有没有 ``Truncated: true`` 段。

        ⚠️⚠️ **解析内容之前必须先问它**：被截断的内容**必然**缺右括号，
        ``json.loads`` 会抛异常 —— 而那是**数据事实**（服务端按 40 KiB 截的），
        不是程序错误。

        ⚠️ 它的含义**随动作不同**：在 ``list_feedbacks`` 里是「对象超过一页
        （1000 个），列表不完整」；在 ``get_feedback`` 里是「内容超过读取上限，
        尾巴被丢掉了」。调用方写文案时要分开（见
        :meth:`FeedbacksView._on_list_reply` / ``_on_read_reply``）。

        Args:
            reply: 服务端答复正文（任意类型）。

        Returns:
            bool: 含该段返回 True。
        """
        text = reply if isinstance(reply, str) else str(reply)
        return _Marks.TRUNCATED in text

    @staticmethod
    def decode(reply):
        """把**已经拿到的**答复里的内容解成原始字节。

        ★★ **不重新联网**：本方法吃的是后台线程**刚刚取回来的那一句答复** ——
        两个接口都不做缓存、每次调用都真的发出去，在这里再调一次
        ``get_feedback()`` 会**平白多打一次服务端**，还可能读到与屏幕上那句
        不同的内容。所以真正的 base64 解码走
        :meth:`zmlx.exts.WebLicense.decode_feedback` —— 那是个**只吃一句答复**
        的静态入口，仍然关在 ``WebLicense`` 里（``FileBase64:`` 段属于服务端
        协议，不该漏到界面层）。

        ⚠️ 三条返回值**含义各不相同**，调用方必须分开处理：

        - ``None``：业务拒绝 / 连不上（**不是**成功正文）；
        - ``b''``：那个文件是 **0 字节** —— 这是**成功**；
        - 其余：原始字节（服务端**不解析 JSON、不解码 UTF-8**，所以它可能是
          任何东西）。

        Args:
            reply: ``get_feedback`` 的答复正文（**已经拿到的**那一句）。

        Returns:
            bytes | None: 原始字节，见上。
        """
        return web_license.decode_feedback(reply)

    @staticmethod
    def find_display_name(text):
        """从 ``Feedback: <文件名>`` 那段里取出文件名（显示用）。

        ⚠️ 取不到就返回空串，**绝不猜**：文件名本该由首段给出，猜错了会让人
        以为自己在看另一个文件的内容。

        Args:
            text: ``get_feedback`` 的答复正文。

        Returns:
            str: 裸文件名（如 ``'20260928223007.json'``）；取不到时为空串。
        """
        text = str(text or '').strip()
        if not _Parsers.read_ok(text):
            return ''
        for part in text.split(_Marks.DETAIL_SEP):
            part = part.strip()
            if part.lower().startswith(_Marks.FILE_TAG.lower()):
                return part[len(_Marks.FILE_TAG):].strip()
        return ''

    @staticmethod
    def format_stamp(file_name):
        """把反馈文件名里的 14 位日戳渲染成好读的形式（**纯显示**）.

        实测::

            '20260928223007.json' -> '2026-09-28 22:30:07'
            'bad.json'            -> ''            # 形态不对就不显示

        ⚠️ **只用于显示**：发给服务端的永远是**原样的裸文件名**（服务端对 ``file``
        有精确的形态闸，本地改一个字符就读不到了）。

        Args:
            file_name: 裸文件名。

        Returns:
            str: 形如 ``'2026-09-28 22:30:07'``；日戳形态不对时返回空串。
        """
        stem = str(file_name or '').strip()
        if stem.lower().endswith('.json'):
            stem = stem[:-len('.json')]
        if len(stem) != 14 or not stem.isdigit():
            return ''
        try:
            moment = datetime.datetime.strptime(stem, _Marks.STAMP_FORMAT)
        except ValueError:
            return ''
        return moment.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_content(raw):
        """把**原始字节**渲染成界面上要显示的 ``(文本, 说明)``.

        ★ 这是本控件最核心的一段，处理顺序**固定不可换**：

        ===================================  ==================================
        输入                                  输出
        ===================================  ==================================
        ``None``                              ``('', '没拿到内容。')``
        ``b''``                               ``('', '（这个文件是空的）')``
        合法 UTF-8 且是合法 JSON              **拆成「元数据 + text」两块**
        合法 UTF-8 但不是 JSON                原样文本，说明「不是合法 JSON」
        非 UTF-8（二进制 / 坏字节）            hex 摘要，说明「不是文本」
        ===================================  ==================================

        ★★ **JSON 记录会被拆开**（见 :meth:`_Parsers.split_json`）：顶层有字符串
        字段 ``text`` 时，「``text`` 以外的字段」与「``text`` 的内容」分成两块
        显示 —— 前者是一小段元数据（时间 / 机器码 / 用户…），后者是用户真正写的
        那一段（通常很长、且带换行）。两者混在一份缩进 JSON 里时，正文会被挤到
        屏幕最下面，还得在引号里找 ``\n``。**拆不出 ``text`` 时不拆**（退回整份
        缩进 JSON）—— 那说明这份记录的形态不是本服务写的。

        ⚠️ **0 字节与「没拿到」是两件事**：前者是**成功**（服务端那个文件就是空的），
        后者是业务拒绝。所以它们返回的说明文字不同，界面也不会把它们画成一个样。

        ⚠️ **JSON 解析失败不是错误**：服务端的设计就是「桶里是什么就给什么」，
        内容坏掉时它照样把原始字节给你，由你来判断。所以这里退回原文并**说清楚**
        它是原文，而不是弹一个「解析失败」。

        ⚠️ ``json.loads`` 之前**不判断截断**：截断的标记由调用方
        （:meth:`FeedbacksView._on_read_reply`）单独处理并写进横幅 —— 因为
        「已截断」是**整个答复**的属性，不是这一段的属性。

        Args:
            raw: :meth:`_Parsers.decode` 的返回值（源头是
                ``WebLicense.get_feedback_bytes()`` 解出来的字节）。

        Returns:
            dict: 四个键（**永远是这四个**，界面据此决定怎么摆）：

            - ``'meta'``：上半区要显示的文本（元数据 / 整份缩进 JSON / hex 摘要；
              没有上半区时是空串）；
            - ``'text'``：下半区要显示的文本（``text`` 字段的内容；没有下半区时
              是空串）；
            - ``'note'``：一句说明，空串表示「一切正常」；
            - ``'split'``：**是否真的拆开了**。``False`` 时界面退回**单区**显示
              （把 ``meta`` 与 ``text`` 拼起来就是完整内容）。
        """
        if raw is None:
            return {'meta': '', 'text': '', 'split': False,
                    'note': '没拿到内容（答复不是成功正文，见下面的原始答复）。'}
        if raw == b'':
            return {'meta': '', 'text': '', 'split': False,
                    'note': '（这个文件是空的）'}

        text = None
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = None

        if text is None:
            # 非 UTF-8：显示 hex 摘要。⚠️ 绝不 ``decode(errors='replace')`` 后
            # 当正文显示 —— 那会把二进制垃圾渲染成一屏问号，比说「这是二进制」
            # 更难判断。
            head = raw[:_Marks.HEX_PREVIEW_BYTES]
            hex_text = ' '.join(f'{byte:02x}' for byte in head)
            more = '' if len(raw) <= _Marks.HEX_PREVIEW_BYTES else \
                f'\n…（共 {len(raw)} 字节，这里只显示前 ' \
                f'{_Marks.HEX_PREVIEW_BYTES} 字节）'
            return {'meta': hex_text + more, 'text': '', 'split': False,
                    'note': f'这个文件不是文本（{len(raw)} 字节），'
                            f'下面是它的十六进制摘要。'}

        if len(text) > _Marks.TEXT_PREVIEW_CHARS:
            text = text[:_Marks.TEXT_PREVIEW_CHARS]
            note = f'内容很长，界面只显示前 {_Marks.TEXT_PREVIEW_CHARS} 个字符。'
        else:
            note = ''

        # ★ 先试着当 JSON：合法就**拆成元数据 + text**（拆不出就整份缩进）
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
        if parsed is not None:
            split = _Parsers.split_json(parsed)
            if split is not None:
                meta, body = split
                return {'meta': meta, 'text': body, 'split': True, 'note': note}
            try:
                pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                pretty = text
            return {'meta': pretty, 'text': '', 'split': False, 'note': note}

        # 不是 JSON —— 原样显示，**并说清楚**（这正是服务端刻意的设计）
        not_json = '内容不是合法 JSON，下面是原文。'
        return {'meta': text, 'text': '', 'split': False,
                'note': f'{note} {not_json}'.strip()}

    @staticmethod
    def split_json(parsed):
        """把一条解析好的 JSON 记录拆成 ``(元数据文本, text 内容)``。

        ★ **只有顶层是对象、且带一个字符串 ``text`` 字段时才拆**；其余一律回
        ``None``（调用方随即退回「整份缩进 JSON」）。判据刻意这么紧，是因为
        「拆开」只有在**知道 ``text`` 是什么**时才有意义：

        ==========================================  ==============
        输入                                          结果
        ==========================================  ==============
        ``{'ts':…, 'text': '正文…', …}``              ``(元数据 JSON, '正文…')``
        顶层是列表 / 数字 / 字符串                     ``None``（不拆）
        没有 ``text`` 字段                             ``None``（不拆）
        ``text`` 不是字符串（数字 / 对象 / null）      ``None``（不拆）
        ==========================================  ==============

        ⚠️ **``text`` 不是字符串时不拆**：那种记录的 ``text`` 是数据而不是正文
        （例如某个版本把它写成了对象）。硬把它塞进「正文区」会显示成一串没缩进的
        JSON，反而不如整份缩进清楚。

        ⚠️ **剩下的字段一个都不丢**：元数据那边是**去掉 ``text`` 之后的整份
        对象**（缩进 JSON），所以拆开只是「把 ``text`` 挪了个地方」，不是过滤。

        ⚠️ **``text`` 为空串时照样算拆开**（元数据非空、正文区空着）—— 那说明
        这份记录本来就只写了元数据，界面如实呈现即可。

        Args:
            parsed: :func:`json.loads` 的结果（任意类型）。

        Returns:
            tuple | None: ``(元数据文本, text 内容)``；不该拆时返回 ``None``。
        """
        if not isinstance(parsed, dict):
            return None
        body = parsed.get('text')
        if not isinstance(body, str):
            return None
        # ⚠️ 复制一份再 pop：**绝不改动调用方传进来的那个对象**（它还要用来
        #    显示整份 JSON / 被别处复用）。
        rest = {key: value for key, value in parsed.items() if key != 'text'}
        try:
            meta = json.dumps(rest, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return None
        return meta, body

    @staticmethod
    def full_json(raw):
        """把原始字节渲染成**整份缩进 JSON**（「完整原文」区用）。

        ★ **它只负责「桶里那份文件的完整形态」**：拆分显示把 ``text`` 挪到了
        下面的框里，而这个函数给出**没挪之前**的样子 —— 字段顺序、``text`` 在
        整份记录里的位置都能对照。

        ⚠️ 解不出来（不是 UTF-8 / 不是 JSON）就回**空串** —— 那时调用方**整块
        隐藏**「完整原文」区：正文区给出的已经是全文，再摆一份副本只会让人以为
        有两份不同的东西。

        Args:
            raw: :meth:`_Parsers.decode` 的返回值（原始字节）。

        Returns:
            str: 缩进后的整份 JSON；拿不到时返回空串。
        """
        if not raw:
            return ''
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            return ''
        try:
            parsed = json.loads(text)
        except ValueError:
            return ''
        try:
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return ''


class _Layout:
    """版式常量（**不实例化**，纯粹当命名空间用）.

    ⚠️ 这里**不写任何色值**：见模块文档的「版式约定」。
    """

    MARGIN = 12
    GAP = 8
    BUTTON_HEIGHT = 34

    #: 左侧列表的固定宽度（像素）。
    #:
    #: ⚠️ 与 ``check_count_view.py`` 取同一个值：两个页面并排看时左侧栏**对齐**，
    #: 而固定宽度也保证邮箱 / 文件名不会把右侧的正文挤扁。
    LIST_WIDTH = 200

    #: 左侧各列表的最小高度（像素）——低于这个高度它自己出滚动条。
    LIST_MIN_HEIGHT = 90

    #: 两个文本框（元数据 / text）各自的**最小**高度（像素）。
    #:
    #: ⚠️ 上下两块都是本页的弹性元素（``Expanding`` + 分隔条可拖动）：窗口变高时
    #: 一起变高，变矮时**先缩**，各自缩到这个高度为止 —— 其余各行（横幅 / 表单 /
    #: 原始答复）始终完整显示。
    #: **不要**给它们设 ``maximumHeight``：那会把它们钉死、下方留出一片空白。
    #:
    #: ⚠️ 两块都设了最小高度 + ``setChildrenCollapsible(False)``：**不许任何一块
    #: 被拖到 0** —— 折没了用户就找不到那条分隔线，再也拖不回来。
    META_MIN_HEIGHT = 90
    TEXT_MIN_HEIGHT = 120

    #: 拆分显示时正文那一块的**初始**高度（像素）；元数据那块按它的最小高度起步。
    TEXT_HINT_HEIGHT = 320

    #: 分隔条宽度（像素）。默认太细，鼠标不好抓。
    SPLITTER_HANDLE = 8

    #: 「服务器原始答复」固定高度：那里只有「原话 + 往返耗时」两行。
    STATUS_VIEW_HEIGHT = 62

    #: 「完整原文」那块的高度（像素）。它是**整份 JSON**（含很长的 text），
    #: 比「原始答复」那块需要多几行，但因为默认收起，给一个够看的固定高度即可。
    FULL_VIEW_HEIGHT = 180

    #: 状态提示条的样式：**只含边框与内边距，没有任何 color / background**。
    BANNER_QSS = 'border: 1px solid palette(mid); border-radius: 6px;'

    #: 正文区**空着**（还没选中任何反馈）时，占位文字显示的本页使用方法。
    #:
    #: ★ **完整的那一份放在上面的「元数据」框里**（:data:`USAGE_HINT`），下面的
    #: text 框只写自己那一句（:data:`USAGE_HINT_TEXT`）。原因只有一个，但很硬：
    #: **下面那个框随时可能整块隐藏**（``_text_box`` 在"不拆分"时被藏起来 ——
    #: 而清空之后正是这种状态），提示若挂在它上面，用户就什么都看不到了。
    #: 上面那个框则**始终可见**，所以完整说明放它那里才稳。
    #:
    #: ⚠️⚠️ **两句之间不许互相引用**（踩过）：原先上面写「完整的使用方法见下面的
    #: text 框」，可那时下面那个框**正被隐藏着** —— 等于让用户去看一个不存在的
    #: 东西。两处如今各说各的：上面给完整步骤，下面只说"选中后这里显示 text"。
    #:
    #: ⚠️ 之所以**用占位文字而不是另加一个提示控件**：占位文字天生「有内容就消失、
    #: 没内容就出现」，不需要额外的显隐逻辑去与正文抢可见性（那种同步最容易漏一处、
    #: 表现为「有内容了提示还挂着」）。⚠️ 但**占位文字只在文本框为空时显示**，
    #: 所以 :meth:`_clear_content` 必须真的把 ``setPlainText('')`` 调到（它做到了）。
    #:
    #: ⚠️ 写的是**操作步骤**，不是"这里显示什么"的说明：空着的时候用户需要知道的是
    #: 「下一步点哪里」，而不是"这块区域将来会放什么"。
    USAGE_HINT = (
        '使用方法：\n'
        '  1. 在左侧选择邮箱（默认是本机绑定的那个）；\n'
        '  2. 在左侧选择日期（或点日期下面的「今天」/「昨天」，再按「刷新文件」）；\n'
        '  3. 点左下角的「刷新文件」，左侧会列出这一天该邮箱提交的反馈文件；\n'
        '  4. 点其中一个文件名，这里就显示它的内容 ——\n'
        '     上面是元数据（text 以外的字段），下面是 text 正文。\n'
        '\n'
        '提示：\n'
        '  · 非管理员只能看自己绑定的邮箱。\n'
        '  · 反馈内容只在此处显示，不会保存到本地。'
    )

    #: 未选中反馈时，**下面的 text 框**的占位文字。
    #:
    #: ⚠️ 只写自己这一句、**绝不引用别处**（完整步骤在上面的元数据框里，见
    #: :data:`USAGE_HINT`）：本框随时可能被整块隐藏，那时引用就指向了不存在的东西。
    USAGE_HINT_TEXT = (
        '选中反馈后，这里显示它的 text 正文。'
    )


#: 正在后台跑的线程（模块级强引用）。
#:
#: ⚠️⚠️ **线程的 parent 绝不能是本控件**：标签页关闭时控件会被
#: ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，parent 是本控件的线程会
#: **跟着一起被析构**；而 Qt 规定「正在运行的 QThread 不能被销毁」，请求还没
#: 回来时就会直接 abort::
#:
#:     QThread: Destroyed while thread is still running
#:
#: 这是**进程级崩溃**，不是异常，``try/except`` 兜不住。本控件的每个请求最长
#: 30 秒，关标签时线程几乎必然还在跑。``closeEvent`` 里的 ``wait()`` 也兜不住
#: —— ``close_tab`` 走 ``deleteLater()``，**根本不发** ``closeEvent``。
#:
#: 挂在这里线程一定能跑完；控件销毁后迟到结果由 :func:`_is_deleted` 拦掉。
#: （与 ``check_count_view.py`` / ``demo_view.py`` 是同一条纪律。）
_RUNNING_WORKERS = []


def _forget_worker(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）."""
    try:
        _RUNNING_WORKERS.remove(worker)
    except ValueError:
        pass


def _is_deleted(obj):
    """判断一个 Qt 对象的底层 C/C++ 对象是否已经被销毁.

    ⚠️ **为什么需要它**：本控件的结果槽是**用 lambda 连的**
    （``connect(lambda ...: self._on_list_reply(...))``）。Qt 只能对「接收者是
    QObject 的**绑定方法**」做自动断连 —— lambda 没有接收者对象，控件被
    ``deleteLater()`` 销毁后**连接依然有效**，线程回来时那个 lambda 照样被调用，
    于是在一个已经死掉的控件上碰子控件，抛::

        RuntimeError: wrapped C/C++ object of type QPlainTextEdit has been deleted

    ⚠️ 与 ``check_count_view.py`` 里那个**同名同实现**（照抄而非 import：两个控件
    互不依赖，将来各自演进时不会互相牵连）。改动其一请**两处一起改**。

    Args:
        obj: 任意 Qt 对象（QWidget 等）。

    Returns:
        bool: 底层对象已被销毁返回 True。
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


def _merge_emails(*sources):
    """把多组邮箱合并成一份列表：**清洗 + 去重 + 保序**（纯函数）.

    规则与 ``lic_utils.merge_emails`` 逐字相同（照抄而非 import，理由同
    :func:`_is_deleted`）：去首尾空白、丢掉不像邮箱的、按 ``lower()`` 去重、
    **保留首次出现的原始写法**。

    ⚠️ 「像不像邮箱」**刻意极宽松**（有且仅有一个 ``@``、两边非空、域名含点）：
    真正的合法性由**服务端**拥有，本地严格校验只会把将来合法的新形式误杀掉。
    这里的作用是**过滤脏数据**（名单里混入表头之类），**不是**校验用户输入。

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
            if text.count('@') != 1 or len(text) > 254:
                continue
            local, _, domain = text.partition('@')
            if not local or not domain or '.' not in domain:
                continue
            if domain.startswith('.') or domain.endswith('.'):
                continue
            if any(ch.isspace() for ch in text):
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(text)
    return out


def _find_tag(text, tag):
    """从答复里取出以 ``tag`` 开头的那个**段**（取不到返回空串）.

    ⚠️ 段数**不固定**（``Dropped:`` / ``Truncated:`` 只在异常时出现），所以必须
    **按段名找**，不能按下标取。

    Args:
        text: 服务端答复正文。
        tag: 段名（含冒号），例如 ``'Dropped:'``。

    Returns:
        str: 段内内容（已去首尾空白）；没有该段时返回空串。
    """
    for part in str(text or '').split(_Marks.DETAIL_SEP):
        part = part.strip()
        if part.lower().startswith(tag.lower()):
            return part[len(tag):].strip()
    return ''


class _ListWorker(QtCore.QThread):
    """在后台线程里列一次某天的反馈文件名（**绝不碰界面**）.

    与 ``check_count_view._Worker`` 同构：线程里只发请求，结果用信号发回主线程。

    ⚠️ ``list_feedbacks`` 按契约**永不抛异常**，下面那个 ``except`` 只是防御：
    异常真逃出 :meth:`run` 的话线程会静默死掉、信号永不发出，按钮就永远停在
    禁用状态 —— 看起来像程序卡死。

    Attributes:
        sig_done: 信号，携带 ``(答复, 耗时文本)``。耗时单独一个参数、不挤进答复
            正文里，免得污染「只看开头」的成功判定。
    """

    sig_done = QtCore.pyqtSignal(str, str)

    def __init__(self, date, email, parent=None):
        """初始化。

        Args:
            date: 日期（``YYYY-MM-DD``）；空串 = 服务端默认（北京时间今天）。
            email: 看**谁**的反馈（原样转交，本地不 trim、不校验）。
            parent: Qt 父对象。⚠️ 正常调用应当**留空**，理由见 :data:`_RUNNING_WORKERS`。
        """
        super(_ListWorker, self).__init__(parent)
        self._date = date
        self._email = email
        self.setObjectName('FeedbacksViewListWorker')

    def run(self):
        """线程体：发一次请求并把答复发回主线程。

        ⚠️ 耗时在**这里**量：量的必须是「请求本身用了多久」。若改成回到主线程
        再掐表，量到的会变成「界面等了多久」，里面混着信号跨线程的排队延迟。
        """
        start = time.perf_counter()
        try:
            reply = web_license.list_feedbacks(self._date, self._email)
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：list_feedbacks 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        from zmlx.ui.utils.lic_utils import format_elapsed

        self.sig_done.emit(text, format_elapsed(time.perf_counter() - start))


class _ReadWorker(QtCore.QThread):
    """在后台线程里取一条反馈的内容（**绝不碰界面**）.

    与 :class:`_ListWorker` 同构，只是换成 ``get_feedback``。

    ⚠️⚠️ **``file`` 原样转交、绝不改写**：服务端对文件名有精确的形态闸
    （14 位纯数字 + ``.json``），本地改一个字符（例如补上路径、去掉后缀）就会
    读不到 —— 而那是**静默**的失败方向（表现为「这个文件不存在」）。

    Attributes:
        sig_done: 信号，携带 ``(答复, 耗时文本)``。
    """

    sig_done = QtCore.pyqtSignal(str, str)

    def __init__(self, file_name, email, parent=None):
        """初始化。

        Args:
            file_name: **裸文件名**（如 ``'20260928223007.json'``），原样转交。
            email: 看**谁**的反馈（原样转交）。
            parent: Qt 父对象。⚠️ 正常调用应当**留空**，理由见 :data:`_RUNNING_WORKERS`。
        """
        super(_ReadWorker, self).__init__(parent)
        self._file = file_name
        self._email = email
        self.setObjectName('FeedbacksViewReadWorker')

    def run(self):
        """线程体：发一次请求并把答复发回主线程。"""
        start = time.perf_counter()
        try:
            reply = web_license.get_feedback(self._file, self._email)
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：get_feedback 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        from zmlx.ui.utils.lic_utils import format_elapsed

        self.sig_done.emit(text, format_elapsed(time.perf_counter() - start))


class _PrefillWorker(QtCore.QThread):
    """在后台线程里取「本机已绑定的邮箱」（**绝不碰界面**）.

    取邮箱要联网（``web_license.check``，最长 30 秒），放进 UI 线程会让「打开
    本页面」直接卡住。取不到就发空串 —— 那是常态（没联网 / 没绑定）。

    Attributes:
        sig_done: 信号，携带邮箱（可能为空串）。
    """

    sig_done = QtCore.pyqtSignal(str)

    def __init__(self, owner=None, parent=None):
        """初始化。

        Args:
            owner: 提供 :meth:`FeedbacksView._prefill_email` 的控件。
                ⚠️ 这只是**取值用的引用**，不是 Qt parent。
            parent: Qt 父对象。⚠️ 正常调用应当**留空**，理由见 :data:`_RUNNING_WORKERS`。
        """
        super(_PrefillWorker, self).__init__(parent)
        self._owner = owner
        self.setObjectName('FeedbacksViewPrefillWorker')

    def run(self):
        """线程体：取邮箱并发回主线程（任何异常都变成空串）。"""
        try:
            email = self._owner._prefill_email()
        except Exception as err:      # 防御性：正常路径不会触发
            print(f'Error (when prefill email): {err}')
            email = ''
        self.sig_done.emit(str(email or ''))


class _UserListWorker(QtCore.QThread):
    """在后台线程里取「服务端用户名单」（**绝不碰界面**）.

    ⚠️⚠️ **必须在后台线程**：``user_list`` **不做缓存、每次调用都真的发出去**，
    单次最长阻塞 30 秒。放进 UI 线程的话，
    「打开本页面」会直接卡住。

    ⚠️ **非管理员拿到的是 ``Not permitted.``**（HTTP 200 的**正常业务答复**），
    所以这里**不发错误信号**：结果一律通过 :attr:`sig_done` 交回文本。

    Attributes:
        sig_done: 信号，携带服务端答复正文。
    """

    sig_done = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """初始化。

        Args:
            parent: Qt 父对象。⚠️ 正常调用应当**留空**，理由见 :data:`_RUNNING_WORKERS`。
        """
        super(_UserListWorker, self).__init__(parent)
        self.setObjectName('FeedbacksViewUserListWorker')

    def run(self):
        """线程体：取名单并发回主线程。"""
        try:
            from zmlx.ui.utils.lic_utils import is_user_list_detail
            # ★ v3.35：优先要「邮箱 + 姓名」；拿不到再退回旧动作（理由见
            #   ``check_count_view._UserListWorker.run``：老服务端会把未知 action
            #   当成一次许可查询）。
            reply = web_license.user_list_detail()
            if not is_user_list_detail(reply):
                # ⚠️ 实测偶发**空答复**（2026-10-18）—— 重试一次再退回旧动作，
                #    理由见 check_count_view._UserListWorker.run 那处注释。
                retry = web_license.user_list_detail()
                reply = retry if is_user_list_detail(retry) else web_license.user_list()
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：user_list 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        self.sig_done.emit(text)


class FeedbacksView(QtWidgets.QWidget):
    """反馈查看控件：一个日期 + 一个邮箱 → 一批文件名 → 一条反馈的内容。

    ★ 与「授权记录」（``check_count_view.CheckCountView``）是**同构的兄弟**：同一套
    权限模型、同一条线程纪律、同一套版式约定。用户能感知的唯一差别是内容形态
    —— 那边是柱状图，这边是**一批文件 + 一段文本**。

    ⚠️ 类名原先叫 ``LicenseFeedback``（由 ``show_license_feedback`` 那个 gui 命令
    的名字带出来的），但它与授权无关：``web_license`` 只是**碰巧**承载着反馈的读写
    动作，这个控件干的是"看反馈"。故与 ``gui.show_feedbacks_view`` 一并改名。

    首次显示时会自动查一次（见 :meth:`showEvent`），并在构造时预填邮箱与日期：
    默认看的是**本机自己**绑定的那个邮箱与**北京时间的今天**。

    ⚠️ **本控件不实现** :meth:`save_file`：显示的可能是**别人的**私密反馈正文，
    绝不能因为菜单「文件 → 保存」被悄悄写进输出目录。
    """

    def __init__(self, parent=None, *, email=None, date=None):
        """初始化控件。

        Args:
            parent: Qt 父对象。
            email: 预填的邮箱；``None`` 表示尝试从本机已绑定的授权里取
                （取不到就留空，用户自己填）。
            date: 预填的日期（``YYYY-MM-DD``）；``None`` 表示用**北京时间的今天**
                —— 服务端按 ``check.day_stamp()`` 取的那一个，与反馈文件名同源。
        """
        super(FeedbacksView, self).__init__(parent)

        self._list_worker = None       # 后台列文件名的线程（持有引用，防被 GC）
        self._read_worker = None       # 后台读内容的线程（同上）
        self._prefill_worker = None    # 后台取邮箱的线程（同上）
        self._user_list_worker = None  # 后台取名单的线程（同上）
        self._busy = False             # 有请求在飞：按钮禁用，防连点
        self._auto_checked = False     # 首次显示时的「查一次」是否已跑过
        self._last_query = None        # 上一次真正发出去的 (email, date)
        self._bound_email = None       # 本机绑定的邮箱（预填线程拿到后回填）
        self._server_emails = None     # 服务端名单；None = 本次运行还没拿到
        #: 名单里的**姓名**：邮箱（小写）-> 姓名（★ 服务端 v3.35 才有）。
        self._server_names = {}
        self._files = []               # 当前那一批文件名（供重放 / 排错）
        #: 查询代次：每发起一次 +1。旧线程回来时若代号对不上就**丢弃它的结果**
        #: —— 用于「用户在列表里连点了几个文件名 / 几个日期」的情形，
        #: 见 :meth:`FeedbacksView._abandon_current_query`。
        self._query_generation = 0
        #: 右键菜单的扩展点：外部可以往里塞自己的 QAction（与
        #: ``check_count_view.py`` 的 ``context_actions`` 是同一套写法）。
        #: ⚠️ **必须在这里初始化**：``get_context_menu()`` 会读它，一旦漏了，
        #: 右键就会抛 ``AttributeError`` —— 而 PyQt 对**从事件处理器里逃出的**
        #: 异常会调用 ``qFatal()`` 直接终止进程，不是打印一行报错就算了。
        self.context_actions = []

        self.setWindowTitle('反馈记录')

        self._build_ui()
        self.set_date(date if date else self._today_str())
        if email is not None:
            # ⚠️ 这里写的是**只读回显框**（``email_view``，表单里那个），不是另一个
            #    可编辑输入口 —— 邮箱以左侧列表 / 这一份为准。
            #    （⚠️ 别写成 ``email_edit``：本控件没有那个成员，那是
            #    ``check_count_view`` 的写法，误抄会直接 AttributeError。）
            self.email_view.setText(str(email))
            self._bound_email = str(email).strip() or None
        self._refresh_email_list()
        self._update_buttons()

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------

    def _build_ui(self):
        """搭出整个界面（只在这里创建控件）。

        尺寸策略：**内容直接铺在控件上，不套滚动区**——全屏只有一个弹性元素：

        - **正文区**是唯一的伸缩项（``stretch=1`` + ``Expanding``）：窗口变高时
          它变高，变矮时它**先缩**，缩到 :data:`_Layout.TEXT_MIN_HEIGHT` 为止；
        - 其余各行（横幅 / 表单 / 原始答复）都是固定高度，**永不参与拉伸**。

        ⚠️ **不要**去覆写别的控件的 ``sizeHint``、更不要改 ``__class__``
        （``check_count_view.py`` 里真踩过，会偶发卡死）：正文区这里只需要
        ``setMinimumHeight`` + ``Expanding``。
        """
        shell = QtWidgets.QHBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # ---- 左：邮箱 + 日期 + 文件列表 ----
        shell.addWidget(self._build_side_panel())

        # ---- 右：主体 ----
        right = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(right)
        outer.setContentsMargins(_Layout.MARGIN, _Layout.MARGIN,
                                 _Layout.MARGIN, _Layout.MARGIN)
        outer.setSpacing(_Layout.GAP)

        # ⚠️ 这里**不放**标题与说明文字：标签页顶部已经有「反馈记录」这个标题，
        #    控件内再写一遍是重复的。首屏直接给横幅 + 表单 + 正文。
        outer.addWidget(self._build_status_banner())
        outer.addWidget(self._separator())
        outer.addWidget(self._build_form())
        # ⚠️ 这个 1 是关键：**只有正文区**吃多余高度，其余各行保持自身高度
        outer.addWidget(self._build_content_area(), 1)
        outer.addWidget(self._build_full_source())
        outer.addWidget(self._build_status_detail())
        # ⚠️ 右侧吃满剩余宽度（左侧是固定宽）
        shell.addWidget(right, 1)
        self._right_panel = right

        # ★ **``date_view`` 是 ``date_edit`` 的别名，两者是同一个对象**（用户要求
        #   把日期输入口从两个减到一个）：旧的调用方 / 测试里那句
        #   ``w.date_view.setText(...)`` 因此照常可用，且**绝不会**出现「改了别名、
        #   真身没变」这种两份数据不一致的坑 —— 压根只有一份。
        #   ⚠️ 别把它改成 ``self.date_view = QtWidgets.QLineEdit()`` 之类的第二个框：
        #   那正是本轮删掉的东西。
        self.date_view = self.date_edit

    def _build_side_panel(self):
        """左侧面板：邮箱（可整块隐藏）+ 日期 + 文件列表。

        ★ **三段的分工**：

        ============  ====================================================
        邮箱          与「授权记录」逐字同构；**非管理员拿不到名单时整块隐藏**
        日期          一个输入框 + 「今天」「昨天」两个快捷按钮
        反馈文件      点一个就去读它的内容；**始终显示**（自己总有反馈可看）
        ============  ====================================================

        ⚠️ **邮箱那一段可以整块隐藏，日期与文件列表不能**：前者是「管理员才有」
        的附加能力，后两段是**本页的主要用途** —— 就算一条名单都拿不到，
        用户也总有**自己**的反馈要看。

        ★ **左栏负责「选什么」，右栏负责「看什么」**：日期与邮箱都在这里选，
        发起查询的按钮也在这里（「刷新文件」），右侧不再重复摆一套
        （原先右侧另有一个日期框和一个「查询」按钮，都已在 v1.10.6 删除）。

        Returns:
            QtWidgets.QWidget: 左侧面板。
        """
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(_Layout.LIST_WIDTH)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(_Layout.MARGIN, _Layout.MARGIN,
                                  _Layout.GAP, _Layout.MARGIN)
        layout.setSpacing(_Layout.GAP)

        # ---- 邮箱（可整块隐藏的一段）----
        self._email_section = self._build_email_section()
        layout.addWidget(self._email_section)

        # ---- 日期 ----
        date_title = QtWidgets.QLabel('日期')
        date_title.setEnabled(False)      # 置灰跟随主题，不写死颜色
        layout.addWidget(date_title)

        # ⚠️ **本控件只有一个日期输入口，就是这里**（用户要求）：右侧表单里原先
        #    另有一个同步的 ``date_view``，两个框查的是同一天、靠
        #    ``_on_date_changed`` 双向回写保持一致 —— 那是白白多出来的一份"必须
        #    维持一致"的状态。现已删除，日期只在此处填。
        #
        # ⚠️ **``date_view`` 这个名字保留为别名**（指向同一个框，见 ``_build_ui``）：
        #    测试与外部调用可能仍然写 ``w.date_view.setText(...)``，删掉名字会让它们
        #    炸成 AttributeError；别名与真身是**同一个对象**，不存在两份数据。
        self.date_edit = QtWidgets.QLineEdit()
        self.date_edit.setPlaceholderText('YYYY-MM-DD')
        self.date_edit.setToolTip(
            '看哪一天的反馈（北京时间的自然日）。\n'
            '反馈文件名里的时间戳就是北京时间，所以「按天」与文件名天然对齐。\n'
            '留空 = 服务端按北京时间取今天。')
        self.date_edit.returnPressed.connect(self.start_query)
        layout.addWidget(self.date_edit)

        quick = QtWidgets.QHBoxLayout()
        quick.setSpacing(_Layout.GAP)
        for text, days in (('今天', 0), ('昨天', 1)):
            btn = QtWidgets.QPushButton(text)
            btn.setFlat(True)       # 扁平 = 视觉上的次级按钮
            btn.setToolTip(f'把日期设为{text}，然后点「查询」。')
            btn.clicked.connect(
                lambda checked=False, d=days: self.set_date_days(d, query=True))
            quick.addWidget(btn)
        layout.addLayout(quick)

        # ---- 反馈文件 ----
        files_title = QtWidgets.QLabel('反馈文件')
        files_title.setEnabled(False)
        layout.addWidget(files_title)

        self.file_list = QtWidgets.QListWidget()
        self.file_list.setMinimumHeight(_Layout.LIST_MIN_HEIGHT)
        self.file_list.setToolTip(
            '点一个文件名，右侧就显示它的内容。\n'
            '文件名是北京时间的秒级时间戳。')
        # ⚠️ 用 ``itemClicked`` 而不是 ``currentItemChanged``：后者在**程序填充
        #    列表时也会发**，会导致「列完文件就自动读第一条」—— 那不是用户的意图
        #    （而且会平白多一次联网）。``itemClicked`` 只在用户真的点击时才发。
        self.file_list.itemClicked.connect(self._on_file_item_clicked)
        layout.addWidget(self.file_list, 1)

        self.refresh_files_button = QtWidgets.QPushButton('刷新文件')
        self.refresh_files_button.setFlat(True)
        self.refresh_files_button.setToolTip('重新向服务端要一次这一天的文件列表。')
        self.refresh_files_button.clicked.connect(self.start_query)
        layout.addWidget(self.refresh_files_button)

        # ★ **``query_button`` 是它的别名，两者是同一个按钮**（用户要求删掉右侧
        #   那个重复的「查询」）：两个按钮本来就连着**同一个槽** ``start_query``、
        #   也共用 ``_update_buttons`` 的忙碌禁用，删掉一个只是去掉同一件事的第二个
        #   入口。保留名字是为了让 ``w.query_button.click()`` 这类既有写法照常能用
        #   —— 且因为指向同一个对象，**绝不会**出现「点了别名、真身没反应」。
        #   ⚠️ 别把它改回 ``QtWidgets.QPushButton('查询')`` 之类的第二个按钮。
        self.query_button = self.refresh_files_button

        return panel

    def _build_email_section(self):
        """左侧的「邮箱」那一段（**本机邮箱置顶 + 服务端名单**）。

        ⚠️ 与 ``check_count_view._build_email_list`` 逐字同构：同样的**默认隐藏**、
        同样的 ``itemClicked``、同样的「空 -> 整块隐藏」。两处若改请一起改。

        Returns:
            QtWidgets.QWidget: 邮箱段（标题 + 列表 + 刷新按钮）。
        """
        section = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_Layout.GAP)

        title = QtWidgets.QLabel('用户')
        title.setEnabled(False)
        layout.addWidget(title)

        self.email_list = QtWidgets.QListWidget()
        self.email_list.setMinimumHeight(_Layout.LIST_MIN_HEIGHT)
        # ★ 条目是**两行**（姓名在上、邮箱在下）：不打开换行的话，Qt 会把换行
        #   当空白压成一行，长邮箱又会把列表撑宽 —— 两者都正是要避免的。
        self.email_list.setWordWrap(True)
        self.email_list.setToolTip(
            '点一个邮箱，右侧就去看它的反馈。\n'
            '名单由服务端维护，仅管理员可见。')
        self.email_list.itemClicked.connect(self._on_email_item_clicked)
        layout.addWidget(self.email_list, 1)

        self.refresh_list_button = QtWidgets.QPushButton('刷新名单')
        self.refresh_list_button.setFlat(True)
        self.refresh_list_button.setToolTip('重新向服务端要一次用户名单。')
        self.refresh_list_button.clicked.connect(
            lambda: self._start_user_list_query(force=True))
        layout.addWidget(self.refresh_list_button)

        section.setVisible(False)      # ⚠️ 默认隐藏，拿到名单 / 本机邮箱才显示
        return section

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

    def _build_status_banner(self):
        """顶部「一句话结论」提示条。

        Returns:
            QtWidgets.QLabel: 状态提示条。
        """
        self.status_label = QtWidgets.QLabel('准备就绪。')
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(10, 7, 10, 7)
        # ⚠️ 只设边框粗细与圆角，**色值一律交给主题**（见模块文档的版式约定）
        self.status_label.setStyleSheet(_Layout.BANNER_QSS)
        return self.status_label

    def _build_form(self):
        """右侧顶部的表单行：**只有一个只读的邮箱回显**。

        ★ **日期与「查询」都不在这里**（用户要求）：日期只在左侧面板填一次；
        右侧那个「查询」按钮也已删除 —— 它与左侧的「刷新文件」连的是**同一个槽**
        （``start_query``），连「忙碌时一起置灰」都是同一份代码，留着只是同一件事
        的第二个入口。两个名字现在指向**同一个按钮**（见 :meth:`_build_side_panel`
        末尾的别名），所以 ``w.query_button.click()`` 这类既有写法照常能用。

        ⚠️ **控件不做任何日期校验**：形态（``YYYY-MM-DD``，10 字符）与那几句
        文案全都归服务端拥有（它的最准）。本地复写一份必然漂，而漂了会表现为
        「本地放过去的请求被服务端拒」或反过来 —— 两种都查半天。
        所以日期那里只有一个输入框与两个快捷按钮，没有校验。

        ⚠️ **这一行的邮箱框是只读回显，不是第二个输入口**：邮箱以左侧那份为准
        （``get_query`` 读的是它）。放一个能编辑的框在这里，会出现「左边选了 A、
        右边改成 B」这种自相矛盾的状态。

        Returns:
            QtWidgets.QWidget: 配置好的表单。
        """
        box = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(_Layout.GAP)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                               QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.email_view = QtWidgets.QLineEdit()
        self.email_view.setReadOnly(True)      # ⚠️ 只是回显，见 docstring
        self.email_view.setPlaceholderText('（本机绑定的邮箱）')
        self.email_view.setToolTip(
            '当前查看的是谁的反馈。\n'
            '非管理员只能看自己绑定的那个邮箱，看别人的会得到 Not permitted.。')

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(_Layout.GAP)
        row.addWidget(self.email_view, 1)
        form.addRow('邮箱', row)
        return box

    def _build_content_area(self):
        """正文区（**本页唯一的弹性元素**）：文件名标题 + 只读文本框。

        ⚠️ 用 :class:`QtWidgets.QPlainTextEdit` 而不是 ``QTextEdit``：内容是
        JSON / 带时间戳的日志，**不需要富文本**，而 ``QPlainTextEdit`` 处理大段
        纯文本更快、也不会把内容里的 ``<...>`` 当成标记吞掉。

        ⚠️ **等宽字体**（``QFontDatabase.systemFont(FixedFont)``）：反馈正文是
        缩进过的 JSON，等宽才看得出结构。字体族取自系统、**不写死**，所以中文
        环境下也会回落到一个装得下中文的等宽字体。

        ⚠️ **只读**：服务端只有读接口，本控件不做编辑（也绝不把改动写回桶里）。

        Returns:
            QtWidgets.QWidget: 正文区容器。
        """
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_Layout.GAP)

        self.file_label = QtWidgets.QLabel('（还没有选中反馈）')
        # ⚠️ 让文件名**可以被选中复制**：用户常需要拿它去别处比对 / 回报。
        self.file_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
            QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard)
        layout.addWidget(self.file_label)

        # ---- 两个文本框（上下）+ 可拖动分隔 ----
        #
        # ★ **为什么是两个框**：反馈记录的形状是「一小段元数据 + 一大段正文」。
        #    合成一份缩进 JSON 时，正文会被挤到屏幕最下面，还得在引号里找 ``\n``；
        #    拆开之后上面看元数据、下面读正文，各看各的。
        #
        # ⚠️ **不拆时退回单区**（``_Parsers.format_content`` 说 ``split=False``）：
        #    那时**下框整个隐藏**，上框吃掉全部高度 —— 界面与改动前**逐像素一致**。
        #    （非 JSON 的原文、hex 摘要、空文件都走这条。）
        self.content_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical)
        # ⚠️ 子控件**不许被折叠到 0**：折没了用户就再也拖不回来（找不到那条
        #    分隔线）。所以下面给两个框都设了 ``setMinimumHeight``，并按顺序
        #    ``addWidget``（QSplitter 的顺序 = 上下顺序）。
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(_Layout.SPLITTER_HANDLE)

        # ⚠️ **完整的使用方法给上面这个框**（它始终可见）：下面那个框随时可能被
        #    整块隐藏（"不拆分"时 —— 清空之后正是这种状态），提示挂它上面会看不见。
        self.meta_view = self._make_text_view(
            _Layout.USAGE_HINT)
        self.meta_label = QtWidgets.QLabel('元数据')
        self.meta_label.setEnabled(False)      # 置灰跟随主题，不写死颜色

        self.text_view = self._make_text_view(
            _Layout.USAGE_HINT_TEXT)
        self.text_label = QtWidgets.QLabel('text')
        self.text_label.setEnabled(False)

        meta_box = self._wrap_labeled(self.meta_label, self.meta_view)
        text_box = self._wrap_labeled(self.text_label, self.text_view)
        self.content_splitter.addWidget(meta_box)
        self.content_splitter.addWidget(text_box)
        # ⚠️ 顺手把「谁是谁」记下来：``_show_content`` 要隐藏 / 显示它们。
        self._meta_box = meta_box
        self._text_box = text_box
        # 初始比例：元数据通常只有几行，正文才是主角
        self.content_splitter.setSizes(
            [_Layout.META_MIN_HEIGHT, _Layout.TEXT_HINT_HEIGHT])

        layout.addWidget(self.content_splitter, 1)
        return box

    def _make_text_view(self, placeholder):
        """造一个只读的等宽文本框（元数据 / 正文两块共用）.

        ⚠️ 用 :class:`QtWidgets.QPlainTextEdit` 而不是 ``QTextEdit``：内容是
        JSON / 带时间戳的日志，**不需要富文本**，而 ``QPlainTextEdit`` 处理大段
        纯文本更快、也不会把内容里的 ``<...>`` 当成标记吞掉。

        ⚠️ **等宽字体**（``QFontDatabase.systemFont(FixedFont)``）：元数据是缩进
        过的 JSON、正文是带时间戳的日志，等宽才看得出结构。字体族取自系统、
        **不写死**，所以中文环境下也会回落到一个装得下中文的等宽字体。

        ⚠️ **只读**：服务端只有读接口，本控件不做编辑（也绝不把改动写回桶里）。

        Args:
            placeholder: 没有内容时显示的提示文本。

        Returns:
            QtWidgets.QPlainTextEdit: 配置好的文本框。
        """
        view = QtWidgets.QPlainTextEdit()
        view.setReadOnly(True)
        view.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        view.setMinimumHeight(_Layout.META_MIN_HEIGHT)
        view.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        try:
            view.setFont(QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.SystemFont.FixedFont))
        except Exception as err:
            # 拿不到系统等宽字体不是错误：用默认字体照样能看，只是对不齐
            print(f'Error (when set fixed font): {err}')
        view.setPlaceholderText(placeholder)
        return view

    @staticmethod
    def _wrap_labeled(label, view):
        """把一个标签与一个文本框装成一列（标签在上、文本框在下）。

        Args:
            label: 小标题（已 ``setEnabled(False)`` 表达「次要」）。
            view: 文本框。

        Returns:
            QtWidgets.QWidget: 容器。
        """
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(label)
        layout.addWidget(view, 1)
        return box

    def _build_status_detail(self):
        """「服务器原始答复」可折叠区（**默认收起**，沿用 ``QGroupBox``）。

        ⚠️ **默认收起**：这里显示的是服务端原话 + 往返耗时，属于「想深究时才看」
        的排错信息，平时占着一块地方反而挤压正文区。结论已经由上方横幅用一句话
        给出来了（失败时 ``Not permitted.`` / ``The feedback file is not
        available.`` 这类原话**照样**会出现在横幅里，不会被藏起来）。

        ⚠️ ``QGroupBox`` 的「可勾选 + 扁平」用法正好就是「一个可折叠的小节」，
        勾选框本身就是展开 / 收起的开关，不必自造按钮。

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
        self.status_view.setFixedHeight(_Layout.STATUS_VIEW_HEIGHT)
        self.status_view.setPlaceholderText(
            '查询后这里显示服务器的原话，以及本次往返耗时。')
        layout.addWidget(self.status_view)

        # ⚠️ **连接必须放在 ``status_view`` 建好之后**：``setVisible`` 那条槽要用
        #    到它。若在它被创建之前连上，槽函数一跑就抛 ``AttributeError`` ——
        #    而 PyQt 会把槽里的异常**静默吞掉**，表现为「标题能勾，但内容区纹丝
        #    不动」（``check_count_view.py`` 里真踩过）。
        box.toggled.connect(self.status_view.setVisible)
        # ⚠️ 必须**显式**设为不可见：``setChecked(False)`` 是在连接之前调的，
        #    那个信号没有发出，光靠它藏不住这个控件。
        self.status_view.setVisible(False)
        return box

    def _build_full_source(self):
        """「完整原文」可折叠区（**默认收起**）。

        ★ **它是拆分显示的配套**：正文区把 ``text`` 拿出来单独放了，这里保留
        「桶里那份文件原样是什么」—— 拆分只是**换个摆法**，不是过滤，想对照
        原始形态（含字段顺序、含 ``text`` 在整份 JSON 里长什么样）时展开看。

        ⚠️ **显示的是解析后的整份 JSON**（缩进）。⚠️ 非 JSON / hex 摘要 / 空文件
        时它**没有额外信息**（正文区已经是全文了），那时整块**隐藏** —— 见
        :meth:`_show_content`。摆一个空框在那儿只会让人以为内容丢了。

        Returns:
            QtWidgets.QGroupBox: 可勾选的容器（勾选 = 展开，扁平样式）。
        """
        box = QtWidgets.QGroupBox('完整原文（含 text）')
        box.setCheckable(True)
        box.setChecked(False)   # ⚠️ 默认收起：多数时候元数据 + 正文已经够了
        box.setFlat(True)
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)

        self.full_view = QtWidgets.QPlainTextEdit()
        self.full_view.setReadOnly(True)
        self.full_view.setFixedHeight(_Layout.FULL_VIEW_HEIGHT)
        self.full_view.setLineWrapMode(
            QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        try:
            self.full_view.setFont(QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.SystemFont.FixedFont))
        except Exception as err:
            print(f'Error (when set fixed font): {err}')
        self.full_view.setPlaceholderText(
            '拆分显示时，这里保留整份文件的原始形态（含 text）。')
        layout.addWidget(self.full_view)

        # ⚠️ 同 status_view：连接必须在目标控件建好之后，且要显式藏一次
        box.toggled.connect(self.full_view.setVisible)
        self.full_view.setVisible(False)
        # ⚠️ 记下容器本身：``_show_content`` 要整块隐藏 / 显示它（不只是里面
        #    那个文本框）—— 只藏文本框会留下一个**光秃秃的标题**。
        self._full_box = box
        return box

    # ------------------------------------------------------------------
    # 左侧：邮箱列表
    # ------------------------------------------------------------------

    def _refresh_email_list(self):
        """重建左侧邮箱列表 = 服务端名单 ∪ {本机绑定邮箱}（本机邮箱置顶、去重）。

        ⚠️ **本机绑定邮箱排最前**：非管理员拿不到名单时，列表里至少还有它自己那
        一个；管理员则一眼看到「我自己」在最上面。

        ⚠️⚠️ **列表为空时把整个邮箱段隐藏**（不是只藏列表）：这样非管理员看到的
        界面与「没有这个功能」时逐像素一致，不会凭空少掉一块。
        """
        emails = _merge_emails(
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
                # ⚠️ 面板只有 _Layout.LIST_WIDTH 宽，长邮箱一行放不下 —— Qt 的默认
                #   委托只在空格处折行，邮箱没有空格，结果是右边被硬裁掉。
                from zmlx.ui.utils.lic_utils import wrap_text_to_width
                viewport = self.email_list.viewport()
                width = max(60, (viewport.width() if viewport is not None
                                 else _Layout.LIST_WIDTH) - 12)
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

        self._email_section.setVisible(bool(emails))

    def _on_email_item_clicked(self, item):
        """用户点了左侧列表里的某个邮箱：换目标并重新列举那一天的反馈。

        Args:
            item: 被点击的列表项。
        """
        if item is None:
            return
        # ⚠️ 条目文字可能是「姓名\n邮箱」，邮箱以 UserRole 为准（见 _refresh_email_list）
        email = item.data(QtCore.Qt.ItemDataRole.UserRole) or item.text()
        self.query_email(str(email))

    def _start_user_list_query(self, force=False):
        """在后台拉一次服务端名单（**每次运行最多一次**，除非强制刷新）。

        ⚠️⚠️ **必须在后台线程**：``user_list`` 不做缓存、每次真的发出去，单次最长
        阻塞 30 秒。在 UI 线程里调就等于「打开本页卡 30 秒」。

        ⚠️ 拉取期间**界面照常可用**（不置忙、不禁用查询按钮）：名单只是左侧列表
        的装饰，不该拦住用户看自己的反馈。

        Args:
            force: 忽略「已经拉过」的记录，强制再拉一次（「刷新名单」按钮用）。
        """
        if self._user_list_worker is not None:
            return                      # 已经在拉了，不叠加
        if self._server_emails is not None and not force:
            return                      # 本次运行已经拿到过（含「确认拿不到」）
        # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见那里的说明
        #    （关标签时控件会被销毁，parent 设成控件会连着线程一起删 = 进程崩溃）。
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
        **正常业务答复**，不是错误 —— 不弹窗、不改横幅。列表退回到「只有本机
        绑定邮箱」（再没有就整块隐藏）。

        ⚠️ **名单不落盘、也不写进日志内容**：那是**别人的**邮箱，服务端刻意连
        日志都不写。这里只记条数。

        ⚠️ **绝不在这里主动发起查询**：名单是异步回来的，用户可能早就不在看这个
        页面了。查询只由**用户点击列表项 / 按钮**触发。

        Args:
            reply: ``user_list`` 的服务端答复正文。
        """
        from zmlx.ui.utils.lic_utils import parse_user_list, parse_user_list_detail

        entries = parse_user_list_detail(reply)
        if entries is None:
            # ★ 不是新动作的答复：老服务端（< 3.35）会把未知 action 当查询回一句
            #   ``Yes``；这里再试旧格式 ``Users:``，两者都判不出就退回「只用本机邮箱」。
            emails = parse_user_list(reply)
            if emails is None:
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
        """把邮箱换成指定值并重新列举（**给左侧列表 / 外部调用**）。

        ⚠️⚠️ **``force=True``（默认）时会放弃正在飞的那个请求，立刻换成本次点击
        的目标**：用户在列表里连点几个邮箱是很自然的动作，如果每次都因为「上一个
        还没回来」而被忽略，他会以为界面卡了 —— 而**他要看的明明是最后点的那个**。

        Args:
            email: 要看的邮箱；空串直接返回（不查询）。
            force: ``True`` = 换目标（默认）；``False`` = 有请求在飞就不发起。

        Returns:
            bool: 真的发起了查询返回 True。
        """
        email = str(email or '').strip()
        if not email:
            return False
        if self._busy:
            if not force:
                self._log('上一个请求还没结束，这次点击被忽略')
                return False
            self._log('切换到新的查询目标，放弃上一个未完成的结果')
            self._abandon_current_query()
        self._bound_email = email
        self.email_view.setText(email)
        self.start_query()
        return True

    def _on_file_item_clicked(self, item):
        """用户点了左侧的某个文件名：去读它的内容。

        ⚠️ 文件名**原样**转交（``item.text()``），绝不做任何加工 —— 那正是服务端
        形态闸认的那个字符串。

        Args:
            item: 被点击的列表项。
        """
        if item is None:
            return
        self.read_file(item.text())

    def _refresh_file_list(self, files):
        """重建左侧反馈文件列表。

        ⚠️ 填充期间 ``blockSignals(True)``：虽然用的是 ``itemClicked``（填充不会
        触发它），但多一道保险 —— 万一将来有人把信号换成 ``currentItemChanged``，
        这道保险能挡住「列完文件就自动读第一条」。

        ⚠️ **列表项显示的是原文件名**（不显示美化后的时间）：用户要拿这个名字去
        别处比对、要复制走，显示的必须与服务端认的那个字符串**逐字一致**。
        美化后的时间放在**悬停提示**里。

        Args:
            files: 裸文件名列表。
        """
        self._files = list(files or [])
        self.file_list.blockSignals(True)
        try:
            self.file_list.clear()
            for name in self._files:
                item = QtWidgets.QListWidgetItem(name)
                stamp = _Parsers.format_stamp(name)
                item.setToolTip(f'{name}\n{stamp}' if stamp else name)
                self.file_list.addItem(item)
        finally:
            self.file_list.blockSignals(False)

    # ------------------------------------------------------------------
    # 取值与状态
    # ------------------------------------------------------------------

    def get_query(self):
        """返回当前要查的 ``(邮箱, 日期)``（都已去掉首尾空白）。

        ⚠️ **只做去空白，不做形态判断**：这里取到的值原样交给服务端（空串表示
        「不发该字段」），任何本地校验都会成为一份会漂的副本。

        ★ 日期读的是``date_edit``（本控件**唯一**的日期输入口；``date_view``
        只是它的别名，指向同一个对象）。

        Returns:
            tuple: ``(email, date)``。
        """
        return (self.email_view.text().strip(), self.date_edit.text().strip())

    def get_files(self):
        """返回当前左侧列出的文件名（副本）。

        Returns:
            list: 裸文件名列表。
        """
        return list(self._files)

    @staticmethod
    def _today_str():
        """返回**本机今天**的 ``YYYY-MM-DD``（预填用）。

        ⚠️ 这里用的是**本机日期**，只是「用户大概想看哪一天」的初值。真正的
        「今天」由**服务端**按北京时间取（``check.day_stamp()``）—— 两者偶尔差
        一天（时区 / 跨零点）时，**以服务端的结论为准**（见
        :meth:`_on_list_reply`：横幅里的日期段来自服务端答复）。

        Returns:
            str: 例如 ``'2026-10-08'``。
        """
        return datetime.date.today().strftime(_Marks.DATE_FORMAT)

    def set_date(self, date):
        """把日期输入框设为指定值（**不联网**）。

        Args:
            date: ``YYYY-MM-DD``；空串表示留空（= 服务端默认的今天）。
        """
        self.date_edit.setText(str(date or '').strip())

    def set_date_days(self, days, *, query=False):
        """把日期设为「``days`` 天前」（本地计算，不联网）。

        Args:
            days: 往前推的天数；``0`` 就是今天。
            query: 是否顺手发起一次查询。``False``（默认）只改输入框，让用户可以
                先把邮箱改对再点「查询」。
        """
        day = datetime.date.today() - datetime.timedelta(days=max(int(days), 0))
        self.set_date(day.strftime(_Marks.DATE_FORMAT))
        if query:
            self.start_query()

    def _prefill_email(self):
        """尝试从本机已绑定的授权里取邮箱（**在后台线程里调用**）。

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
        """往标准输出记一行（排错用）。

        ⚠️ **必须兜住异常**：Windows 控制台默认是 GBK，装不下一些符号
        （``check_count_view.py`` 里真踩过：UnicodeEncodeError 直接把控件构造打断）。

        ⚠️ **绝不把反馈正文写进日志**：那是**别人的**私密文本。这里只记文件名、
        邮箱、条数、状态码这类元信息。
        """
        try:
            print(message)
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
        """按「是否有请求在飞」刷新按钮可用性（防连点排起一队请求）。

        ⚠️ 日期框也跟着变只读：查询期间改它只会让「屏幕上显示的」与
        「正在查的」对不上。

        ★ ``query_button`` 与 ``refresh_files_button`` 是**同一个按钮**
        （见 :meth:`_build_side_panel`），所以这里只处理一个就够 —— 写成两个
        也无害，但会让人误以为界面上有两个查询入口。
        """
        idle = not self._busy
        self.refresh_files_button.setEnabled(idle)
        self.date_edit.setReadOnly(not idle)

    def _abandon_current_query(self):
        """放弃当前正在飞的请求（旧结果回来时会被丢掉）。

        ⚠️ **不杀线程**：``QThread`` 不能安全地强制终止（``terminate()`` 会让
        资源泄漏、甚至崩）。正确做法是**只放开闸门、并把旧结果标记为作废** ——
        线程自己跑完、结果回来时按代次丢掉即可。
        """
        self._query_generation += 1     # 旧结果靠这个代号失效
        self._busy = False
        self._update_buttons()

    # ------------------------------------------------------------------
    # 查询编排
    # ------------------------------------------------------------------

    def showEvent(self, event):
        """控件首次显示时，自动查一次（并在后台取本机绑定的邮箱 / 名单）。

        ⚠️ 放在 :meth:`showEvent` 而不是 ``__init__``：本控件由 TabWidget
        **创建后立刻挂到标签页**，不一定马上显示；而且构造期间起网络线程会让
        「打开窗口」这件事变得不可预期。用 :attr:`_auto_checked` 保证**只跑
        一次** —— 切换标签页会反复触发本事件，不能每次都发一次请求。
        """
        super(FeedbacksView, self).showEvent(event)
        if self._auto_checked:
            return
        self._auto_checked = True
        # 延后一拍：showEvent 期间控件还没画出来，此时起线程 / 改按钮状态
        # 在某些平台会看到界面闪一下
        QtCore.QTimer.singleShot(0, self._auto_start)

    def _auto_start(self):
        """首次显示时的自动动作：**在后台**补邮箱 + 拉名单，然后再查一次。

        ⚠️ **三个请求都在后台线程**（``_PrefillWorker`` 取本机绑定邮箱、
        ``_UserListWorker`` 取服务端名单），主线程**从不等待**它们 —— 这正是
        「打开本页立即显示」的实现方式。

        ⚠️ 三者**分开成不同线程**：取绑定邮箱失败不该连带把名单也丢掉，反之亦然。

        ⚠️ **本方法不等名单**：先把主流程（补邮箱 → 查询）跑起来，名单回来了
        再单独刷新左侧列表。所以「立即显示」这条在名单很慢（最长 30 秒）时依然成立。
        """
        # 名单那一路：起了就不管它，结果经信号回来自己处理
        self._start_user_list_query()

        if not self.email_view.text().strip():
            # ⚠️ 取邮箱本身要联网（最长 30 秒），**不能在 UI 线程里做**
            self._show_status('正在读取本机已绑定的邮箱...', ok=None)
            # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见那里的
            #    说明。⚠️ 第一个参数是**取值用的 owner 引用**，不是 Qt parent。
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
        """邮箱取回来了（主线程调用）：填进界面、刷新列表、并开始查询。

        ⚠️ **只在为空时填**：用户可能已经在敲字了（查询要联网，回来得比人慢），
        覆盖掉他刚输入的内容是最讨厌的一类交互。填不填得上，都照样发起首次查询
        （查不到邮箱时服务端会回一句可读的失败文案）。

        ⚠️ 把它同时记为 :attr:`_bound_email` 并刷新左侧列表：**非管理员拿不到
        服务端名单时，列表里就只有它自己那一个**。绑定邮箱**不写进任何历史**。
        """
        email = str(email or '').strip()
        if email:
            self._bound_email = email
        if email and not self.email_view.text().strip():
            self.email_view.setText(email)
            self._log(f'预填邮箱：{email}')
        self._refresh_email_list()
        self.start_query()

    def start_query(self):
        """列举当前日期 / 邮箱的反馈文件名（**不等结果**，请求在后台线程里跑）。

        本方法只做三件事：禁用按钮、起线程、更新横幅。

        ⚠️ **本地不拦任何形态问题**：日期写歪、越权，全都由服务端拥有答复文案，
        本地复写只会漂。日期留空**是合法的**（= 服务端的今天），所以这里连
        「日期为空」都不拦。
        """
        if self._busy:
            # 理论上按钮已禁用，点不到；这里是第二道保险（例如回车键触发）
            self._log('上一个请求还没结束，请稍候')
            return

        email, date = self.get_query()
        self._last_query = (email, date)
        self._log(f'列举反馈：email={email or "(默认)"} date={date or "(默认今天)"}')
        self._show_status('正在查询...', ok=None)

        # ⚠️ 把「代号」一并绑进信号处理：这次查询属于哪一代，回来时就按哪一代判。
        #    这样即使用户中途改了日期 / 邮箱（代号 +1），旧结果回来也会被丢掉。
        generation = self._query_generation

        # ⚠️ parent **留空**（不是 ``parent=self``）：本控件会随标签页被
        #    deleteLater 销毁，parent 设成自己的线程会被连带析构 —— 请求还在飞
        #    时就是进程崩溃（"QThread: Destroyed while thread is still running"）。
        #    改由模块级 _RUNNING_WORKERS 持有强引用。
        worker = _ListWorker(date, email, parent=None)
        worker.sig_done.connect(
            lambda reply, elapsed, g=generation:
                self._on_list_reply(reply, elapsed, generation=g))
        worker.finished.connect(lambda: self._on_list_worker_finished(worker))
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._list_worker = worker
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()

    def _on_list_worker_finished(self, worker):
        """列举线程结束（主线程调用）：放开按钮、释放引用。

        ⚠️ 只释放**当前**那个 worker 的引用；若它已经被新的查询顶替掉
        （``self._list_worker`` 已经是别人），就什么都不做 —— 否则会把新查询的
        引用清掉，让那个线程失去引用而被 GC。
        """
        if _is_deleted(self):
            return          # 控件已随标签页关闭被销毁：没什么可释放的
        if self._list_worker is worker:
            self._list_worker = None
            self._busy = False
            self._update_buttons()

    def _on_list_reply(self, reply, elapsed_text, *, generation=None):
        """列举的答复回来了（**在主线程里跑**）：填充左侧文件列表。

        ⚠️ 判定用 :meth:`_Parsers.list_ok`（**只看开头是不是 ``Feedbacks:``**，
        **复数**），不是 ``reply == ...`` 之类：成功正文后面还跟着
        ``| Email: … | Date: … | Files: …`` 若干段，严格比较是一条会随服务端演进
        而失效的隐含假设。

        ⚠️ 失败时**原样显示服务端原话**（``Not permitted.`` / ``dll not found``
        / 连不上的描述），绝不替换成含糊的「失败」，也**绝不**替服务端编一句
        「这个邮箱不存在」—— 那句话是服务端刻意不说的。

        ⚠️⚠️ **代号对不上的答复会被丢弃**：用户连点几个日期 / 邮箱时，
        :meth:`query_email` 会把旧的那次标记作废。旧线程仍会跑完并送答复回来，
        这里按代号丢掉它 —— 否则会出现「点了 A 又点 B，最后显示的却是 A」这种错乱。

        ⚠️ **``Truncated: true`` 在本动作里的含义是「超过一页」**（1000 个对象），
        与读取动作里那个「内容被截断」**不是一回事**，所以文案要分开写。

        Args:
            reply: ``list_feedbacks`` 的答复正文。
            elapsed_text: 已格式化好的往返耗时（可能为空串）。
            generation: 这次查询属于哪一代（``None`` = 不检查，直接显示）。
        """
        # ⚠️ 控件可能已随标签页关闭被销毁，而本槽是 lambda 连的（Qt 不会自动
        #    断连）—— 迟到的答复必须直接丢掉，否则碰子控件会抛
        #    "wrapped C/C++ object ... has been deleted"。
        if _is_deleted(self):
            return
        if generation is not None and generation != self._query_generation:
            self._log('丢弃一个已作废的列举结果（用户已经改查别的日期 / 邮箱）')
            return

        text = str(reply if reply is not None else '').strip()
        self._log(f'列举响应：{text or "(空响应)"}'
                  f'{f" [{elapsed_text}]" if elapsed_text else ""}')

        # 原始答复区始终显示原话 + 耗时（失败时也要显示 —— 那正是最该看的时候）
        self._write_status_detail(text, elapsed_text)

        if not _Parsers.list_ok(text):
            self._refresh_file_list([])
            self._clear_content()
            if not text:
                self._show_status('没拿到任何答复（可能是网络中断）。', ok=False)
            else:
                self._show_status(f'查询失败：{text}', ok=False)
            return

        files = _Parsers.parse_files(text)
        self._refresh_file_list(files)

        # ⚠️ 换了一批文件，右侧那条内容就不再对应得上了 —— 必须清掉，
        #    否则会出现「左边列的是今天，右边显示的是昨天那条」这种错乱。
        self._clear_content()

        date_text = _find_tag(text, 'Date:')
        email_text = _find_tag(text, 'Email:')
        span = f'{date_text}，' if date_text else ''
        who = f'{email_text} 的' if email_text else ''

        if not files:
            # ⚠️ 0 条**不是错误**：那天就是没有反馈。服务端刻意不产出 Files: 段。
            self._show_status(f'查询成功。{span}{who}这一天没有反馈。', ok=None)
        elif _Parsers.is_truncated(text):
            # ⚠️ 本动作里 Truncated 的含义是「超过一页」，列表**不完整**
            self._show_status(
                f'找到 {len(files)} 条反馈（{span}列表被截断，可能还有更多）。',
                ok=None)
        else:
            self._show_status(
                f'找到 {len(files)} 条反馈（{span}点左侧文件名查看内容）。', ok=True)

        dropped = _find_tag(text, _Marks.DROPPED_TAG)
        if dropped:
            # ⚠️ 丢掉但不静默：那是「桶里有不符合命名的对象」，值得让人知道
            self._log(f'列举时有 {dropped} 个对象不符合命名，已跳过')

    def read_file(self, file_name, *, force=True):
        """读取一条反馈的内容（**给左侧列表 / 外部调用**）。

        ⚠️⚠️ **``force=True``（默认）时会放弃正在飞的那个请求**，理由与
        :meth:`query_email` 逐字相同：用户在列表里连点几个文件名是自然的动作，
        他要看的明明是最后点的那个。

        Args:
            file_name: **裸文件名**（如 ``'20260928223007.json'``）；空串直接返回。
            force: ``True`` = 换目标（默认）；``False`` = 有请求在飞就不发起。

        Returns:
            bool: 真的发起了读取返回 True。
        """
        file_name = str(file_name or '').strip()
        if not file_name:
            return False
        if self._busy:
            if not force:
                self._log('上一个请求还没结束，这次点击被忽略')
                return False
            self._log('切换到新的读取目标，放弃上一个未完成的结果')
            self._abandon_current_query()
        self._read_file_name = file_name
        self._show_status(f'正在读取 {file_name} ...', ok=None)

        email, _ = self.get_query()
        generation = self._query_generation
        worker = _ReadWorker(file_name, email, parent=None)
        worker.sig_done.connect(
            lambda reply, elapsed, g=generation:
                self._on_read_reply(reply, elapsed, generation=g))
        worker.finished.connect(lambda: self._on_read_worker_finished(worker))
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)
        self._read_worker = worker
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()
        return True

    def _on_read_worker_finished(self, worker):
        """读取线程结束（主线程调用）：放开按钮、释放引用。"""
        if _is_deleted(self):
            return
        if self._read_worker is worker:
            self._read_worker = None
            self._busy = False
            self._update_buttons()

    def _show_content(self, file_name, parts, full_source=''):
        """把内容写进正文区（**按 ``parts['split']`` 决定单区还是两个区**）。

        ★ **两种摆法**（见 :meth:`_Parsers.format_content`）：

        - ``split=True``：上框放元数据（``text`` 以外的字段）、下框放 ``text``，
          两块都能看、中间可拖；「完整原文」区展开可看整份 JSON；
        - ``split=False``：**退回单区** —— 下框与「完整原文」区一起隐藏，上框吃掉
          全部高度。这时界面与改动前**逐像素一致**（非 JSON 原文 / hex 摘要 /
          空文件都走这条）。

        ⚠️ **每次都要显式设两块与「完整原文」区的可见性**：它们的状态是上一次
        显示留下的，不清就会串味（上一条是拆开的、这一条不是，下框还挂着旧内容）。

        Args:
            file_name: 裸文件名（显示在标题行）。
            parts: :meth:`_Parsers.format_content` 的返回值（四个键的字典）。
            full_source: 「完整原文」区要显示的文本；空串表示**没有额外信息**
                （非 JSON / hex / 空文件），那块**整块隐藏**。
        """
        stamp = _Parsers.format_stamp(file_name)
        title = f'文件名：{file_name}'
        if stamp:
            title += f'（{stamp}）'
        note = str(parts.get('note') or '')
        if note:
            title += f'  —  {note}'
        self.file_label.setText(title)

        split = bool(parts.get('split'))
        self.meta_view.setPlainText(str(parts.get('meta') or ''))
        self.text_view.setPlainText(str(parts.get('text') or ''))

        # ⚠️ 顺序要紧：先设**子块**的可见性，再设分隔条里那一块 —— 否则会闪一下
        self._text_box.setVisible(split)
        self.meta_label.setText('元数据（text 以外的字段）' if split else '内容')
        if split:
            # 每次拆开都把比例复位：上一次用户可能把某一块拖得很小
            self.content_splitter.setSizes(
                [_Layout.META_MIN_HEIGHT, _Layout.TEXT_HINT_HEIGHT])

        has_full = bool(split and full_source)
        self._full_box.setVisible(has_full)
        self.full_view.setPlainText(str(full_source or ''))
        if not has_full:
            # ⚠️ 藏起来的时候顺手把勾去掉：否则下次它带着「已勾选」的状态出现，
            #    而内容区却是收起的 —— 那种自相矛盾最难查。
            self._full_box.setChecked(False)

    def _clear_content(self):
        """把正文区清空（换了一批文件、或查询失败时）。

        ⚠️ **两个框都要清**（还有「完整原文」区）：只清一个的话，下一条内容到来
        之前会看到上一份的残留 —— 而文件名标题已经换了，那是最容易误读的一刻。

        ★ 清成空串之后，两个框各自的**占位文字**会自动重新出现（Qt 的行为），
        也就是 :data:`_Layout.USAGE_HINT`（上面那个框，完整使用方法 —— 它始终
        可见）与 :data:`_Layout.USAGE_HINT_TEXT`（下面那个框，只说自己）——
        空着的时候正好该教用户下一步怎么做。⚠️ 所以**不要**在这里改成
        ``setPlainText(' ')`` 之类的"假装清干净"：那样占位文字就永远不显示了。
        """
        self.file_label.setText('（还没有选中反馈）')
        self.meta_view.setPlainText('')
        self.text_view.setPlainText('')
        self.full_view.setPlainText('')
        self._text_box.setVisible(False)
        self._full_box.setVisible(False)
        self._full_box.setChecked(False)
        self.meta_label.setText('内容')

    def _on_read_reply(self, reply, elapsed_text, *, generation=None):
        """内容的答复回来了（**在主线程里跑**）：解码并显示。

        ★ **处理顺序固定**（每一环都有它的理由）::

            ① 判成功（:meth:`_Parsers.read_ok`，**单数**记号）
            ② 看 ``Truncated:`` 标记 —— **必须先于** ③
            ③ 取字节（:meth:`_Parsers.decode` -> ``get_feedback_bytes()``，解码在那边）
            ④ 格式化（:meth:`_Parsers.format_content`：JSON -> 缩进 / 否则原文 / 二进制 -> hex）

        ⚠️⚠️ **② 必须排在 ③ 之前**：被截断的内容**必然**缺右括号，直接
        ``json.loads`` 会抛异常。而那是**数据事实**（服务端按 40 KiB 截的），
        不是程序错误 —— 所以要先把这个事实记下来、再照常显示已拿到的部分。

        ⚠️ **0 字节文件是成功**（``decode`` 回 ``b''``），与「文件不存在」
        （``The feedback file is not available.``，不是成功正文）是两件事，
        这里的分支把它们分得很开。

        ⚠️ **``Truncated: true`` 在本动作里的含义是「内容被截断」** —— 与列举
        动作里那个「超过一页」不同，所以文案也不同。

        Args:
            reply: ``get_feedback`` 的答复正文。
            elapsed_text: 已格式化好的往返耗时（可能为空串）。
            generation: 这次查询属于哪一代（``None`` = 不检查，直接显示）。
        """
        if _is_deleted(self):
            return
        if generation is not None and generation != self._query_generation:
            self._log('丢弃一个已作废的读取结果（用户已经点了别的文件）')
            return

        text = str(reply if reply is not None else '').strip()
        self._log(f'读取响应：{text[:120] or "(空响应)"}'
                  f'{f" [{elapsed_text}]" if elapsed_text else ""}')

        self._write_status_detail(text, elapsed_text)

        file_name = _Parsers.find_display_name(text) or \
            getattr(self, '_read_file_name', '')

        if not _Parsers.read_ok(text):
            self._clear_content()
            if not text:
                self._show_status('没拿到任何答复（可能是网络中断）。', ok=False)
            else:
                # ⚠️ 原样显示服务端原话：``The feedback file is not available.``
                #    是**正常业务分支**（那个槽位没有这个文件），``Not permitted.``
                #    是越权 —— 两者都**不要**替服务端改写成别的话。
                self._show_status(f'读取失败：{text}', ok=False)
            return

        truncated = _Parsers.is_truncated(text)
        raw = _Parsers.decode(text)
        parts = _Parsers.format_content(raw)

        if truncated:
            # ⚠️ 截断标记**压过**其他说明：它改变的是「这份内容能不能当完整数据用」
            note = '内容超过服务端的读取上限，**已被截断**，不是完整内容' \
                   '（很可能不是合法 JSON）。'
            parts['note'] = note
        else:
            note = str(parts.get('note') or '')

        # ★ 「完整原文」区只在**真的拆开了**的时候才有额外信息：那时正文区是
        #    「元数据 + text」两块，而这里放整份 JSON 供对照。
        #    ⚠️ 不拆的时候它就是正文区那一份的副本 —— 摆出来只会让人以为有两份
        #    不同的东西，所以传空串让它整块隐藏。
        full_source = ''
        if parts.get('split') and raw is not None:
            full_source = _Parsers.full_json(raw)

        self._show_content(file_name, parts, full_source)

        if raw == b'':
            self._show_status(f'读取成功，但 {file_name} 是**空文件**（0 字节）。',
                              ok=None)
        elif truncated:
            self._show_status(f'读取成功，但内容**已被截断**（{file_name}）。',
                              ok=False)
        elif note:
            self._show_status(f'读取成功（{file_name}）：{note}', ok=None)
        elif parts.get('split'):
            size = len(raw) if raw is not None else 0
            self._show_status(
                f'读取成功：{file_name}（{size} 字节，'
                f'已把 text 单独列出）。', ok=True)
        else:
            size = len(raw) if raw is not None else 0
            self._show_status(f'读取成功：{file_name}（{size} 字节）。', ok=True)

    def _write_status_detail(self, text, elapsed_text):
        """把「服务器原始答复 + 往返耗时」写进可折叠区。

        ⚠️ **原话照录，不做任何裁剪**（除了下面那条长度保险）：这是排错时唯一
        能拿去比对的东西。⚠️ 但 ``get_feedback`` 的答复可以长达几十 KB 的 base64
        —— 全塞进去会把那一小块文本区撑得极慢，所以超长时**只留前一段并说明**。

        Args:
            text: 服务端答复正文。
            elapsed_text: 已格式化的往返耗时（可能为空串）。
        """
        shown = text or '(空响应)'
        if len(shown) > 4000:
            shown = shown[:4000] + f'\n…（原文共 {len(text)} 字符，这里截断显示）'
        lines = [shown]
        if elapsed_text:
            lines.append(elapsed_text)
        self.status_view.setPlainText('\n'.join(lines))

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

    def copy_content(self):
        """把正文区的内容复制到剪切板（**拆开时两块一起给**）。

        ⚠️ **拆开时拼成「元数据 + 正文」**：只复制上面那块会丢掉正文（那是用户
        真正要的内容），只复制下面那块又丢掉了上下文。两份之间空一行，粘到哪里
        都还分得清。
        """
        try:
            meta = self.meta_view.toPlainText()
            body = self.text_view.toPlainText()
            if self._text_box.isVisible() and body:
                text = f'{meta}\n\n{body}' if meta else body
            else:
                text = meta
            QtWidgets.QApplication.clipboard().setText(text)
            self._show_status('内容已复制到剪切板。', ok=None)
        except Exception as err:
            self._log(f'Error (when copy content): {err}')

    def copy_full_source(self):
        """把「完整原文」区里的整份 JSON 复制到剪切板。"""
        try:
            QtWidgets.QApplication.clipboard().setText(
                self.full_view.toPlainText())
            self._show_status('完整原文已复制到剪切板。', ok=None)
        except Exception as err:
            self._log(f'Error (when copy full source): {err}')

    def get_context_menu(self):
        """构造正文区的右键菜单。

        Returns:
            QtWidgets.QMenu: 菜单。
        """
        from zmlx.ui.alg import create_action

        menu = QtWidgets.QMenu(self)
        split = self._text_box.isVisible()
        menu.addAction(create_action(
            self,
            '复制内容（元数据 + 正文）' if split else '复制内容',
            icon='export', slot=self.copy_content))
        if self._full_box.isVisible():
            menu.addAction(create_action(
                self, '复制完整原文（整份 JSON）', icon='export',
                slot=self.copy_full_source))
        menu.addAction(create_action(
            self, '复制原始答复', icon='export', slot=self.copy_reply))
        menu.addSeparator()

        selected = self.file_list.currentItem()
        if selected is not None:
            name = selected.text()
            menu.addAction(create_action(
                self, f'读取选中文件（{name}）',
                slot=lambda n=name: self.read_file(n)))
            menu.addAction(create_action(
                self, '复制文件名', icon='export',
                slot=lambda n=name: QtWidgets.QApplication.clipboard().setText(n)))
        if len(self.context_actions) > 0:
            menu.addSeparator()
            for action in self.context_actions:
                menu.addAction(action)
        return menu

    def contextMenuEvent(self, event):
        """右键菜单。

        Args:
            event: 右键事件。
        """
        self.get_context_menu().exec(event.globalPos())

    def refresh(self):
        """重新列举一次（**菜单「操作 → 刷新」的接口**）。

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
        email, date = self._last_query
        # 用户可能在期间改了输入框 —— 以输入框为准，但只在它能构成一次查询时
        current = self.get_query()
        if current[0] or current[1]:
            email, date = current
        self.email_view.setText(email)
        self.date_edit.setText(date)
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

        ⚠️ **四个线程都要放掉**（列举 / 读取 / 取邮箱 / 取名单）：漏掉任何一个，
        它就会在解释器退出时还活着，进程带着
        ``QThread: Destroyed while thread is still running`` **崩在退出阶段**。
        """
        for name in ('_list_worker', '_read_worker',
                     '_prefill_worker', '_user_list_worker'):
            setattr(self, name, None)
        self._busy = False

    def closeEvent(self, event):
        """窗口关闭时等后台请求收尾，避免线程还在跑时对象被销毁。

        ⚠️ **本方法只覆盖「控件被单独 close()」这一条路径**（例如直接运行
        :func:`test_1`）：走**标签页关闭**（``TabWidget.close_tab``）用的是
        ``deleteLater()``，**不发** ``closeEvent``，那条路径由
        :meth:`cleanup_before_tab_close` 负责。``wait(3000)`` 也兜不住长请求
        （最长 30 秒）—— 所以线程本身没有 parent、能活到自然结束。

        Args:
            event: 关闭事件。
        """
        for worker in (self._list_worker, self._read_worker,
                       self._prefill_worker, self._user_list_worker):
            if worker is not None and worker.isRunning():
                worker.wait(3000)
        event.accept()


def test_1():
    """自测入口：**不联网**，用示例数据把界面填满（``python zmlx/ui/tabs/feedbacks_view.py``）.

    ⚠️ **刻意不联网、不落盘**：只为让人一眼看到本控件的版式与三类内容的显示
    差别。真要看线上数据请从主窗口的「帮助 → 用户 → 反馈记录」进。

    ⚠️ 按 ``widget/AGENTS.md`` §4：这里**只造示例数据**，绝不改用户配置。
    """
    import sys
    import os

    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..')))

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = FeedbacksView(email='demo@example.com', date='2026-09-28')
    w.resize(1000, 680)

    # 假装已经列出了一天的文件（不联网）
    w._refresh_file_list([
        '20260928223007.json', '20260928224500.json', '20260928135816.json'])
    w._email_section.setVisible(True)
    for email in ('demo@example.com', 'someone@else.org'):
        w.email_list.addItem(email)

    # ① 合法 JSON -> 缩进显示
    record = {
        'ts': '2026-09-28T22:30:07+08:00',
        'machine': 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
        'user': 'u_demo',
        'text': '打开渗流模型时报错：\nKeyError: "fluid"\n\n复现步骤：\n1. …',
    }
    raw = json.dumps(record, ensure_ascii=False).encode('utf-8')
    w._on_read_reply(
        'Feedback: 20260928223007.json | Email: demo@example.com'
        ' | FileBase64: ' + __import__('base64').b64encode(raw).decode('ascii'),
        '往返耗时：0.42 s')

    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()

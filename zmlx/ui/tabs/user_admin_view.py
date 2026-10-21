"""管理员专用的「用户管理」页（``UserAdminView``）：左侧用户名单，右侧该用户的授权.

本页回答的问题
--------------

一个邮箱对应的授权**现在**是什么状态，以及把它改成什么样：

============  ==========================================================
位置           内容
============  ==========================================================
左侧           服务端全部用户的**姓名 + 邮箱**（可筛选；``user_list_detail``）
右侧           该用户的**姓名 / 单位 / 到期日 / 功能清单**
可改           只有**到期日**与**功能清单**两项（``update_user_info``）
============  ==========================================================

★ **姓名与单位是只读的**：它们来自左侧那份名单（服务端 ``Orgs:`` / ``Names:``
段），本页不改它们。服务端对 ``user`` / ``org`` 的写权限是「本人或管理员」，
技术上能改 —— 但这两个字段是**展示文本**，而本页的职责是**授权**（谁能用到什么
时候、能用哪些功能）。把它们做成只读，可以避免「手滑改掉别人的署名」这类与
授权无关的破坏。

★★ **到期日与功能清单只有管理员能改**（服务端 v3.31 的闸门，见
``license-check/user_info.py`` 的 :func:`update_fields`）：非管理员连改自己都会
拿到 ``Not permitted.``。所以本页一进来就**先验管理员身份**：不是管理员就**只**
显示「没有管理员权限」+ 他当前这份授权的状态 + 一条出路（去反馈 / 联系管理员），
**不显示任何管理功能**（见 :meth:`UserAdminView._apply_denied_info`）。

协议（三个动作，全部走唯一的 ``POST /`` + ``action`` 分流）
-----------------------------------------------------------

1. ``user_list_detail``（**仅管理员**）::

       UsersDetail: 4 | [Dropped: n] [Truncated: true] [NamesLimited: n]
                    | List: a@x; b@y | Names: 张; (none) | Orgs: 中科院; (none)

   ⚠️ ``Dropped:`` / ``Truncated:`` / ``NamesLimited:`` **只在非零时才出现**，
   所以**按段名解析**，绝不数段、也不假设顺序。★ ``List:`` / ``Names:`` /
   ``Orgs:`` 三段**按位置一一对应** —— 这也是 :meth:`_Protocol.parse_detail`
   自己解析（而不是复用 ``lic_utils.parse_user_list_detail``）的原因：那个函数
   只返回 ``[(姓名, 邮箱)]``，拿它的**下标**去配 ``Orgs:`` 会在「有条目被丢弃」
   时整体错位。

2. ``get_user_info``（本人或管理员）::

       {"action": "get_user_info", "field": "date",     "email": "..."}
       {"action": "get_user_info", "field": "features", "email": "..."}

   答复 ``UserInfo: <值>``。★ ``date`` 回桶里的原样文本（没设过是
   ``0001-01-01``，即判定侧的「必然已过期」）；``features`` 回 **JSON 数组文本**
   （``["*"]``）—— 不用 ``,`` 拼接，因为**逗号是合法的 feature 字符**。
   ⚠️ 两个字段各发一次请求：服务端的 ``field`` 白名单**一次只读一个**，没有
   「一次读多个」的入口。

3. ``update_user_info``（``date`` / ``features`` **仅管理员**）::

       {"action": "update_user_info", "email": "...",
        "date": "2027-04-01", "features": ["flow", "thermal"]}

   成功答复 ``Updated``。⚠️ **``features: []`` 是「一份都不授」**，与「不发这个
   字段」（= 不改）**不是一回事** —— 本页把「空文本」翻译成 ``[]``、把「没改动」
   翻译成不发，两者分行处理。

为什么所有操作都在后台线程
--------------------------

``web_license.*`` 的每个动作**都会阻塞**（单次最长 60 秒），且
``user_list_detail`` 在服务端要为**每个用户读一次许可**（硬上限 100 条，按
20 ms/GET 约 2 秒，大桶下更久）。放进界面线程就是「点开本页卡住」——
所以本页的**每一个**网络动作都走 :class:`_Worker`：线程里只取数据，结果经信号
回到主线程再更新界面（Qt 的界面只能在主线程碰）。

关标签时的两条防线（缺一就会**进程级崩溃**，不是异常）
------------------------------------------------------

1. **线程不设 parent** —— ``_Worker(...)`` 而不是 ``_Worker(..., parent=self)``：
   关标签走 ``deleteLater()``，会把**子对象**一起删掉，而联网请求几乎必然还在跑；
   ``QThread: Destroyed while thread is still running`` 直接 abort
   （``0xC0000409``）。
2. **模块级（类属性）容器持有强引用**，跑完 ``finished`` → 摘表 → ``deleteLater``
   —— 见 :attr:`_Jobs.RUNNING` 与 :meth:`_Jobs.keep`。

⚠️ **槽开头的 ``_Jobs.is_deleted(self)`` 不能省**：结果槽是用 lambda 连的
（为的是把「哪个线程 / 第几代」带进来），lambda **没有接收者对象**，Qt 不会
自动断连 —— 控件销毁后迟到的结果照样会调到它，碰子控件就抛
``RuntimeError: wrapped C/C++ object ... has been deleted``。

⚠️ **代次（``_generation``）用来丢弃过期结果**：用户在左侧连点几个用户是很自然
的动作，而 QThread 不能强杀。旧线程照旧跑完，结果回来时代号对不上就丢掉。

界面接线（按用户要求，本文件**之外一个字都没改**）
--------------------------------------------------

本文件提供 :func:`show_user_admin`（打开标签页）与 :func:`setup_ui`（注册 GUI
命令 + 菜单项）。``setup_ui`` **不会自己执行**，要挂上菜单只需在
``zmlx/ui/extra_setups/__init__.py`` 里加一行（与 ``message`` / ``mem_view``
同一种写法）::

    from zmlx.ui.tabs.user_admin_view import setup_ui
    setup_ui()

在挂上之前，也可以用控制台直接打开::

    from zmlx.ui.tabs.user_admin_view import show_user_admin
    show_user_admin()

Created by 小助手 (DeepSeek), 2026-10-18
"""

import datetime
import json
import re
import time

from zmlx.exts import web_license
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.utils.lic_utils import (ADMIN_EMAIL, DETAIL_SEP, bound_info,
                                     detail_of, find_field, format_elapsed,
                                     is_admin_by_web_license,
                                     is_user_list_detail, looks_like_email,
                                     wrap_text_to_width)


class _Protocol:
    """服务端答复的解析、校验与拼装（**纯函数**，不碰界面、不联网）.

    收进一个私有类当命名空间用：本模块的模块级只留 import / 类 / 入口函数
    （见 ``zmlx/ui/widgets/AGENTS.md`` 的「模块级内容」）。
    """

    #: ``get_user_info`` 的成功记号（**只认开头**，不要求整串相等）。
    TAG_FIELD = 'UserInfo:'

    #: ``update_user_info`` 的成功记号。
    TAG_UPDATED = 'Updated'

    #: ``user_list_detail`` 答复里的段名（小写比对）。
    SEG_LIST = 'list'
    SEG_NAMES = 'names'
    SEG_ORGS = 'orgs'
    SEG_DROPPED = 'dropped'
    SEG_TRUNCATED = 'truncated'
    SEG_LIMITED = 'nameslimited'

    #: 服务端对「这一条没有姓名 / 单位」的占位记号（空串会被 ``strip()`` 吃掉）。
    PLACEHOLDER = '(none)'

    #: 服务端对「这份许可没设到期日」的解释（必然已过期）。
    DATE_DEFAULT = '0001-01-01'

    #: 通配符功能名（= 全部功能）。
    ANY_FEATURE = '*'

    #: 功能条数上限（与服务端 ``check.MAX_FEATURES`` 一致；多兜一道）。
    MAX_FEATURES = 64

    #: 单个功能名的长度上限（与服务端 ``check.MAX_FEATURE_LEN`` 一致）。
    MAX_FEATURE_LEN = 64

    #: 写入侧的合法功能名：``[A-Za-z_][A-Za-z0-9_]*``（``"*"`` 单独放行）。
    #:
    #: ⚠️ 与服务端 ``check.is_valid_feature_name`` 逐字同构。这里**只用于本地
    #: 即时提示**（省一次「发出去再被 400 打回来」的往返）；**权威判据仍在服务端**
    #: —— 两者漂了时以服务端的答复为准，本页把它原样显示出来。
    FEATURE_NAME_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,%d}\Z'
                                 % (MAX_FEATURE_LEN - 1))

    @staticmethod
    def segments(reply):
        """把一句答复按 `` | `` 切成 ``{段名小写: 段值}``.

        ⚠️ **按段名取，不按下标取**：``Dropped:`` / ``Truncated:`` /
        ``NamesLimited:`` 是**可选段**，出现与否取决于数据，数段必然出错。

        Args:
            reply: 服务端答复正文（任意对象）。

        Returns:
            dict: 段名（小写、去空白）-> 段值（去空白）。同名段只留第一次出现。
        """
        out = {}
        for part in str(reply if reply is not None else '').split(DETAIL_SEP):
            part = part.strip()
            head, sep, tail = part.partition(':')
            if not sep:
                continue
            out.setdefault(head.strip().lower(), tail.strip())
        return out

    @staticmethod
    def parse_detail(reply):
        """解析 ``user_list_detail`` 的答复 → 名单 + 三个附加信息.

        ★ **三段按位置对齐**：``List:`` 的第 *i* 项配 ``Names:`` / ``Orgs:`` 的
        第 *i* 项。空值占位 ``(none)`` 还原成**空串**（界面据此只显示邮箱）。

        ⚠️ 条目按**形如邮箱**过滤、并按邮箱小写去重 —— 过滤与姓名/单位的配对
        **在同一次循环里做**，所以丢条目不会让后面整体错位（这正是本函数不复用
        ``lic_utils.parse_user_list_detail`` 的原因，见模块文档）。

        Args:
            reply: ``web_license.user_list_detail()`` 的返回值。

        Returns:
            dict | None: 不是本动作的成功答复时返回 ``None``；否则返回
            ``{'entries': [(姓名, 邮箱, 单位)], 'dropped': int,
            'truncated': bool, 'limited': int}``。
        """
        text = str(reply if reply is not None else '').strip()
        if not is_user_list_detail(text):
            return None

        segs = _Protocol.segments(text)

        def split(name):
            value = segs.get(name)
            if value is None:
                return []
            return [item.strip() for item in value.split(';')]

        emails, names, orgs = (split(_Protocol.SEG_LIST),
                               split(_Protocol.SEG_NAMES),
                               split(_Protocol.SEG_ORGS))

        entries, seen = [], set()
        for index, email in enumerate(emails):
            if not looks_like_email(email):
                continue
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            name = names[index] if index < len(names) else ''
            org = orgs[index] if index < len(orgs) else ''
            if name == _Protocol.PLACEHOLDER:
                name = ''
            if org == _Protocol.PLACEHOLDER:
                org = ''
            entries.append((name, email, org))

        return {
            'entries': entries,
            'dropped': _Protocol._to_int(segs.get(_Protocol.SEG_DROPPED)),
            'truncated': str(segs.get(_Protocol.SEG_TRUNCATED, '')).lower()
            == 'true',
            'limited': _Protocol._to_int(segs.get(_Protocol.SEG_LIMITED)),
        }

    @staticmethod
    def _to_int(text):
        """把段值转成非负整数（解析不出来就当 0）.

        Args:
            text: 段值（可能为 ``None``）。

        Returns:
            int: 非负整数。
        """
        try:
            return max(0, int(str(text).strip()))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def field_value(reply):
        """取 ``get_user_info`` 答复里的值.

        ⚠️ **成功时值可能是空串**（例如 ``org`` 没填），所以不能拿「非空」判成败
        —— 必须看开头那个记号。

        Args:
            reply: 服务端答复正文。

        Returns:
            tuple: ``(值, 错误)``。成功时错误为 ``None``；失败时值为 ``None``、
            错误是服务端原话（或本地的一句兜底）。
        """
        text = str(reply if reply is not None else '').strip()
        tag = _Protocol.TAG_FIELD
        if text[:len(tag)].lower() != tag.lower():
            return None, text or '（服务端没有答复内容）'
        return text[len(tag):].strip(), None

    @staticmethod
    def is_updated(reply):
        """判断答复是否为 ``update_user_info`` 的成功正文.

        Args:
            reply: 服务端答复正文。

        Returns:
            bool: 以 ``Updated`` 开头返回 True。
        """
        text = str(reply if reply is not None else '').strip()
        tag = _Protocol.TAG_UPDATED
        return text[:len(tag)].lower() == tag.lower()

    @staticmethod
    def verdict_of(reply):
        """把 ``check`` 答复的首词翻成一句中文状态（「无权限页」要显示它）.

        ★ 只认 ``Yes`` / ``No`` 两个首词（大小写不敏感）：其余一切（连不上、
        ``dll not found``、空答复）一律 ``—`` —— 那些情况下**没有**判定结论，
        编一个「未通过」会让人以为自己的授权真的失效了。

        Args:
            reply: ``web_license.check`` 的答复。

        Returns:
            str: ``'有效'`` / ``'未通过'`` / ``'—'``。
        """
        head = str(reply if reply is not None else '').strip() \
            .split(DETAIL_SEP)[0].strip().lower()
        if head == 'yes':
            return '有效'
        if head == 'no':
            return '未通过'
        return '—'

    @staticmethod
    def features_of(reply):
        """从 ``check`` 答复里取 ``Features:`` 段（展示用，可能为空串）.

        ⚠️ 这里是服务端**给人看**的写法（``*`` 或 ``, `` 分隔），与
        ``get_user_info`` 回的 **JSON 数组**不是一回事 —— 本页只用它做「一眼看
        得出授了什么」，**不用它做判定**，也不拿它回写。

        Args:
            reply: ``web_license.check`` 的答复。

        Returns:
            str: 功能段的原文；没有该段时返回空串。
        """
        return find_field(detail_of(reply), 'Features')

    @staticmethod
    def parse_features(text):
        """把 ``features`` 的答复值（JSON 数组文本）解析成列表.

        Args:
            text: ``UserInfo:`` 之后的那段文本。

        Returns:
            list | None: 字符串列表；不是 JSON 数组时返回 ``None``。
        """
        try:
            items = json.loads(str(text if text is not None else '').strip())
        except (TypeError, ValueError):
            return None
        if not isinstance(items, list):
            return None
        return [str(item) for item in items]

    @staticmethod
    def format_features(items):
        """把功能列表写成编辑框里的文本（**一行一个**）.

        ★ 为什么不用逗号拼：**逗号是合法的 feature 字符**（服务端只禁 ``|`` 与
        ``:``），拼起来就分不清「一个叫 ``a, b`` 的功能」与「两个功能」。

        Args:
            items: 字符串列表。

        Returns:
            str: 用 ``'\\n'`` 连接的文本；空列表返回空串。
        """
        return '\n'.join(str(item) for item in (items or []))

    @staticmethod
    def parse_date_text(text):
        """校验编辑框里的到期日文本.

        ★ 判据与服务端 :func:`user_info._validated_expiry` 同构：**10 个字符的
        ``YYYY-MM-DD``** + 那一天必须真实存在。⚠️ 少判长度会踩
        ``date.fromisoformat`` 在 Python 3.11+ 接受紧凑写法 ``20261001`` 的坑。

        ⚠️ **过去的日子是合法的**：把到期日设成昨天正是「立刻停掉这份授权」的
        手段，不该被本地拦住。

        Args:
            text: 用户输入。

        Returns:
            tuple: ``(值, 错误)``。``值`` 为空串表示「不修改」（空输入）；
            有错误时值为 ``None``。
        """
        value = str(text if text is not None else '').strip()
        if not value:
            return '', None
        if len(value) != 10 or value[4] != '-' or value[7] != '-':
            return None, '到期日必须是 10 个字符的 YYYY-MM-DD（留空 = 不修改）'
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            return None, '到期日不是真实存在的日期：%s' % value
        return value, None

    @staticmethod
    def parse_features_text(text):
        """校验编辑框里的功能清单文本（一行一个）.

        ★ **空文本 = 空列表**（= 一份都不授）。这与「没改动」是两件事：后者由
        调用方比对原始值判定，**不在这里**折叠。

        ⚠️ 去重**保序**：重复项没有意义，但替用户重排顺序是「静默改写」，本项目
        一贯避免 —— 写进去的顺序就是管理员给的顺序（服务端也照原样存）。

        Args:
            text: 编辑框里的多行文本。

        Returns:
            tuple: ``(列表, 错误)``。有错误时列表为 ``None``。
        """
        items, seen = [], set()
        for line in str(text if text is not None else '').splitlines():
            item = line.strip()
            if not item or item in seen:
                continue
            seen.add(item)
            items.append(item)

        if len(items) > _Protocol.MAX_FEATURES:
            return None, ('功能最多 %d 项（当前 %d 项）'
                          % (_Protocol.MAX_FEATURES, len(items)))
        for item in items:
            if item == _Protocol.ANY_FEATURE:
                continue
            if not _Protocol.FEATURE_NAME_RE.match(item):
                return None, ('「%s」不是合法功能名：只能用字母、数字、下划线，'
                              '且不能以数字开头（"*" 表示全部功能）' % item)
        return items, None


class _Jobs:
    """在**后台线程**里跑的纯数据任务，以及线程的持有与销毁（**绝不碰界面**）.

    每个方法的返回值都是一个 ``dict``，经 :class:`_Worker` 的信号原样回到主线程
    —— 这样「一次请求的结果」只有一种形态，界面侧的分支才好写。
    """

    #: 正在跑的后台线程（**类属性强引用**，见模块文档的两条防线）。
    #:
    #: ⚠️ 做成类属性而不是模块级变量：模块级只该有 import / 类 / 入口函数。
    RUNNING = []

    @staticmethod
    def keep(thread):
        """把刚建好的线程登记进来，并安排它跑完后自我清理.

        ⚠️ 线程**不设 parent**（调用方负责 ``_Worker(kind, job)``）；这里持有
        Python 引用，否则它可能在运行中被 GC 掉 —— 同样是进程级崩溃。

        Args:
            thread: 刚创建、尚未 ``start()`` 的 :class:`QtCore.QThread`。
        """
        thread.finished.connect(lambda t=thread: _Jobs.forget(t))
        thread.finished.connect(thread.deleteLater)
        _Jobs.RUNNING.append(thread)

    @staticmethod
    def forget(thread):
        """把一个跑完的线程从登记表里摘掉（主线程调用）.

        Args:
            thread: 已经发出 ``finished`` 的线程。
        """
        try:
            _Jobs.RUNNING.remove(thread)
        except ValueError:
            pass

    @staticmethod
    def is_deleted(obj):
        """判断一个 Qt 对象的底层 C/C++ 对象是否已被销毁.

        ⚠️ **名字必须按绑定逐个试**：PyQt6 的 sip 在 ``PyQt6.sip`` 下，顶层
        ``import sip`` 在 PyQt6 环境里取不到（会静默退化成「没被删」= 没生效）。

        Args:
            obj: 任意 Qt 对象。

        Returns:
            bool: 底层对象已被销毁返回 True。
        """
        for name in ('PyQt6.sip', 'PyQt5.sip', 'sip', 'shiboken6',
                     'shiboken2'):
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
                # ⚠️ shiboken 的语义与 sip 相反：isValid 为真 = 还活着
                try:
                    return not bool(checker(obj))
                except Exception:
                    return False
        return False

    @staticmethod
    def admin():
        """确认本机是不是管理员，并顺手取回「当前这份授权」的信息.

        ★ ``read_cache=False``：结果缓存是按查询名长期保留的，读缓存可能拿到
        「绑定之前」的旧结论（见 ``lic_utils.is_admin_by_web_license``）。

        ★★ **非管理员时多读一次到期日**（``get_user_info`` 的 ``email`` 留空 =
        读自己，服务端允许「本人读自己」）：判定本身**不带**到期日，而这一页要
        告诉用户「你的授权什么时候到期」—— 那正是他接下来会去反馈的事情。
        ⚠️ 只在**已经绑定邮箱**时才多问这一次：没绑定时问也是白问（服务端会让我
        先去注册），白多一次往返。

        Returns:
            dict: ``{'admin', 'reply', 'verdict', 'info', 'date'}``。
            ``verdict`` 是 ``有效`` / ``未通过`` / ``—``；``info`` 是
            ``{'email', 'user', 'org'}``（未绑定时为空字典）；``date`` 是
            ``YYYY-MM-DD``（取不到就是空串）。
        """
        try:
            reply = str(web_license.check('*', read_cache=False) or '')
        except Exception as err:      # 防御性：check 按契约不抛异常
            return {'admin': False, 'verdict': '—', 'info': {},
                    'date': '',
                    'reply': '%s: %s' % (type(err).__name__, err)}

        payload = {
            'admin': is_admin_by_web_license(reply=reply),
            'reply': reply,
            'verdict': _Protocol.verdict_of(reply),
            # ⚠️ bound_info 只在「真的绑定了邮箱」时返回内容（见那边的说明），
            #    所以未登录 / 未授权时这里天然是空字典。
            'info': bound_info(reply),
            'date': '',
        }
        if not payload['admin'] and payload['info']:
            try:
                date_reply = str(web_license.request(
                    action='get_user_info', field='date') or '')
            except Exception:         # 读不到到期日不该让整页打不开
                date_reply = ''
            value, error = _Protocol.field_value(date_reply)
            if error is None and value:
                payload['date'] = value
        return payload

    @staticmethod
    def users():
        """取用户名单（姓名 + 邮箱 + 单位）.

        ⚠️ 失败**不重试第二遍以上**：实测偶发空答复（链路层的偶发），重试一次
        有用；再失败就当「拿不到」，由界面把服务端原话显示出来 —— 反复重试只会
        让打开页面变得更慢。

        Returns:
            dict: :meth:`_Protocol.parse_detail` 的结果，外加 ``'ok'`` 与
            ``'reply'``；拿不到时 ``'entries'`` 是空列表。
        """
        reply = str(web_license.user_list_detail() or '')
        data = _Protocol.parse_detail(reply)
        if data is None:
            retry = str(web_license.user_list_detail() or '')
            retried = _Protocol.parse_detail(retry)
            if retried is not None:
                reply, data = retry, retried
        if data is None:
            return {'ok': False, 'reply': reply, 'entries': [],
                    'dropped': 0, 'truncated': False, 'limited': 0}
        data['ok'] = True
        data['reply'] = reply
        return data

    @staticmethod
    def license_of(email):
        """读一个用户的**到期日**与**功能清单**（两次 ``get_user_info``）.

        ⚠️ 两次请求而不是一次：服务端的 ``field`` 白名单**一次只读一个字段**，
        没有批量入口。两个都失败时把**第一条**错误报出来（够定位问题）。

        Args:
            email: 要读谁的邮箱（管理员可以读任意用户）。

        Returns:
            dict: ``{'ok', 'error', 'date', 'features', 'replies'}``。
        """
        date_reply = str(web_license.request(
            action='get_user_info', field='date', email=email) or '')
        feat_reply = str(web_license.request(
            action='get_user_info', field='features', email=email) or '')

        date_value, date_err = _Protocol.field_value(date_reply)
        feat_text, feat_err = _Protocol.field_value(feat_reply)
        features = _Protocol.parse_features(feat_text) if feat_err is None \
            else None

        error = date_err or feat_err
        if error is None and features is None:
            error = '功能清单无法解析：%r' % feat_text
        return {
            'ok': error is None,
            'error': error or '',
            'date': date_value if date_err is None else '',
            'features': features if features is not None else [],
            'replies': (date_reply, feat_reply),
        }

    @staticmethod
    def update(email, date_value=None, features=None):
        """提交到期日 / 功能清单.

        ★ **``None`` = 不改**（:meth:`WebLicense.request` 会把值为 ``None`` 的
        字段整段丢掉）；``features=[]`` 是「一份都不授」，**必须真的发出去**。

        Args:
            email: 要改谁的邮箱。
            date_value: ``YYYY-MM-DD``；``None`` 表示不改。
            features: 字符串列表；``None`` 表示不改。

        Returns:
            dict: ``{'ok': bool, 'reply': str}``。
        """
        options = {'action': 'update_user_info', 'email': email}
        if date_value is not None:
            options['date'] = date_value
        if features is not None:
            options['features'] = list(features)
        reply = str(web_license.request(**options) or '')
        return {'ok': _Protocol.is_updated(reply), 'reply': reply}


class _Worker(QtCore.QThread):
    """在后台线程里跑一个 :class:`_Jobs` 任务（**绝不碰界面**）.

    Attributes:
        sig_done: 信号，携带 ``(种类, 结果 dict, 耗时文本)``。耗时单独一个参数，
            不挤进结果里 —— 那是「界面 waited 多久」的补充信息，不是数据。
    """

    sig_done = QtCore.pyqtSignal(str, object, str)

    def __init__(self, kind, job, parent=None):
        """初始化.

        Args:
            kind: 任务种类（``'admin'`` / ``'users'`` / ``'license'`` /
                ``'update'``），原样回传给主线程做分流。
            job: 无参可调用对象，返回值必须是 ``dict``。
            parent: Qt 父对象。⚠️ 正常调用应当**留空**（见模块文档的防线 1）。
        """
        super(_Worker, self).__init__(parent)
        self._kind = kind
        self._job = job
        self.setObjectName('UserAdminWorker:%s' % kind)

    def run(self):
        """线程体：跑任务并把结果发回主线程.

        ⚠️ **异常绝不能逃出 ``run``**：逃出去线程会静默死掉、信号永不发出，界面
        就永远停在「读取中……」而按钮一直禁用 —— 看起来像卡死。
        """
        start = time.perf_counter()
        try:
            payload = self._job()
        except Exception as err:      # 防御性：_Jobs 里各方法按契约不抛异常
            payload = {'ok': False, 'error': '%s: %s' % (type(err).__name__,
                                                         err)}
        if not isinstance(payload, dict):
            payload = {'ok': False,
                       'error': '内部错误：任务没有返回 dict（%r）' % (payload,)}
        self.sig_done.emit(self._kind, payload,
                           format_elapsed(time.perf_counter() - start))


class UserAdminView(QtWidgets.QWidget):
    """「用户管理」页：左侧用户名单，右侧该用户的授权（**仅管理员**）.

    进来先验管理员身份（后台线程）。不是管理员时**不显示管理功能**，只显示
    「没有管理员权限」+ 当前这份授权的状态（状态 / 邮箱 / 姓名 / 单位 / 到期日 /
    功能）+ 一条出路（「提交反馈」或联系管理员）；是管理员才搭出左右两栏。
    到期日与功能清单可改，改完点「保存修改」提交。

    ⚠️ 本控件**只被装配层打开成标签页**，不被任何控件复用 —— 所以它归
    ``zmlx/ui/tabs/``（判据见同目录 ``AGENTS.md`` §1）。
    """

    #: 左侧面板宽度（固定）：邮箱很长，但固定的窄栏 + 折行比「自适应宽度」好用
    #: —— 后者会随着最长邮箱把右侧挤扁。
    LIST_WIDTH = 260

    #: 统一的边距与间距。
    MARGIN = 8
    GAP = 6

    #: :class:`QtWidgets.QStackedWidget` 的三页。
    PAGE_CHECKING = 0
    PAGE_DENIED = 1
    PAGE_MAIN = 2

    #: 无权限页顶上的那句说明（**始终是这一句**，不随答复变化）。
    DENIED_SUBTITLE = '本页只对管理员开放。'

    #: 已绑定邮箱时给出的出路。
    DENIED_HINT = ('如需修改姓名、单位、到期时间或功能清单，请点下面的「提交反馈」'
                   '写明需求（会自动带上本机信息），或直接联系管理员：%s')

    #: **未绑定**（或授权已失效）时给出的出路：这时该先去登录，而不是急着反馈。
    DENIED_HINT_UNBOUND = ('本机还没有绑定邮箱，或授权已失效。请先通过「帮助 → 用户 → 登录」'
                           '绑定邮箱；如需修改姓名、单位、到期时间或功能清单，'
                           '请联系管理员：%s')

    def __init__(self, parent=None):
        """初始化控件（**不联网**：管理员检查在 ``showEvent`` 里才起）.

        Args:
            parent: Qt 父对象。
        """
        super(UserAdminView, self).__init__(parent)

        #: 服务端名单：``[(姓名, 邮箱, 单位)]``
        self._entries = []
        #: 当前选中用户的邮箱（空串 = 还没选）
        self._current_email = ''
        #: 当前用户**已经从服务端读到**的原始值（用来判「改了什么」）
        self._origin = {'date': '', 'features': []}
        #: 正在跑的后台线程（最新那一个；旧的仍在跑但结果会被丢掉）
        self._worker = None
        #: 有请求在飞：按钮与输入框禁用，防连点
        self._busy = False
        #: 代次：每发起一次请求 +1，旧线程的结果靠它对不上而作废
        self._generation = 0
        #: 是否已确认管理员权限 / 是否已是管理员
        self._admin_checked = False
        self._admin = False
        #: 名单是否已经成功取到过（``refresh()`` 据此决定要不要补一次）
        self._list_loaded = False
        #: 名单请求是否在飞（**不叠加**：它是最贵的一个请求）
        self._list_pending = False

        self.setWindowTitle('用户管理')
        self._build_ui()
        self._update_buttons()

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------

    def _build_ui(self):
        """搭出三页（检查中 / 无权限 / 主界面）.

        ★ 三页一次建好、用 ``QStackedWidget`` 切换：非管理员**看到**的只有一句
        「没有管理员权限」（另外两页不可见、也拿不到焦点），而管理员从检查中切到
        主界面时不必再等一次布局 —— 那一刻数据已经在路上了。

        ⚠️ 「不显示」不等于「不存在」：主界面即使在无权限页时也是**建好的**。
        所以**不要**把「没有权限」这条判据做成「靠某个子控件为空来判断」——
        判据只有 :attr:`_admin` 一个。
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QtWidgets.QStackedWidget()
        layout.addWidget(self._stack)

        self._stack.addWidget(self._build_checking_page())
        self._stack.addWidget(self._build_denied_page())
        self._stack.addWidget(self._build_main_page())
        self._stack.setCurrentIndex(self.PAGE_CHECKING)

    def _build_checking_page(self):
        """第 0 页：等待管理员检查结果.

        Returns:
            QtWidgets.QWidget: 只含一句提示的页面。
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addStretch(1)
        label = QtWidgets.QLabel('正在检查管理员权限……')
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch(1)
        return page

    def _build_denied_page(self):
        """第 1 页：没有管理员权限 —— **顺便给用户看清自己的授权** + 一条出路.

        ★ 为什么这一页不只是「一句没权限」：用户来这里十有八九是想**改**自己的
        姓名 / 单位 / 到期日 / 功能，而这几项他都改不了。让他看到「现在是什么
        状态」，再告诉他「要改就反馈或找管理员」，比一句冷冰冰的拒绝有用得多。

        ★ 这些信息**全部来自同一次判定**（见 :meth:`_Jobs.admin`）：判定答复里
        本来就有 ``User:`` / ``Org:`` / ``Email:`` / ``Features:``，到期日则多用
        一次 ``get_user_info``（本人读自己，服务端允许）。**没有任何信息是为这一
        页新开接口拿的**。

        Returns:
            QtWidgets.QWidget: 无权限提示页。
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.addStretch(1)

        # 内容收在一个定宽的块里居中：不加宽度约束时，两个 stretch 会把这块压到
        # 它自己 sizeHint 那么窄（长邮箱、长单位就会被折成一条条碎片）；铺满全宽
        # 又会让指引那几行字横着拉到没人愿意读。所以给它一个明确的宽区间。
        body = QtWidgets.QWidget()
        body.setMinimumWidth(520)
        body.setMaximumWidth(620)
        inner = QtWidgets.QVBoxLayout(body)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(self.GAP)

        title = QtWidgets.QLabel('没有管理员权限')
        font = title.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        self.denied_detail = QtWidgets.QLabel(self.DENIED_SUBTITLE)
        self.denied_detail.setWordWrap(True)
        self.denied_detail.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # ⚠️ 置灰**跟随主题**（不写死颜色）：本程序会加载用户可编辑的样式表，
        #    还有暗色模式，写死色值两边都会打架。
        self.denied_detail.setEnabled(False)
        inner.addWidget(self.denied_detail)

        inner.addSpacing(6)
        info_title = QtWidgets.QLabel('当前授权信息')
        info_title.setEnabled(False)
        inner.addWidget(info_title)

        #: 无权限页上那几行的值标签：键 = 行名（见 :meth:`_apply_denied_info`）。
        self.denied_values = {}
        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(self.GAP)
        # ⚠️ 横向多留一点：邮箱紧贴着「登录邮箱」这四个字会看错行。
        form.setHorizontalSpacing(14)
        for key, text in (('verdict', '授权状态'), ('email', '登录邮箱'),
                          ('user', '姓名'), ('org', '单位'),
                          ('date', '到期日'), ('features', '功能')):
            value = QtWidgets.QLabel('—')
            value.setWordWrap(True)
            value.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            self.denied_values[key] = value
            form.addRow(text, value)
        inner.addLayout(form)

        inner.addSpacing(6)
        self.denied_hint = QtWidgets.QLabel(self.DENIED_HINT % ADMIN_EMAIL)
        self.denied_hint.setWordWrap(True)
        self.denied_hint.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(self.denied_hint)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.feedback_button = QtWidgets.QPushButton('提交反馈')
        self.feedback_button.setToolTip('打开「反馈」页，把要改的内容写给作者。')
        self.feedback_button.clicked.connect(self._open_feedback)
        buttons.addWidget(self.feedback_button)

        self.retry_button = QtWidgets.QPushButton('重新检查')
        self.retry_button.setFlat(True)
        self.retry_button.setToolTip('重新向服务端确认一次管理员权限。')
        self.retry_button.clicked.connect(self._check_admin)
        buttons.addWidget(self.retry_button)
        buttons.addStretch(1)
        inner.addLayout(buttons)

        # 服务端原话（小字、跟着上面那块一起限宽）：判定失败时它是唯一能说清
        # 「为什么」的东西（``dll not found`` / ``not available`` / 空答复）。
        self.denied_reply = QtWidgets.QLabel('')
        self.denied_reply.setWordWrap(True)
        self.denied_reply.setEnabled(False)
        self.denied_reply.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(self.denied_reply)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(body)
        row.addStretch(1)
        layout.addLayout(row)

        layout.addStretch(2)
        return page

    def _open_feedback(self):
        """打开「帮助 → 用户 → 反馈」那一页（**不自己造一个反馈入口**）.

        ⚠️ 走 ``gui.show_feedback()``（``MainWindow.show_feedback`` 自动注册的
        命令）而不是直接建 ``FeedbackTool``：反馈正文的拼装、落盘、去重都在那个
        控件里，这里再造一份就是第二套语义。

        ⚠️ 无头模式 / 尚未装配主窗口时 ``gui.show_feedback()`` 是空操作，不会抛
        异常；真失败了也只是把状态行改一句话，不影响这一页。
        """
        try:
            gui.show_feedback()
        except Exception as err:
            self.denied_reply.setText('打不开反馈页：%s（也可以直接联系 %s）'
                                      % (err, ADMIN_EMAIL))

    def _build_main_page(self):
        """第 2 页：左名单 + 右授权.

        Returns:
            QtWidgets.QWidget: 主界面。
        """
        page = QtWidgets.QWidget()
        shell = QtWidgets.QHBoxLayout(page)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        shell.addWidget(self._build_user_list())
        shell.addWidget(self._build_detail_panel(), 1)
        return page

    def _build_user_list(self):
        """左侧：筛选框 + 用户列表 + 刷新按钮.

        Returns:
            QtWidgets.QWidget: 左侧面板（固定宽度）。
        """
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(self.LIST_WIDTH)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(self.MARGIN, self.MARGIN, self.GAP,
                                  self.MARGIN)
        layout.setSpacing(self.GAP)

        self.list_title = QtWidgets.QLabel('用户')
        self.list_title.setEnabled(False)    # 置灰跟随主题
        layout.addWidget(self.list_title)

        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText('筛选姓名 / 邮箱')
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._populate)
        layout.addWidget(self.filter_edit)

        self.user_list = QtWidgets.QListWidget()
        self.user_list.setWordWrap(True)
        # ⚠️ QListWidgetItem 默认带 ItemIsEditable，而默认编辑触发器含双击 ——
        #    双击会弹出就地编辑器（WSLg 下再双击另一个条目会**段错误**）。
        #    本列表是只读名单，直接关掉总闸。
        self.user_list.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.user_list.setToolTip('点一个用户，右侧显示并编辑它的授权。\n'
                                  '名单由服务端维护，仅管理员可见。')
        self.user_list.currentItemChanged.connect(self._on_current_changed)
        layout.addWidget(self.user_list, 1)

        self.list_status = QtWidgets.QLabel('')
        self.list_status.setWordWrap(True)
        self.list_status.setEnabled(False)
        layout.addWidget(self.list_status)

        self.refresh_button = QtWidgets.QPushButton('刷新名单')
        self.refresh_button.setFlat(True)
        self.refresh_button.setToolTip('重新向服务端要一次用户名单'
                                       '（服务端会为每用户读一次许可，可能要几秒）。')
        self.refresh_button.clicked.connect(
            lambda: self._load_users(force=True))
        layout.addWidget(self.refresh_button)

        return panel

    def _build_detail_panel(self):
        """右侧：用户信息（只读）+ 到期日 / 功能清单（可改）+ 状态行.

        Returns:
            QtWidgets.QWidget: 右侧面板。
        """
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN,
                                  self.MARGIN)
        layout.setSpacing(self.GAP)

        self.email_label = QtWidgets.QLabel('（未选择用户）')
        font = self.email_label.font()
        font.setBold(True)
        self.email_label.setFont(font)
        self.email_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.email_label.setWordWrap(True)
        layout.addWidget(self.email_label)

        self.name_label = QtWidgets.QLabel('姓名：—')
        self.name_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.name_label)

        self.org_label = QtWidgets.QLabel('单位：—')
        self.org_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.org_label)

        layout.addWidget(self._separator())

        # ---- 可改的两项 ----
        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(self.GAP)

        self.date_edit = QtWidgets.QLineEdit()
        self.date_edit.setPlaceholderText('YYYY-MM-DD（留空 = 不修改）')
        self.date_edit.setToolTip('这份授权的到期日。设成过去的日子 = 立刻停掉它。')
        form.addRow('到期日', self.date_edit)

        self.features_edit = QtWidgets.QPlainTextEdit()
        self.features_edit.setPlaceholderText('每行一个功能名')
        self.features_edit.setMinimumHeight(110)
        # ⚠️ 设上限：QPlainTextEdit 的垂直策略是 Expanding，不封顶时它会把右侧
        #    面板的剩余高度全吃掉，把状态行挤到最下面。
        self.features_edit.setMaximumHeight(220)
        self.features_edit.setToolTip(
            '这一份授权支持的功能，一行一个。\n'
            '合法名形如 flow / thermal / shiyou_2；\n'
            '"*" 表示全部功能；留空 = 一份功能都不授。')
        form.addRow('功能清单', self.features_edit)
        layout.addLayout(form)

        self.hint_label = QtWidgets.QLabel(
            '功能名只能用字母、数字、下划线（不能以数字开头），一行一个；'
            '"*" 表示全部功能。留空 = 一份都不授。')
        self.hint_label.setWordWrap(True)
        self.hint_label.setEnabled(False)
        layout.addWidget(self.hint_label)

        buttons = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton('保存修改')
        self.save_button.setToolTip('把改动提交给服务端（只有到期日与功能清单会被写）。')
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.save_button)

        self.reload_button = QtWidgets.QPushButton('重新读取')
        self.reload_button.setToolTip('放弃未提交的改动，重新读这一份授权。')
        self.reload_button.clicked.connect(
            lambda: self._select_email(self._current_email))
        buttons.addWidget(self.reload_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        layout.addWidget(self._separator())

        self.status_label = QtWidgets.QLabel('')
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        return panel

    @staticmethod
    def _separator():
        """一条 1px 水平细线（用留白 + 细线划分区域，不画分组框）.

        Returns:
            QtWidgets.QFrame: 水平细线。
        """
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        return line

    # ------------------------------------------------------------------
    # 后台请求的统一入口
    # ------------------------------------------------------------------

    def _begin(self, kind, job):
        """起一个后台任务，结果回到 :meth:`_on_done`.

        ⚠️ **线程不设 parent**（防线 1）；登记进 :attr:`_Jobs.RUNNING`
        （防线 2）；信号用 lambda 连是为了把「哪个线程 / 第几代」带进来 ——
        代价是必须自己判控件是否已销毁。

        Args:
            kind: 任务种类。
            job: 无参可调用对象（在**后台线程**里执行，绝不碰界面）。
        """
        self._generation += 1
        generation = self._generation
        worker = _Worker(kind, job)      # 不设 parent，见模块文档
        worker.sig_done.connect(
            lambda k, p, e, w=worker, g=generation:
            self._on_done(w, g, k, p, e))
        worker.finished.connect(lambda w=worker: self._on_finished(w))
        self._worker = worker
        self._busy = True
        _Jobs.keep(worker)
        worker.start()
        self._update_buttons()

    def _on_finished(self, worker):
        """线程结束（主线程调用）：摘登记表、放掉「忙」标记.

        ⚠️ 只在自己仍是**最新**那个线程时才清 ``_busy`` —— 否则「结果回来后立刻
        起了下一个请求」会被这次收尾误清掉。

        Args:
            worker: 刚结束的线程。
        """
        _Jobs.forget(worker)
        if _Jobs.is_deleted(self):
            return
        if self._worker is worker:
            self._worker = None
            self._busy = False
            self._update_buttons()

    def _on_done(self, worker, generation, kind, payload, elapsed):
        """后台结果回到主线程：先判有效性，再按种类分流.

        Args:
            worker: 发出结果的线程（用于自检，不参与分支）。
            generation: 发起时的代次。
            kind: 任务种类。
            payload: 结果 dict。
            elapsed: 耗时文本（可能为空串）。
        """
        if _Jobs.is_deleted(self):
            return                       # 控件已随标签页关闭被销毁
        if generation != self._generation:
            return                       # 过期结果（用户已经换了目标）
        if not isinstance(payload, dict):
            return
        if kind == 'admin':
            self._apply_admin(payload, elapsed)
        elif kind == 'users':
            self._apply_users(payload, elapsed)
        elif kind == 'license':
            self._apply_license(payload, elapsed)
        elif kind == 'update':
            self._apply_update(payload, elapsed)

    # ------------------------------------------------------------------
    # 管理员检查
    # ------------------------------------------------------------------

    def _check_admin(self):
        """（重新）确认管理员权限 —— 后台线程，最长 60 秒."""
        self._admin = False
        self._admin_checked = False
        self.denied_detail.setText(self.DENIED_SUBTITLE)
        self._stack.setCurrentIndex(self.PAGE_CHECKING)
        self._begin('admin', _Jobs.admin)

    def _apply_admin(self, payload, elapsed):
        """管理员检查的结果.

        ⚠️ **不是管理员时主界面不显示**（用户要求）：只显示「没有管理员权限」+
        当前这份授权的信息 + 一条出路（反馈 / 联系管理员）。服务端答复本身也留着
        —— 否则「连不上」「没登录」「邮箱不是作者的」三种情况在界面上长得一模
        一样，用户无从下手。

        Args:
            payload: :meth:`_Jobs.admin` 的返回值。
            elapsed: 耗时文本。
        """
        self._admin_checked = True
        self._admin = bool(payload.get('admin'))

        if not self._admin:
            self._stack.setCurrentIndex(self.PAGE_DENIED)
            self._apply_denied_info(payload)
            self._update_buttons()
            return

        self._stack.setCurrentIndex(self.PAGE_MAIN)
        self._status('已确认管理员权限。%s' % elapsed)
        self._update_buttons()
        if not self._list_loaded:
            self._load_users()

    def _apply_denied_info(self, payload):
        """把「当前这份授权」填进无权限页（**全部来自判定那一次请求**）.

        ⚠️ 未绑定时字段一律 ``—``，并把出路换成「先去登录」：对着一个还没登录的
        人强调「请反馈」是错的 —— 他连自己是谁都还没告诉服务端。

        Args:
            payload: :meth:`_Jobs.admin` 的返回值（可能只有 ``reply``）。
        """
        info = payload.get('info') or {}
        reply = str(payload.get('reply') or '')
        email = str(info.get('email') or '').strip()
        features = _Protocol.features_of(reply).strip()
        if features == _Protocol.ANY_FEATURE:
            features = '*（全部功能）'

        values = {
            'verdict': str(payload.get('verdict') or '—'),
            'email': email or '未登录 / 未绑定邮箱',
            'user': str(info.get('user') or '').strip() or '—',
            'org': str(info.get('org') or '').strip() or '—',
            'date': str(payload.get('date') or '').strip() or '—',
            'features': features or '—',
        }
        for key, label in self.denied_values.items():
            label.setText(values.get(key, '—'))

        self.denied_reply.setText('服务端答复：%s' % (reply or '（空答复）'))
        self.denied_hint.setText(
            (self.DENIED_HINT if email else self.DENIED_HINT_UNBOUND)
            % ADMIN_EMAIL)

    # ------------------------------------------------------------------
    # 名单
    # ------------------------------------------------------------------

    def _load_users(self, force=False):
        """在后台拉一次用户名单.

        ⚠️ **只看 ``_list_pending``、不看 ``_busy``**：管理员检查刚成功时那个线程
        还没发出 ``finished``（``_busy`` 仍是 True），而这时正该接着拉名单 ——
        用 ``_busy`` 当闸门会让名单永远不加载。

        Args:
            force: 忽略「已经拉过」的记录，强制再拉一次（「刷新名单」按钮用）。
        """
        if not self._admin:
            return
        if self._list_loaded and not force:
            return
        if self._list_pending:
            # ⚠️ 名单不叠加：服务端要为每个用户读一次许可，重复发只会更慢。
            self._status('正在读取名单，请稍候。')
            return
        self._list_pending = True
        self.list_status.setText('正在读取用户名单……')
        self._begin('users', _Jobs.users)

    def _apply_users(self, payload, elapsed):
        """名单回来了：填充左侧列表，并把服务端的附加提示写进状态行.

        ⚠️ **``Not permitted.`` 要切回无权限页**：管理员检查与服务端列举是两次
        独立判定（中间可能刚好被运维改了授权），只在状态行里写一句会让用户以为
        是「名单为空」。

        Args:
            payload: :meth:`_Jobs.users` 的返回值。
            elapsed: 耗时文本。
        """
        if not payload.get('ok'):
            reply = str(payload.get('reply') or '（空答复）').strip()
            self._list_pending = False
            self._list_loaded = False
            if reply.lower().startswith('not permitted'):
                self._admin = False
                # ⚠️ 只换「服务端答复」那一行：上面那几行信息还是判定时取到的
                #    真实值，没必要清掉（清掉等于把用户已经看到的信息收走）。
                self.denied_detail.setText(self.DENIED_SUBTITLE)
                self.denied_reply.setText('服务端答复：%s' % reply)
                self._stack.setCurrentIndex(self.PAGE_DENIED)
                self._update_buttons()
                return
            self.list_status.setText('名单不可用')
            self._status('没能取到用户名单：%s' % reply)
            self._update_buttons()
            return

        self._entries = list(payload.get('entries') or [])
        self._list_pending = False
        self._list_loaded = True
        self._populate()

        notes = []
        if payload.get('dropped'):
            notes.append('丢弃 %d 条' % payload['dropped'])
        if payload.get('truncated'):
            notes.append('名单被截断')
        if payload.get('limited'):
            notes.append('其中 %d 个用户未取到姓名/单位（服务端读取上限）'
                         % payload['limited'])
        self.list_status.setText('共 %d 个用户' % len(self._entries))
        tail = ' '.join(part for part in ('；'.join(notes), elapsed) if part)
        self._status('名单已更新：%d 个用户。%s' % (len(self._entries), tail))
        self._update_buttons()

    def _populate(self):
        """按筛选词重建左侧列表（**纯本地操作**）.

        ⚠️ 填充期间 ``blockSignals(True)``：``currentItemChanged`` 在程序填充时
        也会发，不挡住就会出现「打开页面自动去读第一个用户的授权」。

        ⚠️ 邮箱**单独存进 UserRole**：条目文字可能是「姓名\\n邮箱」，拿 ``text()``
        去查是错的。
        """
        keyword = self.filter_edit.text().strip().lower()
        current = self._current_email

        # ⚠️ 折行宽度按**固定的面板宽度**算，不用 viewport().width()：列表还没
        #    显示时 viewport 宽度是个很小的默认值，按它折会把邮箱切成一条条碎片；
        #    而面板宽度是固定的（LIST_WIDTH），随时算都对。
        width = max(60, self.LIST_WIDTH - 2 * self.GAP - 12)

        self.user_list.blockSignals(True)
        try:
            self.user_list.clear()
            shown = 0
            for name, email, _org in self._entries:
                if keyword and keyword not in name.lower() \
                        and keyword not in email.lower():
                    continue
                # 有些用户的「姓名」填的就是邮箱（注册时图省事），两行会变成同一串
                # 重复 —— 那种情况按「没有姓名」处理，只显示一行。
                shown_name = name if name and name.lower() != email.lower() \
                    else ''
                email_text = wrap_text_to_width(email, width,
                                                self.user_list.font())
                text = '%s\n%s' % (shown_name, email_text) if shown_name \
                    else email_text
                item = QtWidgets.QListWidgetItem(text)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, email)
                item.setToolTip('%s\n%s' % (name, email) if name else email)
                self.user_list.addItem(item)
                shown += 1
                if current and email.lower() == current.lower():
                    self.user_list.setCurrentItem(item)
        finally:
            self.user_list.blockSignals(False)

        total = len(self._entries)
        self.list_title.setText('用户（%d）' % total if not keyword
                                else '用户（%d / %d）' % (shown, total))

    def _on_current_changed(self, current, _previous):
        """用户换了选中项：去读它的授权.

        Args:
            current: 新的当前条目（可能为 ``None``）。
            _previous: 旧的当前条目（未使用）。
        """
        if current is None:
            return
        email = current.data(QtCore.Qt.ItemDataRole.UserRole) or ''
        if email:
            self._select_email(str(email))

    # ------------------------------------------------------------------
    # 单个用户的授权
    # ------------------------------------------------------------------

    def _select_email(self, email):
        """选中一个用户并读它的授权（后台线程）.

        ⚠️ **允许在请求在飞时切换目标**：连点几个用户是很自然的动作，如果每次
        都因为「上一个还没回来」而被忽略，用户会以为界面卡了。旧的那次结果回来
        时会被代次丢掉（见 :meth:`_on_done`），线程本身不杀（QThread 不能安全
        强杀）。

        Args:
            email: 要读的用户邮箱；空串直接返回。
        """
        email = str(email or '').strip()
        if not email or not self._admin:
            return

        self._current_email = email
        entry = next((item for item in self._entries
                      if item[1].lower() == email.lower()), ('', email, ''))
        self.email_label.setText(email)
        self.name_label.setText('姓名：%s' % (entry[0] or '（未填写）'))
        self.org_label.setText('单位：%s' % (entry[2] or '（未填写）'))

        # 旧值先清空：宁可显示「还没读到」，也不要把上一个用户的数字留在这里
        # （那会让人以为已经读到了，然后照着错的值去改）。
        self._origin = {'date': '', 'features': []}
        self.date_edit.clear()
        self.features_edit.clear()
        self._status('正在读取 %s 的授权……' % email)
        self._begin('license', lambda: _Jobs.license_of(email))

    def _apply_license(self, payload, elapsed):
        """读到的授权填进编辑框，并把原始值记下来（判「改了什么」用）.

        Args:
            payload: :meth:`_Jobs.license_of` 的返回值。
            elapsed: 耗时文本。
        """
        if not payload.get('ok'):
            self._origin = {'date': '', 'features': []}
            self.date_edit.clear()
            self.features_edit.clear()
            self._status('读取失败：%s' % (payload.get('error')
                                          or '（未知原因）'))
            return

        date_value = str(payload.get('date') or '')
        features = list(payload.get('features') or [])
        self._origin = {'date': date_value, 'features': list(features)}
        self.date_edit.setText(date_value)
        self.features_edit.setPlainText(_Protocol.format_features(features))

        note = ''
        if date_value == _Protocol.DATE_DEFAULT:
            note = '（服务端没有为这份许可设置到期日，0001-01-01 = 已过期）'
        elif not date_value:
            note = '（服务端答复里没有到期日）'
        self._status('已读取：到期日 %s%s，功能 %d 项。%s'
                     % (date_value or '（空）', note, len(features), elapsed))

    def _save(self):
        """校验并提交改动（只有**真的改了**的字段才会发出去）.

        ★ 只发改动过的字段：服务端把「没给」当「不改」，而多发一个没变的字段
        会让审计日志里多出一条「他改了这个字段」—— 那是假的。
        """
        email = self._current_email
        if not email:
            return

        date_value, error = _Protocol.parse_date_text(self.date_edit.text())
        if error:
            self._status(error)
            return
        features, error = _Protocol.parse_features_text(
            self.features_edit.toPlainText())
        if error:
            self._status(error)
            return

        changed_date = None
        if date_value and date_value != self._origin['date']:
            changed_date = date_value
        changed_features = None
        if features != self._origin['features']:
            changed_features = features

        if changed_date is None and changed_features is None:
            if not date_value and self._origin['date']:
                # 「留空」在本接口里是**不修改**，不是「清空到期日」—— 想停用这份
                # 授权只能填一个过去的日期。不说清楚会被误以为已经清掉了。
                self._status('到期日留空 = 不修改。若要停用这份授权，'
                             '请填入今天之前的日期。')
            else:
                self._status('内容没有变化，未提交。')
            return

        parts = []
        if changed_date is not None:
            parts.append('到期日')
        if changed_features is not None:
            parts.append('功能清单')
        self._status('正在提交（%s）……' % '、'.join(parts))
        self._begin('update', lambda: _Jobs.update(email, changed_date,
                                                   changed_features))

    def _apply_update(self, payload, elapsed):
        """提交结果：成功就**重新读一遍**，让界面显示服务端的权威值.

        ⚠️ 成功答复只有 ``Updated`` 一个词，**不含新值** —— 想确认「真的写成了
        这样」只能再读一次。这也顺手覆盖了「服务端做了规范化」的情形（例如把
        ``features`` 原样存下、不排序）。

        Args:
            payload: :meth:`_Jobs.update` 的返回值。
            elapsed: 耗时文本。
        """
        if not payload.get('ok'):
            self._status('更新失败：%s' % (payload.get('reply') or '（空答复）'))
            self._update_buttons()
            return
        self._status('已更新%s。正在重新读取……'
                     % ('（%s）' % elapsed if elapsed else ''))
        self._begin('license', lambda: _Jobs.license_of(self._current_email))

    # ------------------------------------------------------------------
    # 状态、启用状态与生命周期
    # ------------------------------------------------------------------

    def _status(self, text):
        """在右下角显示一句话（服务端原话优先，不加工）。

        Args:
            text: 要显示的文本。
        """
        self.status_label.setText(str(text if text is not None else ''))

    def _update_buttons(self):
        """按「是否管理员 / 是否选中用户 / 是否有请求在飞」统一刷新可用状态.

        ★ 输入框也跟着置灰：读取期间可编辑的话，读回来的值会盖掉用户刚敲的字。
        """
        has_user = bool(self._current_email)
        idle = not self._busy
        editable = bool(self._admin) and has_user and idle

        self.filter_edit.setEnabled(bool(self._entries) and idle)
        self.user_list.setEnabled(idle or has_user)
        self.refresh_button.setEnabled(bool(self._admin) and idle)
        self.retry_button.setEnabled(not self._busy)
        self.save_button.setEnabled(editable)
        self.reload_button.setEnabled(editable)
        self.date_edit.setEnabled(editable)
        self.features_edit.setEnabled(editable)

    def showEvent(self, event):
        """第一次显示时去验管理员权限（**只验一次**）.

        ⚠️ 不在 ``__init__`` 里做：控件构造不该联网（``TabWidget`` 可能在
        恢复标签页时先把控件建出来，那时用户还没看到它）。``showEvent`` 会在每次
        切到本页时发，所以用一个标志挡住重复检查。

        Args:
            event: Qt 的显示事件。
        """
        super(UserAdminView, self).showEvent(event)
        if self._admin_checked or self._busy:
            return
        self._check_admin()

    def refresh(self):
        """GUI 刷新钩子（切到本页 / 菜单「显示 → 刷新」）.

        ⚠️ **必须快**：只补一次「名单还没取到」的初始加载，绝不重放上一次查询。
        名单要服务端逐用户读许可（可能好几秒），在这里无条件重拉的话，每切一次
        标签就打一次服务端。
        """
        if not self._admin or self._busy or self._list_loaded:
            return
        self._load_users()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用：**放掉线程引用、不等**（``TabWidget.close_tab``）.

        ⚠️ **刻意不 ``wait()``**：请求最长 60 秒，在这里同步等就是把「关标签」
        变成冻结界面。线程没有 parent（见模块文档的防线 1），所以不会随控件一起
        被销毁 —— 关标签只是让结果失去接收者，迟到结果由 :meth:`_on_done` 开头的
        ``_Jobs.is_deleted`` 与代次挡掉。

        ⚠️ ``closeEvent`` 在这条路径上**不会**被调用（``deleteLater()`` 不发它），
        两者缺一不可，见 :meth:`closeEvent`。
        """
        self._generation += 1
        self._worker = None
        self._busy = False
        self._list_pending = False

    def closeEvent(self, event):
        """控件被**单独** ``close()`` 时（例如直接跑 ``test_1``）等一会儿线程.

        ⚠️ 只等 3 秒：长请求可达 60 秒，等下去就是冻结；线程本身能活到自然结束
        （没有 parent），所以这里只是给「短请求」一个干净退出的机会。

        Args:
            event: Qt 的关闭事件。
        """
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.wait(3000)
        event.accept()


def show_user_admin():
    """打开「用户管理」页（管理员专用，只开一个标签页）.

    ⚠️ 走 ``gui.get_widget`` 而不是直接 ``UserAdminView()``：重复调用只是把已有
    页面切到前面，不会开第二个。

    ⚠️ ``oper`` 每次调用都会执行，所以里面只放 ``gui_restore``（重启后按这段代码
    恢复标签页）；真正的联网检查挂在控件的 ``showEvent`` 上。
    """
    def oper(widget):
        widget.gui_restore = 'gui.show_user_admin()'

    gui.get_widget(
        UserAdminView,
        caption='用户管理',
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='按用户查看并修改授权的到期日与功能清单（仅管理员）',
    )


def setup_ui():
    """注册 GUI 命令与菜单项「**帮助 → 用户 → 管理**」.

    ⚠️ 菜单文字是「管理」不是「用户管理」：它已经在「用户」子菜单里，
    再叫「用户管理」就成了「用户 → 用户管理」这种重复（2026-10-19 之前是顶层
    「用户 → 管理」，如今「用户」并到了「帮助」下面，文字保持不变）。

    ⚠️ **本函数不会自动执行**：要挂上菜单，需由
    ``zmlx/ui/extra_setups/__init__.py`` 调用（那里经
    ``extra_setups/user_admin.py`` 统一登记）::

        from zmlx.ui.tabs.user_admin_view import setup_ui
        setup_ui()
    """
    gui.add_func('show_user_admin', show_user_admin)

    def not_running():
        return not gui.is_running()

    gui.add_action(
        menu=['帮助', '用户'],
        name='user_admin_view',
        text='管理',
        icon='info',
        tooltip='按用户查看并修改授权的到期日与功能清单（仅管理员）',
        slot=show_user_admin,
        is_enabled=not_running,
        overwritable=False,
    )


def test_1():
    """交互式查看本控件（**会真的联网**，需要管理员权限）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = UserAdminView()
    w.resize(940, 640)
    w.show()
    sys.exit(app.exec())


def test_2():
    """离线自检：解析 / 校验 / 界面填充（**不联网**）."""
    import os
    import sys

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QtWidgets.QApplication(sys.argv)

    # ---- 1. user_list_detail 的解析 ----
    detail = ('UsersDetail: 3 | NamesLimited: 1 | '
              'List: a@x.com; b@y.org; c@z.net | '
              'Names: 张; (none); 李四 | Orgs: 中科院; (none); 某公司')
    data = _Protocol.parse_detail(detail)
    assert data is not None
    assert data['entries'] == [('张', 'a@x.com', '中科院'),
                               ('', 'b@y.org', ''),
                               ('李四', 'c@z.net', '某公司')], data
    assert data['limited'] == 1 and not data['truncated']
    # 老动作 / 失败答复都必须拿不到东西
    assert _Protocol.parse_detail('Users: 2 | List: a@x.com; b@y.org') is None
    assert _Protocol.parse_detail('Not permitted.') is None
    # 坏条目被丢掉时，姓名与单位**不能**整体错位
    data = _Protocol.parse_detail(
        'UsersDetail: 2 | List: good@x.com; bad | '
        'Names: 甲; 乙 | Orgs: 单位甲; 单位乙')
    assert data['entries'] == [('甲', 'good@x.com', '单位甲')], data

    # ---- 2. get_user_info 的答复 ----
    assert _Protocol.field_value('UserInfo: 2027-04-01') == ('2027-04-01',
                                                             None)
    assert _Protocol.field_value('UserInfo: ')[0] == ''      # 成功但值为空
    assert _Protocol.field_value('Not permitted.')[0] is None
    assert _Protocol.parse_features('["*"]') == ['*']
    assert _Protocol.parse_features('[]') == []
    assert _Protocol.parse_features('a, b') is None
    assert _Protocol.is_updated('Updated')
    assert not _Protocol.is_updated('Not permitted.')

    # check 答复的首词 / Features 段（无权限页要用）
    assert _Protocol.verdict_of('Yes | Source: u_1 | Email: a@b.c') == '有效'
    assert _Protocol.verdict_of('No | Expires: 2020-01-01') == '未通过'
    assert _Protocol.verdict_of('dll not found') == '—'
    assert _Protocol.features_of('Yes | Features: * | User: 张') == '*'
    assert _Protocol.features_of('Yes | Features: a, b') == 'a, b'
    assert _Protocol.features_of('No') == ''

    # ---- 3. 本地校验（与服务端规则同构，只用于即时提示） ----
    assert _Protocol.parse_date_text('') == ('', None)
    assert _Protocol.parse_date_text(' 2027-04-01 ')[0] == '2027-04-01'
    assert _Protocol.parse_date_text('20270401')[0] is None
    assert _Protocol.parse_date_text('2026-02-30')[0] is None
    assert _Protocol.parse_date_text('0001-01-01')[0] == '0001-01-01'
    assert _Protocol.parse_features_text('flow\nthermal\n')[0] == ['flow',
                                                                  'thermal']
    assert _Protocol.parse_features_text('flow\nflow')[0] == ['flow']
    assert _Protocol.parse_features_text('')[0] == []        # 清空是合法意图
    assert _Protocol.parse_features_text('*')[0] == ['*']
    assert _Protocol.parse_features_text('1a')[0] is None
    assert _Protocol.parse_features_text('a, b')[0] is None

    # ---- 4. 界面：管理员 + 名单 + 一个用户的授权（全部直接调内部方法） ----
    w = UserAdminView()
    w._admin = True
    w._stack.setCurrentIndex(w.PAGE_MAIN)
    w._apply_users({'ok': True, 'entries': [('张', 'a@x.com', '中科院'),
                                            ('', 'b@y.org', '')],
                    'dropped': 0, 'truncated': False, 'limited': 0}, '')
    assert w.user_list.count() == 2, w.user_list.count()
    assert w.list_title.text() == '用户（2）', w.list_title.text()
    # 筛选
    w.filter_edit.setText('b@')
    assert w.user_list.count() == 1
    w.filter_edit.setText('')
    assert w.user_list.count() == 2

    # 选中（**不**走 _select_email：那会起联网线程）
    w._current_email = 'a@x.com'
    w.email_label.setText('a@x.com')
    w._apply_license({'ok': True, 'date': '2027-04-01',
                      'features': ['flow', 'thermal']}, '')
    assert w.date_edit.text() == '2027-04-01'
    assert w.features_edit.toPlainText() == 'flow\nthermal'
    w._update_buttons()
    assert w.save_button.isEnabled()

    # 没改动时点保存：只提示、不发请求
    w._worker = None
    w._save()
    assert w._worker is None, '没有改动却发起了请求'
    assert '没有变化' in w.status_label.text()

    # 日期写歪：只提示、不发请求
    w.date_edit.setText('2026-13-01')
    w._save()
    assert w._worker is None, '日期非法却发起了请求'
    assert '真实存在的日期' in w.status_label.text()

    # 功能名非法：只提示、不发请求
    w.date_edit.setText('2027-04-01')
    w.features_edit.setPlainText('flow\n1bad')
    w._save()
    assert w._worker is None, '功能名非法却发起了请求'
    assert '不是合法功能名' in w.status_label.text()

    # 非管理员页：只显示「没有管理员权限」+ 自己的授权信息 + 出路
    w2 = UserAdminView()
    w2._apply_admin({'admin': False,
                     'reply': 'No | Source: u_x | Features: flow, thermal | '
                              'User: 张三 | Org: 某单位 | '
                              'Email: zhang@x.com',
                     'verdict': '未通过', 'date': '2026-12-31',
                     'info': {'email': 'zhang@x.com', 'user': '张三',
                              'org': '某单位'}}, '')
    assert w2._stack.currentIndex() == w2.PAGE_DENIED
    assert w2._stack.currentWidget().findChildren(QtWidgets.QListWidget) == []
    texts = [label.text() for label in
             w2._stack.currentWidget().findChildren(QtWidgets.QLabel)]
    assert any('没有管理员权限' in text for text in texts), texts
    assert w2.denied_values['email'].text() == 'zhang@x.com'
    assert w2.denied_values['user'].text() == '张三'
    assert w2.denied_values['org'].text() == '某单位'
    assert w2.denied_values['date'].text() == '2026-12-31'
    assert w2.denied_values['features'].text() == 'flow, thermal'
    assert w2.denied_values['verdict'].text() == '未通过'
    assert '提交反馈' in w2.denied_hint.text()
    assert 'Not permitted' not in w2.denied_reply.text()   # 这里是判定答复原文
    assert 'No |' in w2.denied_reply.text()

    # 未绑定时：字段一律「—」，出路换成「先去登录」
    w3 = UserAdminView()
    w3._apply_admin({'admin': False, 'reply': 'Please register with your '
                                             'email first.',
                     'verdict': '—', 'info': {}}, '')
    assert w3.denied_values['email'].text() == '未登录 / 未绑定邮箱'
    assert w3.denied_values['date'].text() == '—'
    assert '登录' in w3.denied_hint.text()

    w.cleanup_before_tab_close()
    w2.cleanup_before_tab_close()
    w3.cleanup_before_tab_close()
    w.deleteLater()
    w2.deleteLater()
    w3.deleteLater()
    print('test_2 passed (offline).')


if __name__ == '__main__':
    test_1()

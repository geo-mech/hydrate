# ** name = '用户管理'
# ** desc = '「帮助 → 用户」下的三个页面：管理 / 登录记录 / 反馈记录'
# ** enabled = True
"""「帮助 → 用户」子菜单的全部内容：管理 + 登录记录 + 反馈记录.

**本文件自含**：「帮助 → 用户」下的三个页面 —— 菜单项、命令、**控件本体**全在这里。
``zmlx/ui/tabs/`` 与 ``zmlx/ui/widget/`` 里**没有任何残留、也没有任何垫片**。

=======================  ==================================  =========================================
菜单                      命令                                控件
=======================  ==================================  =========================================
帮助 → 用户 → 管理          ``gui.show_user_admin``             :class:`UserAdminView`
帮助 → 用户 → 登录记录      ``gui.show_check_count_view``       :class:`CheckCountView`
帮助 → 用户 → 反馈记录      ``gui.show_feedbacks_view``         :class:`FeedbacksView`
=======================  ==================================  =========================================

⚠️ **读代码时先认清自己在哪一段**（本文件有几段互不相干的控件，名字像但各管各的）：

============================  ===========================================================
段                             内容
============================  ===========================================================
``_Protocol`` / ``_Jobs`` /    管理页：服务端答复解析、线程登记、:class:`UserAdminView`
``_Worker`` / ``UserAdminView``
（本文件最前面）               ``_Worker`` 是「按代次丢弃过期结果」的版本
----                          -----------------------------------------------------------
``CheckCountView`` 那一段     登录记录页：``_BarChart``（原生 Qt 柱状图）、
                              ``_Worker`` / ``_PrefillWorker`` / ``_UserListWorker``、
                              ``parse_count_reply`` 等解析函数、``_RUNNING_WORKERS`` 表
                              ⚠️ 这里的 ``_Worker`` 名字与上面那个**重名但不同**：
                              带 ``sig_done(str, str)``，一次查一个邮箱
----                          -----------------------------------------------------------
``FeedbacksView`` 那一段     反馈记录页：``_Marks`` / ``_Parsers`` / ``_Layout``、
                              ``_ListWorker`` / ``_ReadWorker`` / ``_PrefillWorker`` /
                              ``_UserListWorker``、另一张 ``_RUNNING_WORKERS`` 表
============================  ===========================================================

⚠️ **重名的私有成员不要合并**：两处 ``_Worker``、两处 ``_PrefillWorker``、
两处 ``_UserListWorker``、两张 ``_RUNNING_WORKERS`` 表 —— 每一份都只在自己的类里被
引用，参数表与信号签名都不同。合进一个模块是**为了入口与控件住在一起**，不是让它们
互相改写。

四次合并（都**不留垫片**）
--------------------------

1. **2026-10-31 上午**：`zmlx/ui/tabs/user_admin_view.py` 整体并入本文件（原模块删除、
   **不留垫片**：全仓与外部工作区都没有别处 import 它，唯一引用就是本插件的装配；
   打开入口走的是命令 ``gui.show_user_admin()``，与控件路径无关）。此前
   ``setups/user_admin.py`` 只是个「转发一行 setup_ui」的装配壳，控件本体住
   ``ui/tabs/``。
2. **2026-10-31 稍后**：``zmlx/ui/setups/license_query.py`` 整体并入本文件
   （原模块删除、**不留垫片**）。那个模块里只有两个 ``show_xxx`` 函数与 ``setup_ui``，
   全都只服务「帮助 → 用户」这一个子菜单 —— 既然子菜单已经整块归本插件，
   装配代码也应当住在一起。
3. **2026-10-31 再稍后**：``zmlx/ui/tabs/check_count_view.py`` 整体并入本文件
   （原模块删除、**不留垫片**；``tabs/__init__.py`` 的转发与 ``widget/`` 下
   ``check_count_view.py`` / 更早的 ``license_count.py`` 两个垫片一并删掉）。
4. **2026-10-31 最后**：``zmlx/ui/tabs/feedbacks_view.py`` 与其离线自测
   ``zmlx/ui/tabs/_test_feedbacks_view.py`` 整体并入本文件（原模块删除、**不留垫片**；
   ``tabs/__init__.py`` 的转发与 ``widget/`` 下 ``feedbacks_view.py`` /
   更早的 ``license_feedback.py`` 两个垫片一并删掉）。那个离线自测成了本文件的
   :func:`test_4`。

⚠️ 至此 `ui/tabs/` 与 `ui/widget/` 里**再也找不到**这三个控件的任何痕迹 —— 老路径
``from zmlx.ui.tabs import CheckCountView`` / ``from zmlx.ui.widget import FeedbacksView``
等都会直接失败（**这是有意的**，用户明确要求不留垫片）。新代码请用
``from zmlx.ui.plugins.builtin.user_admin import UserAdminView, CheckCountView, FeedbacksView``，
或直接调 ``gui.show_user_admin()`` / ``gui.show_check_count_view()`` / ``gui.show_feedbacks_view()``。

为什么是插件（``plugins/``）而不是 ``setups/``
--------------------------------------------------

⚠️ **这是一次判据变更，值得写清楚**（2026-10-31，用户要求）：2026-10-18 时它一度是
插件，当晚以「用户管理是产品功能，不该让用户关掉」为由搬回 ``setups/``。
现在的判断是：**关掉它，软件照样能建模、求解、绘图** —— 少的只是「帮助 → 用户」下
这几个管理 / 查询入口，属于**可关闭的扩展**。按 ``setups/AGENTS.md`` §1 的判据
（可检验的那一条），它归插件，**默认加载**（``# ** enabled = True``），绝大多数用户
不必知道它的存在，管理员也照旧点得到。

⚠️ 两张记录页随之搬进插件，是同一个判据的直接结果：它们是**管理 / 运维用的查询页**，
不是「不登录就登录不了」的必经环节。真正属于产品功能、关不掉的是**登录与授权检查**
本身 —— 那在 ``MainWindow`` / ``zmlx/ui/tabs/license_register.py`` / ``widgets/
license_button.py`` 里，与本文件无关。

⚠️ **命令名与菜单项键一律未改**（``show_user_admin`` / ``show_check_count_view`` /
``show_feedbacks_view``，``name='user_admin_view'`` / ``'check_count_view'`` /
``'feedbacks_view'``）：历史标签页（``gui_restore`` 存的就是这些 ``gui.show_xxx()`` 原文）
照常恢复；两个更早的旧名（``show_license_count`` / ``show_license_feedback``）
也仍作为别名注册，见 :func:`setup_ui`。

⚠️ 菜单文字是「**管理**」而不是「用户管理」：它已经在「用户」子菜单里，
再叫「用户管理」就成了「用户 → 用户管理」这种重复。2026-10-19 那个顶层「用户」
菜单并回了「帮助」，于是这里是「帮助 → 用户 → 管理」。

⚠️ **普通用户也会看到「管理」这一项**：:class:`UserAdminView` 开页后先验证管理员身份，
非管理员只看到「没有管理员权限」+ 自己的授权信息与一条出路。菜单项不分级 ——
判定发生在打开页面之后，这样用户至少知道「这里有这个入口，但我不够格」，
而不是菜单项凭空消失。

下面是控件本体的说明（原 ``tabs/user_admin_view.py`` 的模块文档，随控件一并搬来）
-----------------------------------------------------------------------------

管理员专用的「用户管理」页（``UserAdminView``）：左侧用户名单，右侧该用户的授权.

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

界面接线
--------

本文件提供 :func:`show_user_admin`（打开标签页）与 :func:`setup_ui`（注册 GUI
命令 + 菜单项），由 ``@execute_once`` 与末尾的 ``if __name__ == '__zml_plugin__':``
调起。在挂上之前，也可以用控制台直接打开::

    from zmlx.ui.plugins.builtin.user_admin import show_user_admin
    show_user_admin()

Created by 小助手 (DeepSeek), 2026-10-18
Modified by DeepSeek, 2026-10-18: 装配由 ``plugins/user_admin.py`` 移回 ``setups/``
Modified by DeepSeek, 2026-10-18: 菜单由「帮助 → 查询 → 用户管理」改为「用户 → 管理」
Modified by DeepSeek, 2026-10-19: 「用户」整体并回「帮助」，菜单为「帮助 → 用户 → 管理」
Modified by DeepSeek, 2026-10-31: ``tabs/user_admin_view.py`` 的内容整体并入本文件，
    原模块删除、**不留垫片**；随后本文件由 ``setups/user_admin.py`` 搬到
    ``plugins/builtin/user_admin.py``（改为可关闭的插件、默认加载）。
    命令名 ``gui.show_user_admin``、action ``name='user_admin_view'``、控件公开接口
    （``show_user_admin`` / ``UserAdminView``）均未变。
Modified by DeepSeek, 2026-10-31: ``setups/license_query.py`` 的内容（登录记录 /
    反馈记录两条命令 + 菜单项 + 两个旧名别名）整体并入本文件，原模块删除、**不留垫片**。
    ``show_check_count_view`` / ``show_feedbacks_view`` / ``show_license_count`` /
    ``show_license_feedback`` 四条命令与两个 action name 均未变。
Modified by DeepSeek, 2026-10-31: ``tabs/check_count_view.py``（``CheckCountView`` 控件 +
    ``_BarChart`` / ``_Worker`` / ``_PrefillWorker`` / ``_UserListWorker`` + 解析函数）整体
    并入本文件，原模块删除、**不留垫片**；``tabs/__init__.py`` 的转发与 ``widget/`` 下
    ``check_count_view.py`` / ``license_count.py`` 两个兼容垫片一并删除。
    控件类名 ``CheckCountView``、常量与公开函数（``parse_count_reply`` 等）未变。
Modified by DeepSeek, 2026-10-31: ``tabs/feedbacks_view.py``（``FeedbacksView`` 控件 +
    ``_Marks`` / ``_Parsers`` / ``_Layout`` + 四个后台线程）与其离线自测
    ``tabs/_test_feedbacks_view.py`` 整体并入本文件，原模块删除、**不留垫片**；
    ``tabs/__init__.py`` 的转发与 ``widget/`` 下 ``feedbacks_view.py`` /
    ``license_feedback.py`` 两个兼容垫片一并删除。离线自测成为本文件的 ``test_4()``。
    控件类名 ``FeedbacksView``、``_Parsers`` 与公开方法均未变。
"""

import datetime
import json
import re
import time

from zmlx.exts import web_license
from zmlx.system import execute_once, make_parent
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.utils.lic_utils import (ADMIN_EMAIL, DETAIL_SEP, bound_info,
                                     detail_of, find_field, format_elapsed,
                                     is_admin_by_web_license, is_user_list,
                                     is_user_list_detail, looks_like_email,
                                     merge_emails, parse_user_list,
                                     parse_user_list_detail,
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
    DENIED_HINT_UNBOUND = ('本机还没有绑定邮箱，或授权已失效。请先通过「帮助 → 登录」'
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
        """打开「帮助 → 反馈」那一页（**不自己造一个反馈入口**）.

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
        """GUI 刷新钩子（切到本页 / 菜单「操作 → 刷新」）.

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


class _CountWorker(QtCore.QThread):
    """在后台线程里查一次「查询次数统计」（**绝不碰界面**）。

    与 ``license_register._CountWorker`` 同构：线程里只发请求，结果用信号发回主线程。

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
        super(_CountWorker, self).__init__(parent)
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
        # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见 _CountWorker
        #    那一处的说明（关标签时控件会被销毁，parent 设成控件会连着线程一起删）。
        worker = _CountUserListWorker()
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

        ⚠️ **两个请求都在后台线程**（``_CountPrefillWorker`` 取本机绑定邮箱、
        ``_CountUserListWorker`` 取服务端名单），主线程**从不等待**它们 —— 这正是
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
            # ⚠️ 线程的 parent 一律留空、登记到模块级 _RUNNING_WORKERS：见 _CountWorker
            #    那一处的说明（关标签时控件会被销毁，parent 设成控件会连着线程一起删）。
            #    ⚠️ 第一个参数是**取值用的 owner 引用**，不是 Qt parent —— 不要写
            #    _CountPrefillWorker(self, self)。
            worker = _CountPrefillWorker(self)
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
        """发起一次查询（**不等结果**，请求在后台线程 :class:`_CountWorker` 里跑）。

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
        worker = _CountWorker(email, from_date, to_date, parent=None)
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


class _CountPrefillWorker(QtCore.QThread):
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
        super(_CountPrefillWorker, self).__init__(parent)
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


class _CountUserListWorker(QtCore.QThread):
    """在后台线程里取「服务端用户名单」（**绝不碰界面**）。

    ⚠️⚠️ **必须在后台线程**：``user_list`` **不做缓存、每次调用都真的发出去**，
    单次最长阻塞 30 秒。放进 UI 线程的话，
    「点开授权记录」会直接卡住 —— 而本控件的要求正是**立即显示**。

    ⚠️ **非管理员拿到的是 ``Not permitted.``**（HTTP 200 的**正常业务答复**），
    所以这里**不发错误信号**：结果一律通过 :attr:`sig_done` 交回文本，
    由主线程用 :func:`parse_user_list` 判定；判不出就静默忽略。

    ⚠️ 与 :class:`_CountPrefillWorker` 分开成两个线程，是因为两者**失败互不影响**：
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
        super(_CountUserListWorker, self).__init__(parent)
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


def test_count_1():
    """交互式查看本控件（会真的联网查询）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = CheckCountView()
    w.resize(900, 640)
    w.show()
    sys.exit(app.exec())


def test_count_2():
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


# ======================================================================
# 帮助 → 用户 → 反馈记录：FeedbacksView 控件本体
#
# ⚠️ 2026-10-31 由 ``zmlx/ui/tabs/feedbacks_view.py`` **整体并入本文件**
# （原模块删除、**不留垫片**）。控件类名、常量与公开方法一字未改。
# 本段自带 ``_Marks`` / ``_Parsers`` / ``_Layout`` 三个私有类、四个后台线程
# （``_FbListWorker`` / ``_FbReadWorker`` / ``_FbPrefillWorker`` / ``_FbUserListWorker``）
# 与一张模块级的 ``_RUNNING_WORKERS`` 表 —— 与本文件前面那两段**互不相干**，
# 不要合并（名字虽像，语义与信号签名都不同）。
# ======================================================================


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
    #: ⚠️ 与 ``plugins/builtin/user_admin.py`` 取同一个值：两个页面并排看时左侧栏**对齐**，
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
#: 挂在这里线程一定能跑完；控件销毁后迟到结果由 :func:`_FbIsDeleted` 拦掉。
#: （与 ``plugins/builtin/user_admin.py`` / ``demo_view.py`` 是同一条纪律。）
_RUNNING_WORKERS = []


def _FbForgetWorker(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）."""
    try:
        _RUNNING_WORKERS.remove(worker)
    except ValueError:
        pass


def _FbIsDeleted(obj):
    """判断一个 Qt 对象的底层 C/C++ 对象是否已经被销毁.

    ⚠️ **为什么需要它**：本控件的结果槽是**用 lambda 连的**
    （``connect(lambda ...: self._on_list_reply(...))``）。Qt 只能对「接收者是
    QObject 的**绑定方法**」做自动断连 —— lambda 没有接收者对象，控件被
    ``deleteLater()`` 销毁后**连接依然有效**，线程回来时那个 lambda 照样被调用，
    于是在一个已经死掉的控件上碰子控件，抛::

        RuntimeError: wrapped C/C++ object of type QPlainTextEdit has been deleted

    ⚠️ 与 ``plugins/builtin/user_admin.py`` 里那个**同名同实现**（照抄而非 import：两个控件
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
    :func:`_FbIsDeleted`）：去首尾空白、丢掉不像邮箱的、按 ``lower()`` 去重、
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


class _FbListWorker(QtCore.QThread):
    """在后台线程里列一次某天的反馈文件名（**绝不碰界面**）.

    与 ``CheckCountView._CountWorker`` 同构：线程里只发请求，结果用信号发回主线程。

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
        super(_FbListWorker, self).__init__(parent)
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


class _FbReadWorker(QtCore.QThread):
    """在后台线程里取一条反馈的内容（**绝不碰界面**）.

    与 :class:`_FbListWorker` 同构，只是换成 ``get_feedback``。

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
        super(_FbReadWorker, self).__init__(parent)
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


class _FbPrefillWorker(QtCore.QThread):
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
        super(_FbPrefillWorker, self).__init__(parent)
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


class _FbUserListWorker(QtCore.QThread):
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
        super(_FbUserListWorker, self).__init__(parent)
        self.setObjectName('FeedbacksViewUserListWorker')

    def run(self):
        """线程体：取名单并发回主线程。"""
        try:
            from zmlx.ui.utils.lic_utils import is_user_list_detail
            # ★ v3.35：优先要「邮箱 + 姓名」；拿不到再退回旧动作（理由见
            #   ``CheckCountView._FbUserListWorker.run``：老服务端会把未知 action
            #   当成一次许可查询）。
            reply = web_license.user_list_detail()
            if not is_user_list_detail(reply):
                # ⚠️ 实测偶发**空答复**（2026-10-18）—— 重试一次再退回旧动作，
                #    理由见 CheckCountView._FbUserListWorker.run 那处注释。
                retry = web_license.user_list_detail()
                reply = retry if is_user_list_detail(retry) else web_license.user_list()
            text = str(reply if reply is not None else '')
        except Exception as err:      # 防御性：user_list 按契约不抛异常
            text = f'{type(err).__name__}: {err}'
        self.sig_done.emit(text)


class FeedbacksView(QtWidgets.QWidget):
    """反馈查看控件：一个日期 + 一个邮箱 → 一批文件名 → 一条反馈的内容。

    ★ 与「授权记录」（``plugins/builtin/user_admin.CheckCountView``）是**同构的兄弟**：同一套
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
        #: ``plugins/builtin/user_admin.py`` 的 ``context_actions`` 是同一套写法）。
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
            #    ``plugins/builtin/user_admin.py`` 的写法，误抄会直接 AttributeError。）
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
        （``plugins/builtin/user_admin.py`` 里真踩过，会偶发卡死）：正文区这里只需要
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

        ⚠️ 与 ``CheckCountView._build_email_list`` 逐字同构：同样的**默认隐藏**、
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
        #    不动」（``plugins/builtin/user_admin.py`` 里真踩过）。
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
        worker = _FbUserListWorker()
        worker.sig_done.connect(self._on_user_list)
        worker.finished.connect(lambda: self._on_user_list_finished(worker))
        worker.finished.connect(lambda w=worker: _FbForgetWorker(w))
        worker.finished.connect(worker.deleteLater)
        self._user_list_worker = worker
        _RUNNING_WORKERS.append(worker)
        worker.start()

    def _on_user_list_finished(self, worker):
        """名单线程结束（主线程调用）：释放引用。

        Args:
            worker: 刚结束的线程。
        """
        if _FbIsDeleted(self):
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
        （``plugins/builtin/user_admin.py`` 里真踩过：UnicodeEncodeError 直接把控件构造打断）。

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

        ⚠️ **三个请求都在后台线程**（``_FbPrefillWorker`` 取本机绑定邮箱、
        ``_FbUserListWorker`` 取服务端名单），主线程**从不等待**它们 —— 这正是
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
            worker = _FbPrefillWorker(self)
            worker.sig_done.connect(self._on_prefill)
            worker.finished.connect(lambda: self._prefill_worker_done(worker))
            worker.finished.connect(lambda w=worker: _FbForgetWorker(w))
            worker.finished.connect(worker.deleteLater)
            self._prefill_worker = worker
            _RUNNING_WORKERS.append(worker)
            worker.start()
            return
        self.start_query()

    def _prefill_worker_done(self, worker):
        """邮箱预取线程结束：释放引用（主线程调用）."""
        if _FbIsDeleted(self):
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
        worker = _FbListWorker(date, email, parent=None)
        worker.sig_done.connect(
            lambda reply, elapsed, g=generation:
                self._on_list_reply(reply, elapsed, generation=g))
        worker.finished.connect(lambda: self._on_list_worker_finished(worker))
        worker.finished.connect(lambda w=worker: _FbForgetWorker(w))
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
        if _FbIsDeleted(self):
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
        if _FbIsDeleted(self):
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
        worker = _FbReadWorker(file_name, email, parent=None)
        worker.sig_done.connect(
            lambda reply, elapsed, g=generation:
                self._on_read_reply(reply, elapsed, generation=g))
        worker.finished.connect(lambda: self._on_read_worker_finished(worker))
        worker.finished.connect(lambda w=worker: _FbForgetWorker(w))
        worker.finished.connect(worker.deleteLater)
        self._read_worker = worker
        _RUNNING_WORKERS.append(worker)
        self._busy = True
        self._update_buttons()
        worker.start()
        return True

    def _on_read_worker_finished(self, worker):
        """读取线程结束（主线程调用）：放开按钮、释放引用。"""
        if _FbIsDeleted(self):
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
        if _FbIsDeleted(self):
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
        跑完，然后被 :func:`_FbForgetWorker` 摘掉。迟到的结果由 :func:`_FbIsDeleted`
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


def test_feedbacks_1():
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


# ======================================================================
# 帮助 → 用户 → 登录记录 / 反馈记录
#
# ⚠️ 2026-10-31 由 ``zmlx/ui/setups/license_query.py`` **整体并入本文件**
# （原模块删除、**不留垫片**）。⚠️ **``CheckCountView`` 也在这里**：2026-10-31 由
# ``zmlx/ui/tabs/check_count_view.py`` 整体并入（原模块删除、**不留垫片**）；
# ``FeedbacksView`` 的控件本体仍留在 ``zmlx/ui/tabs/feedbacks_view.py``。
#
# 历史：2026-10-19 菜单由 ``用户 → 查询 → X`` 改为 ``帮助 → 查询 → X``；
# 2026-10-24 起 ``查询`` 并入 ``用户``，于是 ``帮助 → 用户 → {管理, 登录记录, 反馈记录}``
# —— **只剩一个子菜单**（「查询记录」与「管账号」本来就不是两层概念），
# 最终结构仍是**两级**：三条记录页与管理同深，**没有三级菜单**。
# ``登录`` / ``反馈`` 两项在 ``main.py`` 里注册，不在本文件。
#
# ⚠️ **``gui.show_check_count_view`` / ``gui.show_feedbacks_view`` 这两个名字必须
# 逐字保留**：它们既是控制台里用户会敲的命令，也是标签页的 ``gui_restore``（重启后
# 按这段代码恢复标签页，见 ``main.py`` 的 ``__save_tabs``）。所以这里用
# ``gui.add_func`` **自己把这两个名字注册进 GUI 命令表**。
#
# ⚠️ **只改显示文字，命令名与控件类名一律不动**：菜单项 / 标签页标题由「查询统计」
# 「查询反馈」改为 **「授权记录」「反馈记录」**，``show_check_count_view`` /
# ``CheckCountView`` / ``show_feedbacks_view`` / ``FeedbacksView`` 这些标识符保持
# 原样 —— 它们是 ``gui_restore`` 里存着的历史状态、也是控制台命令。
#
# ⚠️ 改这套名字时（``show_license_count`` → ``show_check_count_view``、
# ``show_license_feedback`` → ``show_feedbacks_view``）**必须同时注册旧名**
# （见 ``setup_ui``）：老标签页的 ``gui_restore`` 里存的是旧名，只改名会让它恢复不了。
#
# ★ **命名规则只有一条：命令名 = ``show_`` + 控件类名的小写化。**
#    一个字都不许改词形（别写成 ``..._viewer``、别截掉 ``_view``）。两个控件名本身
#    则统一为「接口名去掉动词 + ``View``」。
#
# ⚠️ ``gui.add_func`` / ``gui.add_action`` 会被 GuiApi 派发到**主线程**执行。
#
# ⚠️ **``oper`` 每次调用都会执行**（见 ``TabWidget.get_widget``），所以里面只放
# ``gui_restore``；自动查询挂在控件自己的 ``showEvent`` 上。
# ======================================================================


def show_check_count_view():
    """显示「授权记录」控件（某个邮箱对应用的许可查询次数，按天柱状图）。

    数据来自 ``web_license.check_count``。
    查询本身在后台线程里跑（最长 30 秒），且**不做缓存** —— 每次都是真的发出去，
    见本文件中 :class:`CheckCountView` 的说明（2026-10-31 由
    原 ``zmlx.ui.tabs.check_count_view`` 整体并入）。

    ⚠️ 只通过 ``gui.get_widget`` 打开（而不是直接 ``CheckCountView()``）：这样标签页
    只会有**一个**，重复调用只是把已有页面切到前面。

    名字的由来: 原先叫 ``show_license_count``、控件叫 ``LicenseCount``（由
    ``MainWindow`` 的公开方法自动注册而来）。那个名字说的其实是**数据来源**
    （``check_count`` 这个接口），而不是"这个控件是什么"；而 ``check_count`` 查的也
    不是"授权检查"，是**被数出来的那些 check 的次数**。故与控件一起改为
    ``CheckCountView``（与 ``FeedbacksView`` 配成一对：接口名去掉动词 + ``View``）。
    """
    def oper(w):
        w.gui_restore = 'gui.show_check_count_view()'

    gui.get_widget(
        CheckCountView,
        caption='登录记录',
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='某个邮箱对应用的许可查询次数，按天统计（原生 Qt 柱状图）',
    )


def show_feedbacks_view():
    """显示「反馈记录」控件（某个用户某一天的反馈文件名 + 单条内容）。

    数据来自 ``web_license.list_feedbacks`` / ``web_license.get_feedback``
    （**本人或管理员**可用）。两个查询都在后台线程里跑
    （各最长 30 秒），且**不做缓存** —— 每次都是真的发出去，见
    本文件中「帮助 → 用户 → 反馈记录」那一段的说明。

    ⚠️ 与 :func:`show_check_count_view` 逐字同构（两个页面的权限模型与线程纪律完全
    相同）；差别只在显示：那边画柱状图，这边显示**文本**。

    名字的由来: 原先叫 ``show_license_feedback``（由 ``MainWindow`` 的公开方法自动
    注册而来），但它干的只是**看反馈**这一件事, 与 ``license_`` 前缀暗示的"授权查询"
    无关 —— ``web_license.get_feedback`` 只是碰巧挂在 license 服务上。既然这是本轮
    新加的登记（见上面的说明），就一并改成语义清楚的名字。
    """
    def oper(w):
        w.gui_restore = 'gui.show_feedbacks_view()'

    gui.get_widget(
        FeedbacksView,
        caption='反馈记录',
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='某个用户某一天的反馈：列出文件名并查看内容（本人或管理员）',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册「帮助 → 用户」下的三个页面：管理 / 登录记录 / 反馈记录.

    ⚠️ 菜单文字是「管理」不是「用户管理」：它已经在「用户」子菜单里，
    再叫「用户管理」就成了「用户 → 用户管理」这种重复（2026-10-19 之前是顶层
    「用户 → 管理」，如今「用户」并到了「帮助」下面，文字保持不变）。

    ⚠️ **菜单路径必须与 ``main.py`` 里那几处逐字一致**（``'帮助'`` / ``'用户'``），
    否则 ``get_menu`` 会另建一个同名的新菜单，界面上就会出现两个「帮助」。

    ⚠️ 本函数由末尾的 ``if __name__ == '__zml_plugin__':`` 调起（插件机制用
    ``__name__ == '__zml_plugin__'`` 执行本文件）。``@execute_once`` 是双保险：
    「临时加载」与「启动」都跑过一次时也只挂一条。

    ⚠️ **条目顺序**：三项按这里写的先后挂进子菜单 —— 「管理」在前，两条记录页在后
    （先管账号、再查记录）。2026-10-31 之前它们分别由本插件与
    ``setups/license_query.py`` 注册，「管理」因此一度排在子菜单末尾；
    合并进本文件后顺序恢复成下面的样子。
    """
    # ---- 命令 ----
    gui.add_func('show_user_admin', show_user_admin)

    # ⚠️ 这两个命令原先由 ``MainWindow.__init_gui_api`` 自动注册，方法搬走后那条链
    #   就断了 —— 必须在这里显式补上，否则调用方会报 ``gui function <xxx> not found``。
    gui.add_func('show_check_count_view', show_check_count_view)
    gui.add_func('show_feedbacks_view', show_feedbacks_view)
    # ★ **两个旧名都保留为别名**：改名前打开过的标签页把
    #   ``gui_restore = 'gui.show_license_count()'`` / ``'gui.show_license_feedback()'``
    #   存进了标签状态（见 main.py 的 ``__save_tabs``），重启时按原文重放 —— 少了别名，
    #   那些标签页就再也打不开（``gui function <show_license_count> not found``）。
    #   一份别名换老状态能恢复，值得。新代码请用新名。
    #   ⚠️ 别名同时也留在控制台命令表里，用户敲惯的旧命令不会失效。
    gui.add_func('show_license_count', show_check_count_view)
    gui.add_func('show_license_feedback', show_feedbacks_view)

    # ★ 三个条目都带 ``is_enabled=not_running``：两个记录页要联网、管理页也要联网读名单，
    #   正在跑仿真时点它们只会排队等，不如直接置灰。
    #   ⚠️ 判据写成 ``not gui.is_running()``（``main.py`` 与其它菜单也这么做）：主窗口的
    #   ``not_running`` 是 ``__init_actions`` 里的闭包，本文件拿不到；而
    #   ``gui.is_running()`` 正是它内部调的那一个，语义完全一致。
    #   ⚠️ ``add_action`` 的 ``is_enabled`` 会**动态地**调用（见 ``Action.is_enabled``），
    #   所以这里传函数即可，不必在注册时求值。
    def not_running():
        return not gui.is_running()

    # ⚠️ 菜单标题与 ``main.py`` 里那一行 ``get_menu`` **逐字一致**
    #   （``['帮助', '用户']``），否则 ``get_menu`` 会另建一个同名子菜单，
    #   界面上出现两个「用户」。
    #   ``menu`` 用 list 形式时，``get_menu`` 会**按层级逐个查找、缺哪层就建哪层**，
    #   所以即使 ``main.py`` 没有先建出「用户」，这里也会自己建 —— 但那样它会
    #   排在「帮助」的**末尾**（见 ``main.py`` 的说明），所以仍在那边先建。
    #   ⚠️ 本文件在 ``MainWindow`` **构造之后**（由插件加载）才执行，
    #   所以这里只负责**往已有的「用户」子菜单里填条目**，不影响它的位置。
    # ⚠️ ``name`` 是 ``get_action`` / ``list_actions`` / ``refresh_action`` 的键（也是
    #   ``Action.objectName()``）。全仓核对过：**没有任何地方按字符串取这三项**
    #   （``get_action`` 的调用者只有 ``main.py`` 里按局部变量名查的那几处），所以
    #   ``check_count_view`` / ``feedbacks_view`` 与各自的函数名、控件名一起改过
    #   （``license_count`` → ``check_count_view``、``license_feedback`` → ``feedbacks_view``）
    #   —— 让三处名字彼此对得上。
    #   ⚠️ 唯一的用途是 ``gui.refresh_action(name)``；将来若要单独刷新，请用新键。
    #   （注意 ``name`` 与 gui 函数名**不是一回事**：前者是菜单项的键，后者是命令名。）
    gui.add_action(
        menu=['帮助', '用户'],
        name='user_admin_view',
        text='管理',
        icon='info',
        tooltip='按用户查看并修改授权的到期日与功能清单（仅管理员）',
        slot=show_user_admin,
        is_enabled=not_running,
        overwrite=False,
    )

    gui.add_action(
        menu=['帮助', '用户'],
        name='check_count_view',
        text='登录记录',
        icon='info',
        tooltip='查看某个邮箱对应用的许可查询次数（按天统计）',
        slot=show_check_count_view,
        is_enabled=not_running,
        overwrite=False,
    )

    gui.add_action(
        menu=['帮助', '用户'],
        name='feedbacks_view',
        text='反馈记录',
        icon='info',
        tooltip='查看某个用户某一天的反馈内容（本人或管理员）',
        slot=show_feedbacks_view,
        is_enabled=not_running,
        overwrite=False,
    )


def test_admin_1():
    """交互式查看本控件（**会真的联网**，需要管理员权限）."""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = UserAdminView()
    w.resize(940, 640)
    w.show()
    sys.exit(app.exec())


def test_admin_2():
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
    print('test_admin_2 passed (offline).')


def test_3():
    """离线自检：**登录记录页**（``CheckCountView``）—— 解析 + 标签 + 柱状图几何 + 邮箱列表.

    ⚠️ 与 ``test_2`` 一样**不联网**：所有控件都用 :func:`_quiet` 关掉了「首次显示自动
    查询」，否则 ``showEvent`` 会起真实的联网线程，解释器退出时进程会崩。
    """
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
        assert got == expect, (reply, got, expect)

    # 标签展开：30 天区间的首尾必须落在区间的两端
    labels = CheckCountView._make_labels('2026-09-06 ~ 2026-10-05', 30)
    print('labels[0] =', labels[0], ' labels[-1] =', labels[-1],
          ' len =', len(labels))
    assert labels[0] == '09-06' and labels[-1] == '10-05'

    # 柱状图几何：每根柱子都能被点中
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

    print('test_3 passed (offline).')


# ======================================================================
# 反馈记录页的离线自测（原 ``zmlx/ui/tabs/_test_feedbacks_view.py``）
#
# ⚠️ 2026-10-31 随控件一并并入本文件：断言**数据结构与显示文本**，不看像素、
# 不联网、不需要 DLL。跑法：``python zmlx/ui/plugins/builtin/user_admin.py --self-test 4``。
# ======================================================================


#: 自测计数（``test_4`` 用）：通过的条数 / 失败的条数。
OK = 0
BAD = 0


def check(label, got, want):
    global OK, BAD
    if got == want:
        OK += 1
        print(f'  OK   {label}')
    else:
        BAD += 1
        print(f'  FAIL {label}\n         got  {got!r}\n         want {want!r}')


def contains(label, haystack, needle):
    global OK, BAD
    if needle in haystack:
        OK += 1
        print(f'  OK   {label}')
    else:
        BAD += 1
        print(f'  FAIL {label}\n         {needle!r} not in {haystack[:200]!r}')


def test_4():
    import base64
    import sys

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    print('--- 记号判定（复数是列表、单数是单条，只差一个 s）---')
    listing = ('Feedbacks: 2 | Email: a@b.com | Date: 2026-09-28'
               ' | Files: 20260928223007.json; 20260928224500.json')
    one = 'Feedback: x.json | Email: a@b.com | FileBase64: e30='
    check('list_ok(listing)', _Parsers.list_ok(listing), True)
    check('read_ok(one)', _Parsers.read_ok(one), True)
    # 两个必须互斥 —— 拿混 = 成功读成失败
    check('list_ok(one)', _Parsers.list_ok(one), False)
    check('read_ok(listing)', _Parsers.read_ok(listing), False)
    # 提交反馈的记号同名不同义
    check('list_ok(Succeed)', _Parsers.list_ok('Succeed'), False)
    check('read_ok(Succeed)', _Parsers.read_ok('Succeed'), False)
    check('list_ok(Not permitted.)', _Parsers.list_ok('Not permitted.'), False)

    print()
    print('--- parse_files（0 条时没有 Files 段 -> 空列表，不是错误）---')
    check('2 files', _Parsers.parse_files(listing),
          ['20260928223007.json', '20260928224500.json'])
    check('0 files', _Parsers.parse_files(
        'Feedbacks: 0 | Email: a@b.com | Date: 2026-09-28'), [])
    check('with Dropped',
          _Parsers.parse_files('Feedbacks: 3 | Email: a@b.com'
                               ' | Date: 2026-09-28 | Dropped: 1'
                               ' | Files: a.json; b.json'),
          ['a.json', 'b.json'])
    check('with Truncated',
          _Parsers.parse_files('Feedbacks: 1000 | Email: a@b.com'
                               ' | Date: 2026-09-28 | Truncated: true'
                               ' | Files: a.json'), ['a.json'])
    check('rejected', _Parsers.parse_files('Not permitted.'), [])

    print()
    print('--- find_display_name ---')
    check('from reply', _Parsers.find_display_name(one), 'x.json')
    check('on rejection', _Parsers.find_display_name('Not permitted.'), '')

    print()
    print('--- format_stamp（纯显示，不改发给服务端的名字）---')
    check('normal', _Parsers.format_stamp('20260928223007.json'),
          '2026-09-28 22:30:07')
    check('bad name', _Parsers.format_stamp('bad.json'), '')
    check('13 digits', _Parsers.format_stamp('2026092822300.json'), '')
    check('non-digit', _Parsers.format_stamp('2026092822300a.json'), '')

    print()
    print('--- format_content: 五种数据形态（返回四个键的 dict）---')
    # ① 合法 JSON 且带 text -> **拆开**（元数据 + text 两块）
    rec = {'ts': '2026-09-28T22:30:07+08:00', 'text': '中文', 'n': 1}
    raw = json.dumps(rec, ensure_ascii=False).encode('utf-8')
    parts = _Parsers.format_content(raw)
    check('split flag', parts['split'], True)
    check('text pulled out', parts['text'], '中文')
    check('meta keeps other fields', json.loads(parts['meta']), {'ts': rec['ts'], 'n': 1})
    check('meta drops text key', 'text' not in json.loads(parts['meta']), True)
    check('meta is indented', '\n  ' in parts['meta'], True)
    check('json note empty', parts['note'], '')

    # ①b 没有 text 字段 -> **不拆**，退回整份缩进 JSON
    rec2 = {'ts': '2026-09-28T22:30:07+08:00', 'n': 1}
    parts = _Parsers.format_content(
        json.dumps(rec2, ensure_ascii=False).encode('utf-8'))
    check('no text -> not split', parts['split'], False)
    check('no text -> full json shown', json.loads(parts['meta']), rec2)
    check('no text -> body empty', parts['text'], '')

    # ①c text 不是字符串 -> **不拆**（那份记录的 text 是数据不是正文）
    for label, value in (('number', 42), ('object', {'a': 1}), ('null', None),
                         ('list', [1, 2])):
        parts = _Parsers.format_content(
            json.dumps({'text': value}).encode('utf-8'))
        check(f'text={label} -> not split', parts['split'], False)

    # ①d 顶层不是对象 -> 不拆
    for label, doc in (('list', [1, 2]), ('number', 5), ('string', 'hi')):
        parts = _Parsers.format_content(json.dumps(doc).encode('utf-8'))
        check(f'top-level {label} -> not split', parts['split'], False)

    # ①e text 为空串 -> **仍然算拆开**（元数据非空、正文区空着）
    parts = _Parsers.format_content(
        json.dumps({'ts': 'x', 'text': ''}, ensure_ascii=False).encode('utf-8'))
    check('empty text still splits', parts['split'], True)
    check('empty text body', parts['text'], '')

    # ①f split_json 绝不改动传进来的对象
    original = {'ts': 'x', 'text': 'body'}
    _Parsers.split_json(original)
    check('split_json does not mutate input', original,
          {'ts': 'x', 'text': 'body'})

    # ② 能解码但不是 JSON -> 原文 + 说明（**不拆**）
    parts = _Parsers.format_content(b'hello world')
    check('plain text kept', parts['meta'], 'hello world')
    check('plain text not split', parts['split'], False)
    contains('plain text explained', parts['note'], '不是合法 JSON')

    # ③ 二进制 -> hex 摘要
    # ⚠️ 必须用**真的解不成 UTF-8** 的字节：``bytes(range(16))`` 全是控制字符，
    #    但它们是合法的 UTF-8，于是走「原文」那条分支（这一点值得记住）。
    binary = bytes([0xff, 0xfe, 0x00, 0x01, 0x80, 0x81])
    parts = _Parsers.format_content(binary)
    check('hex shown', parts['meta'], ' '.join(f'{b:02x}' for b in binary))
    check('binary not split', parts['split'], False)
    contains('binary explained', parts['note'], '不是文本')

    # ③b 控制字符（合法 UTF-8）走的是**原文**分支，不是 hex
    parts = _Parsers.format_content(bytes(range(16)))
    check('control chars are text', parts['meta'],
          bytes(range(16)).decode('utf-8'))

    # ④ 0 字节 -> 成功，但显示为空文件
    parts = _Parsers.format_content(b'')
    check('0-byte meta empty', parts['meta'], '')
    check('0-byte note', parts['note'], '（这个文件是空的）')
    check('0-byte not split', parts['split'], False)

    # ⑤ None（业务拒绝）-> 与 0 字节**不同**
    parts = _Parsers.format_content(None)
    check('None meta empty', parts['meta'], '')
    contains('None note differs', parts['note'], '没拿到内容')
    check('None note != 0-byte note',
          parts['note'] != '（这个文件是空的）', True)

    # ⑥ 非法 UTF-8
    parts = _Parsers.format_content(b'\xff\xfe\x00abc')
    contains('bad utf-8 explained', parts['note'], '不是文本')

    print()
    print('--- full_json（「完整原文」区的内容）---')
    check('full json parses back', json.loads(_Parsers.full_json(raw)), rec)
    check('full json keeps text', 'text' in json.loads(_Parsers.full_json(raw)),
          True)
    check('full json on non-json', _Parsers.full_json(b'hello'), '')
    check('full json on empty', _Parsers.full_json(b''), '')
    check('full json on binary', _Parsers.full_json(b'\xff\xfe'), '')

    print()
    print('--- is_truncated ---')
    check('truncated', _Parsers.is_truncated(
        'Feedback: x.json | Email: a@b.com | Truncated: true'
        ' | FileBase64: e30='), True)
    check('not truncated', _Parsers.is_truncated(one), False)

    print()
    print('--- 控件：列举成功后填充文件列表 ---')
    w = FeedbacksView(email='a@b.com', date='2026-09-28')
    w._on_list_reply(listing, '往返耗时：0.42 s')
    check('files filled', w.get_files(),
          ['20260928223007.json', '20260928224500.json'])
    check('banner mentions count', '2' in w.status_label.text(), True)

    print()
    print('--- 控件：0 条 / 越权 / 超一页 三种横幅 ---')
    w._on_list_reply('Feedbacks: 0 | Email: a@b.com | Date: 2026-09-28', '')
    check('0 files', w.get_files(), [])
    contains('0-file banner', w.status_label.text(), '没有反馈')

    w._on_list_reply('Not permitted.', '')
    contains('denied shows raw server text', w.status_label.text(),
             'Not permitted.')
    # ⚠️ 绝不替服务端编「邮箱不存在」
    check('does not invent text', '邮箱不存在' in w.status_label.text(), False)

    w._on_list_reply('Feedbacks: 1000 | Email: a@b.com | Date: 2026-09-28'
                     ' | Truncated: true | Files: a.json', '')
    contains('page-truncated banner', w.status_label.text(), '截断')

    w._on_list_reply('', '')
    contains('empty reply handled', w.status_label.text(), '网络')

    print()
    print('--- 控件：读取一条内容（合法 JSON 带 text -> 拆成两块）---')
    w2 = FeedbacksView(email='a@b.com', date='2026-09-28')
    b64 = base64.b64encode(raw).decode('ascii')
    w2._on_read_reply(
        f'Feedback: 20260928223007.json | Email: a@b.com | FileBase64: {b64}',
        '往返耗时：0.5 s')
    check('text box visible (split)', w2._text_box.isVisibleTo(w2), True)
    check('meta shows other fields', json.loads(w2.meta_view.toPlainText()),
          {'ts': rec['ts'], 'n': rec['n']})
    check('text box shows body', w2.text_view.toPlainText(), '中文')
    check('meta has no text key',
          'text' not in json.loads(w2.meta_view.toPlainText()), True)
    check('full source visible', w2._full_box.isVisibleTo(w2), True)
    check('full source is whole json',
          json.loads(w2.full_view.toPlainText()), rec)
    contains('file name in label', w2.file_label.text(), '20260928223007.json')
    contains('read ok banner', w2.status_label.text(), '读取成功')
    contains('split mentioned in banner', w2.status_label.text(), 'text')

    print()
    print('--- 控件：没有 text 字段 -> 退回单区（下框与完整原文都藏起来）---')
    w2b = FeedbacksView(email='a@b.com')
    rec_notext = {'ts': '2026-09-28', 'n': 7}
    raw_notext = json.dumps(rec_notext, ensure_ascii=False).encode('utf-8')
    w2b._on_read_reply(
        'Feedback: x.json | FileBase64: '
        + base64.b64encode(raw_notext).decode('ascii'), '')
    check('text box hidden', w2b._text_box.isVisibleTo(w2b), False)
    check('full source hidden', w2b._full_box.isVisibleTo(w2b), False)
    check('meta shows whole json', json.loads(w2b.meta_view.toPlainText()),
          rec_notext)

    print()
    print('--- 控件：0 字节文件是成功（与「文件不存在」分开）---')
    w3 = FeedbacksView(email='a@b.com')
    w3._on_read_reply('Feedback: x.json | Email: a@b.com | FileBase64: ', '')
    contains('0-byte banner', w3.status_label.text(), '空文件')
    check('0-byte does not split', w3._text_box.isVisibleTo(w3), False)

    w4 = FeedbacksView(email='a@b.com')
    w4._on_read_reply('The feedback file is not available.', '')
    contains('missing file shows raw text', w4.status_label.text(),
             'The feedback file is not available.')
    check('missing file banner differs from 0-byte',
          '空文件' in w4.status_label.text(), False)

    print()
    print('--- 控件：截断的内容不抛异常，且横幅说明 ---')
    w5 = FeedbacksView(email='a@b.com')
    partial = '{"ts": "2026-09-28", "text": "被截断的'.encode('utf-8')
    b64p = base64.b64encode(partial).decode('ascii')
    w5._on_read_reply(
        f'Feedback: x.json | Email: a@b.com | Truncated: true'
        f' | FileBase64: {b64p}', '')
    contains('truncated banner', w5.status_label.text(), '截断')
    check('content still shown',
          len(w5.meta_view.toPlainText() + w5.text_view.toPlainText()) > 0, True)

    print()
    print('--- 控件：二进制内容不崩 ---')
    w6 = FeedbacksView(email='a@b.com')
    w6._on_read_reply(
        'Feedback: x.json | Email: a@b.com | FileBase64: '
        + base64.b64encode(b'\xff\xfe\x00\x01').decode('ascii'), '')
    contains('binary banner', w6.status_label.text(), '十六进制')
    check('binary content non-empty',
          len(w6.meta_view.toPlainText()) > 0, True)
    check('binary does not split', w6._text_box.isVisibleTo(w6), False)

    print()
    print('--- 控件：切换文件时上一条的残留被清掉 ---')
    w6._on_read_reply(
        f'Feedback: y.json | FileBase64: {b64}', '')
    check('now split again', w6._text_box.isVisibleTo(w6), True)
    w6._clear_content()
    check('meta cleared', w6.meta_view.toPlainText(), '')
    check('text cleared', w6.text_view.toPlainText(), '')
    check('full source cleared', w6.full_view.toPlainText(), '')
    check('text box hidden after clear', w6._text_box.isVisibleTo(w6), False)
    check('full box hidden after clear', w6._full_box.isVisibleTo(w6), False)

    print()
    print('--- 控件：日期快捷按钮（本地计算，不联网）---')
    w7 = FeedbacksView(email='a@b.com')
    w7.set_date_days(0)
    import datetime
    check('today', w7.date_view.text(),
          datetime.date.today().strftime('%Y-%m-%d'))
    w7.set_date_days(1)
    check('yesterday', w7.date_view.text(),
          (datetime.date.today() - datetime.timedelta(days=1)
           ).strftime('%Y-%m-%d'))

    print()
    print('--- 控件：get_query 只去空白，不做校验 ---')
    w7.date_view.setText('  not-a-date  ')
    w7.email_view.setText('  a@b.com  ')
    check('get_query', w7.get_query(), ('a@b.com', 'not-a-date'))

    print()
    print('--- 控件：不实现 save_file（绝不落盘别人的反馈正文）---')
    check('no save_file', hasattr(w7, 'save_file'), False)

    print()
    print('--- 控件：cleanup_before_tab_close 释放全部四个线程引用 ---')
    w7.cleanup_before_tab_close()
    check('all workers released',
          [w7._list_worker, w7._read_worker,
           w7._prefill_worker, w7._user_list_worker],
          [None, None, None, None])

    print()
    print(f'== {OK} passed, {BAD} failed ==')
    if BAD:
        raise SystemExit(1)


# ======================================================================
# 入口（**整个文件只能有这一处**，见下面的 ⚠️）
# ======================================================================

# ⚠️ 插件的标准形式：**注册写在这个分支里**。
#    插件机制用 ``exec`` 执行本文件时，命名空间里的 ``__name__`` 被设成
#    ``'__zml_plugin__'``，于是这里成立 —— 只注册，不开窗口。
#    ⚠️ **不要**在顶层裸写 ``setup_ui()``：那样「插件加载」与「直接运行本文件」
#    走同一段代码，既无法区分两种意图，也无法在直接运行时自测。
#    ⚠️⚠️ **全文件只许有这一个 ``__zml_plugin__`` 块**：本文件由好几个模块合并而来，
#    每个原模块都带着自己的入口块 —— 2026-10-31 合并 `feedbacks_view.py` /
#    `_test_feedbacks_view.py` 时，就把多余的那一套漏在了文件中间（`test_4` 之前）。
#    以后**再往本文件里合代码，务必连同它的 ``if __name__ == ...`` 块一起删掉**，
#    否则同名块会出现两次（`setup_ui` 有 `@execute_once` 兜底，不会真的挂两遍菜单，
#    但读代码的人会以为它会）。
if __name__ == '__zml_plugin__':
    setup_ui()

# ⚠️ 两支用**两个独立的 if**，不要写成 if / elif（见 `../../plugins/AGENTS.md` §2 第 4 步）。
#
# ⚠️⚠️ **本文件是三段控件的合并体，所以自测有 7 个**，按页面分类命名
#    （`test` / `test_count` / `test_feedbacks` / `test_admin` 前缀 = 哪一段）：
#
#    ======================  =====================================================
#    命令                     跑什么
#    ======================  =====================================================
#    直接运行（无参数）        全部**离线**自测（管理 / 登录记录 / 反馈记录）
#    ``--self-test admin``   管理页：`test_admin_2`
#    ``--self-test count``   登录记录页：`test_count_2`
#    ``--self-test feedbacks`` 反馈记录页：`test_4`（98 条断言）
#    ======================  =====================================================
#
#    ⚠️ **不要**把这些自测改回同名的 `test_1` / `test_2`：合并前它们各在一个模块里，
#    同名无妨；合进一个文件后后定义的会**覆盖**前面的，「直接运行本文件」就只会跑到
#    最后那一份（2026-10-31 踩过，连带引出了 `_Worker` 类互相覆盖的 bug）。
if __name__ == '__main__':
    import sys
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    if '--self-test' in sys.argv:
        if 'admin' in sys.argv:
            test_admin_2()
        elif 'count' in sys.argv:
            test_count_2()
        else:
            test_4()
    else:
        # 三段一起跑：任何一段抛异常都会中止（正是自测该有的行为）
        test_admin_2()
        test_count_2()
        test_4()
        print('ALL OFFLINE SELF-TESTS PASSED.')

"""软件登录控件（邮箱验证码 + 登录本机）.

★ **界面上一律说「登录」，不说「注册」**（措辞约定见
``zmlx/_private/AUTHORIZATION_NOTES.md``）：用户看到的是「登录」，不涉及授权。

把「本机」与「邮箱」关联起来，让 :meth:`zmlx.exts.web_license.check` 从此读到这个
邮箱的正式授权。

★ 一个控件、两种形态
-------------------

本控件只有**一套输入框**、**一个主按钮**，形态随「本机绑定没有」自动切换。
**不**再另开一块「修改资料」区域 —— 那样会出现两处同一份信息（很乱），而且
下方改完上方不跟着变（自相矛盾）。

::

    ── 登录（未登录时）────────────────────────────────────────────
    登录
    用邮箱收一次验证码，即可完成登录。
    ┌──────────────────────────────────────────────────────────────┐
    │ 正在确认登录状态…            ← 一句话状态横幅（自动查询）      │
    └──────────────────────────────────────────────────────────────┘
    ────────────────────────────────────────────────────────────────
       姓名 [必填，例如：张三          ]
       单位 [必填，例如：XX大学        ]
       备注 ┌────────────────────────────────────────────────────┐
            │ 选填，可写多行（例如：博士生 / 用途说明）            │ ← 多行框
            └────────────────────────────────────────────────────┘
       邮箱 [you@example.com        ]  [发送验证码]
     验证码 [6 位数字                  ]
       ┌────────────────────────────────────────────────────────┐
       │                        登录                            │  ← 主按钮
       └────────────────────────────────────────────────────────┘
                                               [刷新登录状态]
    ▾ 服务器原始答复 / ▸ 日志（排错用）

    ── 更新信息（已登录时）────────────────────────────────────────
    登录
    已登录，可直接修改下面的信息（留空 = 不改该项）。
    ┌──────────────────────────────────────────────────────────────┐
    │ 已登录：zhangzhaobin@mail.iggcas.ac.cn   [在这台电脑上退出]   │
    └──────────────────────────────────────────────────────────────┘
    ────────────────────────────────────────────────────────────────
       姓名 [张召彬                    ]
       单位 [中国科学院地质与地球物理研究所]
       备注 ┌────────────────────────────────────────────────────┐
            │ self-registered via email code                       │
            └────────────────────────────────────────────────────┘
       邮箱 [（已登录：要换邮箱请直接改这里）]  ← **仍可编辑**，且没有「发送验证码」
                          ↑ 已登录时：验证码整行消失
       ┌────────────────────────────────────────────────────────┐
       │                    更新信息                            │  ← 同一个按钮，换了文案
       └────────────────────────────────────────────────────────┘
                                               [刷新登录状态]
    ▾ 服务器原始答复 / ▸ 日志（排错用）

★★ **单出处原则（本控件的核心约束）**

输入框**只有一套**。⚠️ **绝不要**再建第二组「显示用」的框或标签 —— 那正是
上一版「下方更新之后上方没更新」的成因：两处各存一份，刷了一处另一处就是旧的。

于是一条纪律：**服务端给的值只有一个入口**（:meth:`LicenseRegister._prefill`），
任何写入都必须经过它。

★ 两种形态怎么切（:meth:`LicenseRegister._apply_mode`）

判据是 :func:`bound_info` 是否给出内容（= 本机有没有绑定邮箱），**外加**一条：
用户有没有**改动邮箱框**（:meth:`LicenseRegister._on_email_edited`）。

============================  ====================  ========================
                              **未登录 / 换邮箱中**  **已登录（未动邮箱）**
============================  ====================  ========================
主按钮文案                    登录                    更新信息
点击后调的服务端动作            ``submit``             ``update_user_info`` ＋
                                                    ``write_file``/``delete_file``
                                                    （备注，见下）
「验证码」那一行               显示                   **整行隐藏**
「发送验证码」按钮             显示                   **隐藏**
邮箱输入框                     可编辑                 **可编辑**
说明文字                       用邮箱收一次验证码…      已登录，可直接修改…
============================  ====================  ========================

★★ **换绑邮箱 = 改邮箱框**（这是本控件唯一一条「改输入框就换动作」的规则）

⚠️⚠️ 服务端换绑走的是 ``submit``（带 ``machine_code``），**不是**
``update_user_info`` —— 后者**永远改不了 ``email``**（它是身份字段）。所以「想换
邮箱」必须回到注册形态：要重新收验证码、要按下 ``submit``。

于是规则定成：**邮箱框一被改动（且与当前绑定的邮箱不同），立刻切回注册形态**；
改回原值则切回更新形态。

⚠️ **邮箱框在两种形态下都必须可编辑**：「这里不能改」的正确表达不是置灰。
⚠️ **监听 ``textEdited`` 而不是 ``textChanged``**：前者只在**用户真的敲键盘**时
发信号，后者在我们自己 ``setText`` 预填时也会发 —— 那会让界面自己把自己翻乱。
⚠️ **判据是「与当前绑定的邮箱是否相同」**（``self._bound_email``），不是「有没有
敲过键盘」。
⚠️ **隐藏的是「整行」，不是把框置灰**（widget/AGENTS.md 明令「别用置灰当闸门」）。

★ 换绑的副作用（必须让用户知道）

换绑走 ``submit``，而它在给了 ``user`` / ``org`` 时会把这两个字段**一并写到新
邮箱那份授权上**。所以换绑成功的提示里**明说**了这一点。

- **旧邮箱那份授权本身不受影响**；
- **换绑不改到期日**。

★ 备注：多行框，存在服务端的 ``note.txt`` 里

★★ **备注走「用户文件」接口，不走许可记录**（2026-10 改）：它曾经是许可记录里的
``note`` 字段（``get_user_info`` / ``update_user_info``），现在改存成一个用户文件
``note.txt``：

| | 读 | 写 | 清空 |
|---|---|---|---|
| 动作 | ``read_file`` | ``write_file`` | ``delete_file`` |
| 记号 | ``File:`` | ``FileWritten`` | ``FileDeleted`` |

- **读**：回复是 ``File: <base64>``，解码见 :meth:`_ProfileBox.decode_note`；
  文件不存在时回复就是 ``File:``（空）—— 那是「还没有备注」，**是成功**。
- **写**：``data_base64`` 必须是**编码后**的内容（见
  :meth:`_ProfileBox.note_to_file_body`）。⚠️ 与旧的 ``update_user_info(note=…)``
  直接收原文不同，这是本改动最容易漏的一处。
- **清空**：备注框被清空并保存时，走 ``delete_file`` 真的把那份文件删掉。
  ⚠️ **不能靠发一个空 ``data_base64``**：那是 **400**（服务端刻意不让空值降级
  成删除，见其 ``write_file``）。

⚠️⚠️ **服务端存不住换行**：它会把所有换行与控制字符压成空格。所以由**客户端**
把换行折成显式分隔符（:data:`_ProfileBox.NOTE_LINE_SEP` = ``；``）。
落地在 :meth:`_ProfileBox.note_to_wire`。

⚠️ **取值用 ``toPlainText()`` 而不是 ``text()``**（统一走
:meth:`_ProfileBox.note_of`）。
⚠️ **多行控件没有 ``setMaxLength``**：长度靠
:meth:`LicenseRegister._on_note_changed` 在输入时就地拦。

★ 注册时也能写备注，但要分两步

⚠️⚠️ **``submit`` 的请求体里没有备注** —— 所以「注册时直接写备注」**必须分
成两步**：① ``submit`` 完成注册 / 绑定；② 紧接着调一次 ``write_file``，
把备注写进 ``note.txt``。这一步对本控件是**透明的**。

- **只在备注非空时才补**；
- **第二步失败不回滚注册**（注册已经成功了，那时弹「注册失败」是**谎报**）。

★ 「更新信息」最多发两次请求

姓名 / 单位走 ``update_user_info``（``Updated``），备注走
``write_file`` / ``delete_file``（``FileWritten`` / ``FileDeleted``）——
**先身份、后备注**，两步各自独立成败（见 :meth:`LicenseRegister.update_info`）。

自动查询与预填
--------------

控件**首次显示时**会自己在后台线程里查一次在线状态
（:meth:`LicenseRegister.auto_query`），据此决定两种形态，并把已绑定那份授权里的
邮箱 / 姓名 / 单位**填进输入框**（:meth:`LicenseRegister._prefill`）。

同一套收尾也挂在「刷新授权状态」按钮上。

两条路径给状态栏的 ``read_cache`` 不一样，**别照抄**：

- 点「刷新授权状态」→ 传 ``True``（读缓存）；
- 注册成功 → 传 ``False``（强制联网）：缓存里存着「绑定之前」的成功结果。

四条约束（改之前先读）：

1. **必须开线程**：单次查询最长阻塞 60 秒。
2. **只在输入框为空时填**：覆盖用户刚输入的内容是最讨厌的一类交互。
3. **未绑定就什么都不填**：那种情况下答复里的姓名 / 单位并不属于本机用户。
4. ⚠️ **``_prefill`` 是「服务端值」的唯一入口**。

⚠️ **改完资料之后要重新读一次服务端**：这一步**不能省**，否则用户看到的是「我刚
填的值」（本地文本），而不是「服务端真的存下了什么」。

版式：为什么不写颜色
--------------------

⚠️ **不要在控件里 ``setStyleSheet`` 写 ``color`` / ``background``**：本程序会加载
用户可编辑的 ``zml_window_style.qss``，并且有暗色模式。需要「次要文字」就用
``setEnabled(False)``，需要边框就用 ``palette(mid)``（见 :data:`BANNER_QSS`）。

调用服务端时要知道的三条
------------------------

1. **成功与否只看响应正文，不看 HTTP 状态码**：业务失败也可能按 200 返回。
   所以本控件把**服务端的原话**显示给用户，绝不替换成含糊的「失败」。
2. **``web_license.send_code`` / ``web_license.submit`` 不抛异常**：一切失败都以
   一句描述文本返回。下面那些 ``lambda`` 直接返回 ``(True, 正文)``。
3. **判定一律用「只看开头」的比较**（:func:`is_sent` / :func:`is_bound`），
   **不要** ``==`` 严格相等。

姓名与单位
----------

⚠️ **两个都是必填的**：控件在**发验证码之前**就把关 —— 署名只在创建那一刻有机会
写入，事后补不回来，所以宁可提前拦住。

⚠️ **机器码（硬件码）不显示给用户**：它由 ``web_license.submit`` 在 C++ 侧自己算，
控件既不显示也不传。

⚠️ 自检一律走 ``check_web('*', read_cache=False)``：读缓存会让用户看到**注册之前
的旧结论**。

修改已注册的资料
----------------

已绑定时，同一个主按钮改调服务端的 ``update_user_info``。

★ **服务端那个动作【不验码】**：机器码即凭证。所以已绑定时**整行验证码都收起来**。

四条取舍：

1. **只有一套输入框**；改完由 :meth:`_after_saved` 重新联网读一次服务端。
2. **三个可改字段都是选填**（``user`` / ``org`` / ``note``）：留空 = 不改。
   ⚠️ 所以更新模式下 :meth:`_require_identity` **不生效**（那是注册的门）。
3. **邮箱不可改**：服务端的写动作绝不动 ``email``（身份字段）。
4. **不额外联网读资料**：姓名 / 单位就在 ``check`` 响应的段里。

⚠️ **四个动作、四个成功记号，各判各的**（拿混一律把成功读成失败）：
``Sent``（发码）/ ``Bound``（注册绑定）/ ``Yes``（查询）/ ``Updated``（改资料）。

用法::

    from zmlx.ui.tabs.license_register import LicenseRegister
    widget = LicenseRegister()
    widget.show()

实现上的三条取舍
----------------

1. **网络请求全在后台线程**（:class:`_Worker`）：请求期间按钮全部禁用，防止连点
   两下发两封邮件。⚠️ 请求本身由 **C++ 侧**发出，单次最长阻塞 60 秒。
2. **不在控件里发 HTTP**：网络部分收在 ``zmlx.exts.web_license`` 里。
3. **不显示硬件码**：注册完全由邮箱验证码驱动。

响应分段伪造的防线、线程崩溃纪律、服务端的取值规则，见
``zmlx/_private/AUTHORIZATION_NOTES.md`` §10 / §12。

Modified by DeepSeek, 2026-09-27
Modified by DeepSeek, 2026-10-11: **重新设计成「一个控件、两种形态」**。
Modified by DeepSeek, 2026-10-13: 备注改存服务端用户文件 ``note.txt``
（``read_file`` / ``write_file`` / ``delete_file``），不再用许可记录的
``note`` 字段。
Modified by DeepSeek, 2026-10-16: 本文件迁至 ``zmlx/ui/tabs/``（标签页专用控件包）；
许可答复的解析与查询工具下沉到 :mod:`zmlx.ui.utils.lic_utils`，本模块改为从那里 import。
"""

import base64
import binascii

from zmlx.exts import web_license
from zmlx.ui.utils.lic_utils import (
    CHECK_FEATURE, DEFAULT_SOURCE, MAX_ORG_LEN, MAX_USER_LEN, PURPOSE_BIND,
    _leading_word,
    bound_info, check_web, detail_of, find_field, fingerprint_sha,
    format_elapsed, is_bound, is_sent, is_yes, pack_elapsed, unpack_elapsed,
)
from zmlx.ui.pyqt import QtCore, QtWidgets


# ---------------------------------------------------------------------------
# 版式常量
#
# ⚠️ **这里不写任何色值**：本程序会加载用户可编辑的 zml_window_style.qss
#    （「设置 → 样式表」），并且有暗色模式（gui.in_dark_mode）。控件里一旦
#    出现硬编码颜色，要么在暗色下瞎眼，要么把用户自己的主题盖掉。
#    所以「现代感」只靠间距、对齐、层次与控件类型来实现，颜色一律跟随主题。
# ---------------------------------------------------------------------------

#: 外边距与元素间距（统一 12 / 8，避免各处 margin 随手给值造成节奏凌乱）。
MARGIN = 12
GAP = 8

#: 主按钮（「注册并绑定本机」）的最小高度，让它明显高于普通控件。
BUTTON_HEIGHT = 34

#: 「服务器原始答复」框的固定高度：那里只有「原始字符串 + 往返耗时」两行，
#: 给两行多一点的高度即可；用固定值免得它随内容长短把窗口撑来撑去。
STATUS_VIEW_HEIGHT = 62

#: 状态提示条的样式：**只含边框与内边距，没有任何 color / background**。
#: 颜色由当前主题的调色板决定，因此亮色与暗色都能正常显示。
BANNER_QSS = 'border: 1px solid palette(mid); border-radius: 6px;'


#: 正在后台跑的 :class:`_Worker`（模块级强引用）。
#:
#: ⚠️ **线程的 parent 绝不能是本控件**：标签页关闭时控件会被
#: ``TabWidget.close_tab`` 用 ``deleteLater()`` 销毁，parent 是本控件的线程会
#: **跟着一起被析构**；而 Qt 规定「正在运行的 QThread 不能被销毁」，网络请求
#: 还没回来时就会直接 abort::
#:
#:     QThread: Destroyed while thread '' is still running
#:
#: 这是**进程级崩溃**，不是异常（``web_license.check`` 最长 60 秒，关标签时
#: 线程几乎必然还在跑）。``closeEvent`` 里的 ``wait()`` 兜不住这一点 ——
#: ``close_tab`` 走 ``deleteLater()``，**根本不发** ``closeEvent``。
#:
#: 挂在这里线程一定能跑完；控件销毁后 Qt 自动断连，迟到结果被安全丢弃。
_RUNNING_WORKERS = []


def _forget_worker(worker):
    """把已经跑完的线程从登记表里摘掉（主线程调用）。"""
    try:
        _RUNNING_WORKERS.remove(worker)
    except ValueError:
        pass


def _is_deleted(obj):
    """判断一个 Qt 对象的底层 C/C++ 对象是否已经被销毁。

    ⚠️ 场景：控件被 ``deleteLater()`` 销毁了，但它的后台线程还在跑，线程回来的
    信号仍然会**投递到那个已经不存在的控件**上（PyQt 的 Python 包装对象往往比
    C++ 对象活得久）。此时任何 ``self.send_button.setEnabled(...)`` 都会抛::

        RuntimeError: wrapped C/C++ object of type QPushButton has been deleted

    迟到结果应当被**直接丢弃**，所以槽函数开头要先问一句「我还活着吗」。

    Args:
        obj: 任意 Qt 对象（QWidget 等）。

    Returns:
        bool: 底层对象已被销毁返回 True。

    Added by DeepSeek, 2026-10-07
    """
    # ⚠️ 名字必须**按绑定逐个试**：PyQt6 的 sip 在 ``PyQt6.sip`` 下，顶层
    #    ``import sip`` 在 PyQt6 环境里是**找不到**的（会静默退化成「没被删」，
    #    等于本函数完全没生效）。PyQt5 则两种写法都能用。
    for name in ('PyQt6.sip', 'PyQt5.sip', 'sip', 'shiboken6', 'shiboken2'):
        try:
            mod = __import__(name, fromlist=['_'])
        except ImportError:
            continue
        checker = getattr(mod, 'isdeleted', None)
        if checker is None:
            checker = getattr(mod, 'isValid', None)
            if checker is not None:
                # shiboken 的语义与 sip 相反：isValid 为真 = 还活着
                try:
                    return not bool(checker(obj))
                except Exception:
                    return False
            continue
        try:
            return bool(checker(obj))
        except Exception:
            return False
    # 拿不到绑定层的检查函数：保守地认为「还活着」，让正常路径照常工作
    return False


class _ProfileBox:
    """「更新信息」形态用到的常量与判据（**纯命名空间，不实例化**）。

    按widget/AGENTS.md §2「模块级内容」：模块级只留 import / 类定义 / ``test_1()``
    / 主入口，所以新增的常量与工具函数一律收进类里。⚠️ 模块里那几个老的模块级
    函数（:func:`is_sent` / :func:`find_field` …）**本次不动** —— 它们已被
    ``about`` / ``license_button`` / ``check_count_view`` / ``feedbacks_view``
    四个模块 import 走，改名会牵动一片，且与本功能无关。
    """

    #: 写动作的成功记号（服务端 ``update_user_info``）。
    #:
    #: ⚠️ 与注册侧的 ``Sent`` / ``Bound`` / ``OK`` **刻意不同**：那是注册落地，
    #: 这是资料管理。**不要**拿 :func:`is_bound` 去判它（``Updated`` 不以 ``bound``
    #: 开头，会把**成功读成失败**）。
    SUCCESS_UPDATED = 'Updated'

    #: 备注**存在服务端的哪个文件里**（``read_file`` / ``write_file`` 的 ``file_name``）。
    #:
    #: ★★ 备注曾经走 ``get_user_info`` / ``update_user_info`` 的 ``note`` 字段，
    #: 现在改用**用户文件**接口存一个 ``note.txt``。理由：``note`` 是许可记录里的
    #: 一个字段，而备注在语义上就是「用户自己的一小段文字」，与其它用户文件同类；
    #: 归到文件接口后面还能顺带存更长的内容 / 附件。
    #:
    #: ⚠️ ``file_name`` 的形态由服务端严格校验（首字符须是字母或 ``_``，其余只许
    #: ``[A-Za-z0-9._-]``，长度 ≤ 64）：``note.txt`` 正好合规。
    NOTE_FILE_NAME = 'note.txt'

    #: 读动作的成功记号（服务端 ``read_file``）。
    #:
    #: ⚠️ 文件**不存在**时服务端回的也是这个前缀，只是后面什么都没有
    #: （``'File:'``）—— 那是「还没有备注」，**是成功**，不是失败。
    SUCCESS_FILE = 'File:'

    #: 写动作的成功记号（服务端 ``write_file``）。
    SUCCESS_FILE_WRITTEN = 'FileWritten'

    #: 删动作的成功记号（服务端 ``delete_file``）。
    #: ⚠️ 删除是**幂等**的：「本来就没有」也回它。
    SUCCESS_FILE_DELETED = 'FileDeleted'

    #: 备注的最大长度。服务端对 ``note`` 有自己的净化与限长，这里只是**界面层的
    #: 预防**（与 :data:`MAX_USER_LEN` / :data:`MAX_ORG_LEN` 同一条思路）。
    MAX_NOTE_LEN = 512

    #: 备注框的可见高度（像素）。给「多行」的观感，一次能看到三四行，
    #: 免得用户以为那还是个单行框。⚠️ 用固定高度而不是让它随内容长高：输入框
    #: 长高会把下面的按钮推走，一屏的版式就乱了（与 :data:`STATUS_VIEW_HEIGHT`
    #: 同一条理由）。
    NOTE_HEIGHT = 78

    #: **发出去时**用来替换换行的分隔符。
    #:
    #: ⚠️⚠️ **为什么必须替换**：服务端存不住换行（会把换行与控制字符压成
    #: 空格）。所以由**客户端**把换行换成一个看得见的分隔符：用户在框里看到的是
    #: 多行，服务端存的是同一句话但用 ``；`` 断开。
    #: 完整理由见 ``zmlx/_private/AUTHORIZATION_NOTES.md`` §10。
    NOTE_LINE_SEP = '；'

    #: ``note`` base64 解码失败时的返回值（调用方据此区分「空备注」与「读不到」）。
    NOTE_UNDECODABLE = None

    #: 写入侧**禁止**出现在 ``user`` / ``org`` 里的字符（与服务端**同一套规则**）。
    #:
    #: ⚠️ **两处必须保持一致**：漂了的表现是「本地放行、服务端 400」，用户会
    #: 收到一句与真实原因无关的报错。改任一侧都要同步另一侧。
    #:
    #: ⚠️ **``note`` 不在此列**：它可以含 ``|`` / ``:``，只有 ``user`` /
    #: ``org`` 受这条限制。
    FORBIDDEN_IN_IDENTITY = '|:'

    #: 零宽与方向控制字符（同样禁止出现在 ``user`` / ``org`` 里）。
    #: 它们**看不见**，混进名字里会让「两份看着一样的名字」其实不等。
    INVISIBLE_CHARS = (
        '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
        '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
        '\u2066', '\u2067', '\u2068', '\u2069',
    )

    @staticmethod
    def validate_identity(label, value):
        """检查 ``user`` / ``org`` 里有没有服务端禁止的字符。

        本地先查一遍，是为了**省一次往返**，以及**当场说清是哪一项**（服务端的
        报错不区分是哪一项，而界面上用户可能同时改了姓名与单位）。

        ⚠️ **规则必须与服务端一致**：本地若比服务端**松**，用户会拿到一句莫名
        的 400；若比服务端**紧**，用户会发现「明明能写却被本地拦住」。改任一侧
        都要同步另一侧。

        Args:
            label: 字段的中文名（``'姓名'`` / ``'单位'``），只用于报错。
            value: 已去空白的值。

        Returns:
            str: 有问题时返回一句给用户看的话；没有问题返回空串。
        """
        text = str(value or '')
        for ch in _ProfileBox.FORBIDDEN_IN_IDENTITY:
            if ch in text:
                return (f'「{label}」不能包含半角竖线或冒号（{ch}）。\n\n'
                        f'这两者会破坏服务器的响应格式，所以被禁止。\n'
                        f'需要分隔可以用空格、顿号或全角符号。')
        for ch in _ProfileBox.INVISIBLE_CHARS:
            if ch in text:
                return (f'「{label}」里有看不见的字符（零宽字符或方向控制符）。\n\n'
                        f'请删掉它们 —— 它们会让两个看起来一样的名字其实不相等。')
        return ''

    @staticmethod
    def decode_note(reply):
        """把 ``read_file`` 的答复解成**备注原文**。

        服务端把文件内容 base64 编码后放在 ``File: `` 后面，且**一个字节都不
        改写** —— 所以解出来就是用户当初写的那段文字。

        ⚠️ **三条返回值含义各不相同**，调用方必须分开处理：

        - ``None``：**读不到**（答复不是 ``File:`` 开头，例如网络错误 / 未登录）；
        - ``''``：还没有备注 —— 文件不存在（``'File:'``）**或**它是 0 字节。
          两者含义相同，都是**成功**；
        - 其余：备注原文。

        ⚠️ **任何情况下都不抛异常**：base64 解不开一律回 ``None``。
        ⚠️ 解码用 ``validate=True``：默认的 ``validate=False`` 会把字母表外的
        字符**直接丢掉**，于是 ``'!!!'`` 这种垃圾会被静默解成 ``b''``，与
        「空备注」混成一回事。

        ⚠️ **非 UTF-8 的处理与旧 ``UserInfo:`` 一路不同**：那边读的是许可记录里
        的 ``note`` 字段，解不出 UTF-8 只可能是数据坏了，所以如实回 ``None``。
        这里读的是**用户文件**，服务端允许存任意二进制 —— 但它同时又是我们的
        备注，界面只能显示文本。所以解不出 UTF-8 时按「读不到」处理（``None``），
        让框保持原样，而不是显示一串替换字符冒充备注。

        Args:
            reply: ``web_license.request(action='read_file',
                file_name='note.txt')`` 的答复正文（任意类型）。

        Returns:
            str | None: 备注原文 / 空串 / ``None``，见上。
        """
        text = reply if isinstance(reply, str) else str(reply or '')
        text = text.strip()
        if not text.startswith(_ProfileBox.SUCCESS_FILE):
            return _ProfileBox.NOTE_UNDECODABLE
        payload = text[len(_ProfileBox.SUCCESS_FILE):].strip()
        if not payload:
            # 文件不存在（服务端回 ``'File:'``）或内容是 0 字节 —— 都是「空备注」。
            return ''
        try:
            raw = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            return _ProfileBox.NOTE_UNDECODABLE
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            # 那个文件不是 UTF-8（用户文件本来就可以是任意二进制）——
            # 如实回报「读不到」，不要拿一个替换字符版冒充备注。
            return _ProfileBox.NOTE_UNDECODABLE

    @staticmethod
    def note_to_file_body(text) -> str:
        """把备注原文编成 ``write_file`` 要的 ``data_base64``。

        ★ ``write_file`` 收的是 **base64 编码后的字节**（v3.26 起见
        ``check.is_valid_base64``：只许标准字母表 ``[A-Za-z0-9+/=]``、非空、
        长度 ≤ 约 2.8 MB）。所以发之前必须自己编一次 —— 这与旧的
        ``update_user_info(note=…)`` 直接收原文**不同**，是本次改动最容易漏的
        一处：漏了就会收到 ``Bad request: "data_base64" is invalid``。

        ⚠️ **空串不能编**：``b64encode(b'')`` 得 ``''``，而空 ``data_base64``
        是 **400**（服务端刻意不把空值降级成删除）。要「清空备注」请走
        :meth:`LicenseRegister._clear_note_file`（``delete_file``）。

        Args:
            text: 备注原文（任意类型；非字符串按空串处理）。

        Returns:
            str: 标准 base64（ASCII）；``text`` 为空时返回空串（调用方据此
            改走删除，而不是发一个非法的空值）。
        """
        if not isinstance(text, str) or not text:
            return ''
        return base64.b64encode(text.encode('utf-8')).decode('ascii')

    @staticmethod
    def note_to_wire(text) -> str:
        """把备注框里的**多行文本**折成服务端能存住的**单行串**。

        ★ 这是「客户端把换行转成分隔符」那条取舍的落点：服务端会把换行压成
        空格（见 :data:`NOTE_LINE_SEP` 的说明），所以换行**必须**在这里换成
        显式分隔符，否则用户敲的换行会静默消失、几行连成一句。

        处理顺序（每一步都有理由）：

        1. 按 ``splitlines()`` 切行（它同时认 ``\\r\\n`` / ``\\r`` / U+2028）；
        2. 每行 ``strip()`` 并**丢掉空行** —— 用户顺手敲的空行不该变成一串 ``；``；
        3. 用 :data:`NOTE_LINE_SEP` 连接；
        4. 再交给 :meth:`fold_ws` 折叠行内的多余空白。

        ⚠️ **不能图省事用 ``split()`` 一把梭**：那会把换行与空格同等对待，结果
        就是 ``'a\\nb'`` → ``'a b'`` —— 正是要避免的那件事。

        Args:
            text: 备注框里的原始文本（任意类型；非字符串按空串处理）。

        Returns:
            str: 已折成单行的备注；没有任何内容时返回空串。
        """
        if not isinstance(text, str):
            return ''
        lines = [line.strip() for line in text.splitlines()]
        return _ProfileBox.fold_ws(
            _ProfileBox.NOTE_LINE_SEP.join(line for line in lines if line))

    @staticmethod
    def fold_ws(text) -> str:
        """把字符串里的控制字符压成空格、折叠连续空白、去首尾。

        与服务端的净化规则保持同一套 —— 本地先做一遍，是为了让「超长 / 带控制
        字符」这件事在**界面上当场**可见，而不是等一个网络往返之后由服务端
        悄悄改掉。

        Args:
            text: 原始字符串。

        Returns:
            str: 净化后的单行串。
        """
        if not isinstance(text, str):
            return ''
        cleaned = ''.join(ch if ord(ch) >= 32 else ' ' for ch in text)
        return ' '.join(cleaned.split())

    @staticmethod
    def note_of(widget) -> str:
        """从备注控件里取出**要发出去的**备注文本（已折成单行、已限长）。

        ⚠️ 备注是**多行**控件（``QPlainTextEdit``），取值用 ``toPlainText()``
        而**不是** ``text()`` —— 后者是 ``QLineEdit`` 的接口，混用会
        ``AttributeError``。包这一层，让调用处不必记住控件类型。

        Args:
            widget: 备注控件。

        Returns:
            str: 已折成单行、已限长的备注。
        """
        return _ProfileBox.note_to_wire(
            widget.toPlainText())[:_ProfileBox.MAX_NOTE_LEN]

    @staticmethod
    def set_note(widget, value) -> None:
        """把**服务端给的**备注写进多行控件。

        ⚠️ 服务端存的是单行（换行已被它压掉），直接 ``setPlainText`` 即可 ——
        多行控件显示单行内容不需要特殊处理。

        Args:
            widget: 备注控件。
            value: 服务端给的备注文本。
        """
        widget.setPlainText(str(value or '').strip())

    #: 三种形态的标识（:meth:`LicenseRegister._apply_mode` 的入参）。
    #:
    #: - ``MODE_UNKNOWN``：还没查到 / 查不到（断网）。**按未绑定渲染**，但保留
    #:   邮箱输入框可编辑，让用户能直接去注册；
    #: - ``MODE_REGISTER``：确认未绑定 —— 显示验证码那一行，主按钮是「注册并绑定本机」；
    #: - ``MODE_UPDATE``：确认已绑定 —— 藏起验证码那一行、邮箱只读，主按钮是
    #:   「更新信息」。
    MODE_UNKNOWN = 'unknown'
    MODE_REGISTER = 'register'
    MODE_UPDATE = 'update'

    #: 主按钮在两种形态下的文案（同一个按钮，只换字）。
    #: ⚠️ 界面上一律说「登录」：不提「注册」，也不提「绑定本机」——
    #:    绑定与授权是同义暗示，登录才是中性的。
    BUTTON_REGISTER = '登录'
    BUTTON_UPDATE = '更新信息'

    #: 顶部说明文字在两种形态下的文案。
    HINT_REGISTER = '用邮箱收一次验证码，即可完成登录。'
    HINT_UPDATE = '已登录，可直接修改下面的信息（留空 = 不改该项）。'
    #: ★ 用户正在改邮箱时（= 打算换绑）的说明文字。
    #: ⚠️ 必须**明说会连带改姓名 / 单位**：服务端的 ``_bind`` 在给了 ``user`` /
    #:    ``org`` 时会把它俩一并写到**新邮箱**那份授权上，用户不被告知就会
    #:    觉得「我只是换了个邮箱，名字怎么被动了」。
    HINT_REBIND = '正在更换邮箱：改好邮箱 → 发送验证码 → 点「登录」。'

    #: 已绑定形态下邮箱框的占位提示（**可点可改**，改了就进入换绑流程）。
    #:
    #: ⚠️⚠️ **这里不能置灰**：置灰就点不动了，换绑的入口也就没了 —— 上一版正是
    #: 把邮箱 ``setEnabled(False)``，于是**用户没有任何办法更换绑定邮箱**（真踩过）。
    #: 正确做法是「可编辑 + 一句说明」，让这条路自己浮出来。
    EMAIL_HINT_BOUND = '（已登录：要换邮箱请直接改这里）'
    EMAIL_HINT_FREE = 'you@example.com'

    @staticmethod
    def is_updated(text) -> bool:
        """判断答复是否为「资料已更新」。

        判据与 :func:`is_sent` **完全同一套**：去掉首尾空白后**只看开头**，
        不区分大小写。

        ⚠️ **不要**用 ``text == 'Updated'`` 严格相等：服务端将来在成功正文后
        追加说明段时，严格相等会静默把成功读成失败（这是本模块反复强调的
        隐含假设，:func:`_leading_word` 的文档里记了完整理由）。

        Args:
            text: ``web_license.request(action='update_user_info', …)`` 的答复。

        Returns:
            bool: 更新成功返回 True。
        """
        return _leading_word(text, _ProfileBox.SUCCESS_UPDATED)

    @staticmethod
    def is_file_written(text) -> bool:
        """判断答复是否为「文件已写入」（``write_file`` 的成功记号）。

        ⚠️ 与 :meth:`is_updated` 是**两个动作、两个记号**：备注改用用户文件接口
        之后，「写备注」走 ``write_file``（回 ``FileWritten``），而姓名 / 单位
        仍走 ``update_user_info``（回 ``Updated``）。拿 ``Updated`` 去判
        ``FileWritten`` **永远失败**，反之亦然。

        Args:
            text: ``web_license.request(action='write_file', …)`` 的答复。

        Returns:
            bool: 写入成功返回 True。
        """
        return _leading_word(text, _ProfileBox.SUCCESS_FILE_WRITTEN)

    @staticmethod
    def is_file_deleted(text) -> bool:
        """判断答复是否为「文件已删除」（``delete_file`` 的成功记号）。

        ⚠️ 删除**幂等**：「本来就没有」也回 ``FileDeleted``，所以它不区分
        「刚删掉」与「早就没有」—— 两者对「清空备注」这个目标状态是一样的。

        Args:
            text: ``web_license.request(action='delete_file', …)`` 的答复。

        Returns:
            bool: 删除成功返回 True。
        """
        return _leading_word(text, _ProfileBox.SUCCESS_FILE_DELETED)


class _Logout:
    """「在这台电脑上退出」用到的常量与判据（**纯命名空间，不实例化**）。

    ★ **为什么单独一个类**（而不是塞进 :class:`_ProfileBox`）：那个类的文档说的是
    「『更新信息』形态用到的常量」，而退出是**另一个动作**。按widget/AGENTS.md §2
    「命名空间类按主题拆」的约定分开放，两边都不必再解释自己为什么管着别人的东西。
    """

    #: 按钮的文案。
    #:
    #: ⚠️⚠️ **它只陈述「范围」（这台电脑），不吓人、也不暗示授权** —— 与模块头
    #: 「一律说登录、不说注册」那条措辞纪律同一个方向。**后果全部由确认框承担**
    #: （见 :data:`ASK`）。
    #: ⚠️ **不要**给它加「（重启软件后生效）」这类后缀：服务端的删除是**立即**的
    #: （``unbind.py`` 同步执行 ``delete_machine``），那句后缀会凭空给用户一个
    #: **并不存在的反悔窗口** —— 用户以为「还没生效、我还能改主意」，其实已经晚了。
    BUTTON = '在这台电脑上退出'

    #: 确认框的标题（它本身就是一个问句）。
    TITLE = '在这台电脑上退出？'

    #: 确认框的正文 —— ★★ **严重性全靠这里说清**。
    #:
    #: ⚠️⚠️ 按钮文案取得轻，所以这一个对话框是**唯一的承重墙**，三件事缺一不可：
    #:
    #: 1. **本机将回到未登录状态**；
    #: 2. **恢复要能收到那个邮箱的验证码** —— 邮箱已失效的用户**回不来**；
    #: 3. **只影响这一台** —— 登录邮箱、同一邮箱的其它电脑与到期日都不受影响。
    #:
    #: ⚠️ **刻意不写「本机将无法继续使用」**：内核侧按 feature 的成功结论是
    #: **进程内缓存**，本控件够不着、也清不掉，所以**本次运行**里已经查过的
    #: feature 仍可能照跑（见 :meth:`LicenseRegister._after_logout` 的说明）。
    #: 服务端那边确实已经解绑了，但客户端这句话**不能替内核打包票** ——
    #: 宁可少说，不说满。
    ASK = ('这台电脑将回到未登录状态，需要重新用邮箱收取验证码登录才能恢复。\n\n'
           '⚠️ 请确认你还能收到该邮箱的邮件。\n\n'
           '只影响这一台电脑 —— 登录邮箱、同一邮箱的其它电脑与到期日都不受影响。')

    #: 按钮的悬停提示（比确认框轻，只讲它做什么）。
    TIP = ('解除本机在服务端的登记，让这台电脑回到未登录状态。\n'
           '只影响这一台：登录邮箱与同一邮箱的其它电脑不受影响。\n'
           '⚠️ 恢复需要重新用邮箱收取验证码登录。')

    #: 服务端的成功记号（``unbind``，服务端 v3.20 起）。
    #:
    #: ⚠️⚠️ **它与 ``Bound`` 只差前缀，但机制上是安全的**：判定一律按**开头**
    #: 比较，``bound`` 匹配不上 ``unbound``（后者不以 ``bound`` 开头），所以
    #: :func:`is_bound` 与 :meth:`is_unbound` **互斥**，不会互相误判。
    SUCCESS = 'unbound'

    @staticmethod
    def is_unbound(text) -> bool:
        """判断答复是否为「已在这台电脑上退出」。

        ⚠️ **只认 ``Unbound`` 前缀**，绝不能用「不是错误就算成功」：服务端对
        **不认识的动作**会当成一次许可查询（**旧服务器**收到本动作正是如此），
        那时回的是 ``Yes | …``（或 ``Please register with your email first.``）
        —— 只认前缀才不会把它读成一次成功的退出。

        ⚠️ **不要**改用 :func:`is_bound`：``Unbound`` 不以 ``bound`` 开头，
        那样写会把**成功读成失败**。

        Args:
            text: ``web_license.unbind()`` 的答复（任意类型）。

        Returns:
            bool: 确实解绑了返回 True。
        """
        return _leading_word(text, _Logout.SUCCESS)


class _Pending:
    """耗时动作**进行中**时，横幅上显示的那句话（**纯命名空间，不实例化**）。

    ★★ **为什么值得单独管**：横幅平时显示的是**结论** —— 「已登录：某某」/
    「尚未登录：…」/「登录状态未知」。只有下面这三个时刻才临时改成**进行时**。

    ⚠️⚠️ **因此失败时必须把它收回来**（见 :data:`FAILED` 与
    :meth:`LicenseRegister._show_failure`）：否则横幅会永远停在「正在登录…」
    —— 一句早就不成立的话，而且用户会以为程序卡住了。这正是本模块一直在防的
    那类「界面说的和事实不一样」。

    ⚠️⚠️ **「正在登录…」只能用在 ``submit`` 真的在飞的那一段**，**绝不能**拿它
    当打开页面时的初值（:data:`CHECK`）：那时候软件**没有在登录**，它只是在**问**
    服务器「现在处于什么状态」。用「正在登录」会把三种情况全说歪 ——
    ① 本来就已登录 → 用户以为「它刚把我重新登录了一遍」；
    ② 本来未登录 → 用户以为「我登录失败了」（可他根本没尝试过）；
    ③ 断网 → 用户以为登录失败，其实是网络问题。
    """

    #: 打开页面 / 点「刷新」时的初值：**在问状态**，不是在做登录。
    CHECK = '正在确认登录状态…'

    #: ``submit`` 在飞（用户点了「登录」，**这一刻真的在登录**）。
    LOGIN = '正在登录…'

    #: 发验证码在飞（用户等的是邮件，多这一句就知道程序没卡住）。
    SEND_CODE = '正在发送验证码…'

    #: 上面那两个动作**失败**时，横幅改成什么。
    #:
    #: ⚠️ **按动作分开写**（而不是共用一句「操作失败」）：「没登进去」与
    #: 「验证码没发出去」对用户是两件事，下一步该做的也不同。
    #: ⚠️ 只列**会先把横幅改成进行时**的那两个动作。其余动作（退出 / 更新信息 /
    #: 查询）横幅里放的是**登录状态结论**，而那些状态并没有因为一次失败而改变 ——
    #: **不要**去动它，动了反而把界面上正确的那句话盖掉。
    FAILED = {'bind': '登录未成功（见下方服务器原话）。',
              'send_code': '验证码未发出（见下方服务器原话）。'}


class _Worker(QtCore.QThread):
    """在后台线程里跑一次网络调用（**绝不碰界面**）。

    Qt 的规则是「界面只能在主线程碰」，所以线程里只做请求，结果通过信号发回
    主线程。

    Attributes:
        finished_with: 信号，携带 ``(key, 状态码, 正文)``。
    """

    finished_with = QtCore.pyqtSignal(str, int, str)

    def __init__(self, key, func, parent=None):
        """初始化。

        Args:
            key: 这次调用的标识（发起方用来知道回来的是哪个请求）。
            func: 无参可调用对象，返回 ``(状态码, 正文)``。
            parent: Qt 父对象。
        """
        super().__init__(parent)
        self._key = key
        self._func = func

    def run(self):
        """线程体：执行调用并发回结果（**任何异常都要变成结果**）。

        真让异常逃出去的话，线程会静默死掉、``finished_with`` 永不发出，
        按钮就永远停在「禁用」状态 —— 看起来像程序卡死。
        """
        try:
            status, text = self._func()
        except Exception as err:
            status, text = -1, f'{type(err).__name__}: {err}'
        self.finished_with.emit(self._key, int(status), str(text))


class LicenseRegister(QtWidgets.QWidget):
    """软件登录控件：邮箱验证码 → 登录本机 → 自检登录状态。

    首次显示时会自动在后台查一次在线状态，若本机**已经绑定**过邮箱，就把那份
    授权里的姓名 / 单位 / 邮箱预填进输入框（见 :meth:`auto_query` /
    :meth:`_prefill`）。

    Attributes:
        machine_code: 本机硬件码（= ``web_license.machine_id()``）。
            ⚠️ **只用于内部判断**（空值 = zml.dll 没加载，按钮要禁用）——
            不显示、不复制、也不随请求发出。
    """

    def __init__(self, parent=None, *, machine_code=None, show_log=True):
        """初始化控件。

        Args:
            parent: Qt 父对象。
            machine_code: 硬件码；``None`` 表示用 ``web_license.machine_id()``
                （正常用法）。显式传入**只为测试**方便（可以伪造一台「没装 DLL
                的机器」）—— 它**不会**被显示，也**不会**被发给服务端。
            show_log: 是否显示可收起的日志区。关掉后 :meth:`_log` 只打印到
                标准输出，不再写界面。
        """
        super().__init__(parent)
        self.machine_code = str(machine_code if machine_code is not None
                                else fingerprint_sha()).strip()

        self._workers = {}      # key -> _Worker（持有引用，防被 GC）
        self._busy = False      # 有请求在飞 —— 所有按钮禁用
        self._show_log = bool(show_log)
        self._auto_checked = False   # 首次显示时的「查一次」是否已跑过
        # ★ 当前形态：先按「未绑定」渲染（注册是默认场景），查到结果后由
        #   _apply_mode 切。⚠️ 必须是**显式赋值**而不是让 _apply_mode 兜底 ——
        #   _apply_mode 在 mode 相同时直接 return，初值不对它就永远不执行。
        self._mode = _ProfileBox.MODE_UNKNOWN
        # ⚠️ 备注框的「正在就地截断」标记：_on_note_changed 里 setPlainText 会
        #    再次触发 textChanged，不加这个守卫就会递归。
        self._note_guard = False
        # ⚠️ 备注只取一次的闸门（见 _fetch_note）：它存在服务端的 note.txt 里，
        #    要单独起一个请求；不加闸门的话每次 _prefill 都会多一次往返。
        self._note_fetched = False
        # ★ **服务端当前存着的备注是什么**（``None`` = 还不知道 / 没读过）。
        #   用途只有一个：判断用户有没有真的动过备注（见 _note_pending_action），
        #   免得每次点「更新信息」都白发一趟写 / 删请求。
        #   ⚠️ 它是「服务端事实」的本地影子，只在 _after_note_fetched /
        #   _after_note_pushed 里更新 —— 与其他输入框同一条纪律（单出处）。
        self._note_dirty = None
        # ★ **当前绑定的邮箱**（服务端那份授权里的 Email），空 = 还不知道 / 未绑定。
        #   用途只有一个：判断用户有没有把邮箱改掉（改掉 = 想换绑，见
        #   _on_email_edited）。⚠️ 它是「服务端事实」的本地影子，所以只在
        #   _prefill 里更新 —— 与其他输入框同一条纪律（单出处）。
        self._bound_email = ''

        self._build_ui()
        if not self.machine_code:
            self._log('错误：硬件码为空，zml.dll 可能没加载成功，无法登录')
        # ⚠️ 显式按「未绑定」渲染一次：_mode 初值是 MODE_UNKNOWN，与目标值不同，
        #    所以这一次 _apply_mode 真的会跑（而不是被「相同就 return」挡掉）。
        self._apply_mode(_ProfileBox.MODE_REGISTER)
        self._update_buttons()

    def showEvent(self, event):
        """控件首次显示时，在后台查一次在线状态（并顺手预填输入框）。

        ⚠️ 放在 :meth:`showEvent` 而不是 ``__init__``：本控件由 TabWidget
        **创建后立刻挂到标签页**，不一定马上显示；而且构造期间起网络线程会让
        「打开窗口」这件事变得不可预期。用 :attr:`_auto_checked` 保证**只跑
        一次** —— 切换标签页会反复触发本事件，不能每次都发一次请求。

        ⚠️ 请求本身在后台线程（:class:`_Worker`），所以显示过程不会被 60 秒的
        网络超时卡住；期间按钮会短暂禁用（与手动「刷新状态」同一套编排）。

        Args:
            event: Qt 显示事件。
        """
        super().showEvent(event)
        # ⚠️ **每次显示都重算一次按钮可用性**：退出按钮的判据里含「有没有计算
        #    在跑」，而那个状态**不会**经 _set_busy 通知本控件 —— 用户完全可能
        #    在计算已经开始之后才切到本页，那时按钮不该还亮着（见 _update_buttons）。
        #    这一句只是几个布尔判断，所以放在下面那个早退**之前**。
        self._update_buttons()
        if self._auto_checked:
            return
        self._auto_checked = True
        # ⚠️ 延后一拍再发请求：showEvent 期间控件还没画出来，此时 _set_busy
        #    禁用按钮属于「显示前改状态」，某些平台会看到按钮闪一下。
        QtCore.QTimer.singleShot(0, self.auto_query)

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------

    def _build_ui(self):
        """搭出整个界面（只在这里创建控件）。

        结构上刻意**不用 QGroupBox 画框**：那圈带标题的凹陷边框是办公软件的
        老样子，一屏套三个框显得很碎。改用「留白 + 一条细线」表达分组 ——
        分组的语义靠标题与间距承担，不靠画框。

        ⚠️ **内容全部塞进一个纵向滚动区**（见 :meth:`_build_scroll_area`）：
        本控件被 :meth:`zmlx.ui.main.TabWidget.get_widget` 直接 addTab 到标签页，
        标签页会把控件的最小高度算进自身 —— 控件内容一多（尤其是展开「服务器
        原始答复」与「日志」之后），就会**把标签页甚至主窗口撑高**，挤掉别的
        控件。放进滚动区后，控件的最小高度不再由内容决定（``QScrollArea``
        自己就是可压缩的），窗口再小也只会出现滚动条。
        """
        self.setWindowTitle('软件登录')

        # 顶层只有滚动区一个孩子；内容的高度诉求到此为止，不再往上传。
        shell = QtWidgets.QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self._build_scroll_area())

    def _build_scroll_area(self):
        """纵向滚动区：把整块内容装进去，避免撑住上一级控件。

        Returns:
            QtWidgets.QScrollArea: 已配置好的滚动区。
        """
        scroll = QtWidgets.QScrollArea()
        # ⚠️ 必须为 True：否则内容控件会保持自己的「建议尺寸」，
        #    窗口变宽时表单不会跟着拉伸，右边留一片空白。
        scroll.setWidgetResizable(True)
        # 只要纵向滚动条：横向内容本来就是自适应的，出现横向条只会让人困惑。
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidget(self._build_content())
        return scroll

    def _build_content(self):
        """滚动区里的实际内容（原来的整块界面）。

        Returns:
            QtWidgets.QWidget: 含标题、横幅、表单、答复区与日志的容器。
        """
        content = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(content)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        outer.setSpacing(GAP)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_status_banner())
        outer.addWidget(self._separator())
        outer.addWidget(self._build_form())
        outer.addWidget(self._build_status_detail())
        if self._show_log:
            outer.addWidget(self._build_log_box())
        # ⚠️ 末尾的弹簧**必须留**：滚动区把内容拉到满高时，它保证各块仍然
        #    从顶部依次排列，而不是被均匀撑开（那会让行距忽大忽小）。
        outer.addStretch(1)
        return content

    def _build_header(self):
        """顶部标题区（取代原先 QGroupBox 的标题）。

        Returns:
            QtWidgets.QWidget: 含大标题与一句说明的容器。
        """
        box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title = QtWidgets.QLabel('登录')
        font = title.font()
        font.setPointSize(font.pointSize() + 5)     # 相对放大，不写死磅值
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        hint = QtWidgets.QLabel(_ProfileBox.HINT_REGISTER)
        hint.setWordWrap(True)
        hint.setEnabled(False)      # 置灰跟随主题，不写死颜色
        layout.addWidget(hint)
        # ★ 留着引用：已绑定时这句说明要跟着换（见 _apply_mode）—— 否则界面会
        #   自相矛盾（下面已经是「更新信息」，上面还写着「用邮箱收验证码」）。
        self.hint_label = hint
        return box

    def _build_status_banner(self):
        """顶部「一句话状态」提示条（右端带「在这台电脑上退出」按钮）。

        这里**只放一句话 + 一个次要动作**；原始的服务器报文收进下面的可折叠详情
        （:meth:`_build_status_detail`）—— 日常使用时用户只需要知道
        「能用 / 不能用 / 还没登录」，以及（已登录时）从哪里退出。

        ★ **退出按钮放在这一行最右侧**：它属于「状态」这条信息的一部分
        （「你以谁的身份登录着」→「不想要了就在这里退出」），放在别处会让
        用户先去别的地方找。

        ⚠️⚠️ **边框必须用「带 objectName 的选择器」限定在容器上**：
        :data:`BANNER_QSS` 是**无选择器的裸声明**（``border: …``），而 Qt 的
        ``setStyleSheet`` 会**级联到子控件** —— 直接把它设到容器上，里面的标签与
        按钮会各自长出一圈边框，看起来像三个挤在一起的框。

        Returns:
            QtWidgets.QWidget: 状态提示条（含退出按钮）。
        """
        self.status_label = QtWidgets.QLabel(_Pending.CHECK)
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(10, 7, 10, 7)

        # ★ 「在这台电脑上退出」：**只在确实已登录时可见**（由 _show_status 决定）。
        #   ⚠️ 做成**扁平次要按钮**：它不常做、后果也不小，不该与主按钮抢视觉
        #   重心；与「刷新登录状态」同一档（那个也是 setFlat(True)）。
        #   ⚠️ 不写任何色值 —— 颜色一律交给主题（见模块文档）。
        self.logout_button = QtWidgets.QPushButton(_Logout.BUTTON)
        self.logout_button.setFlat(True)
        # 与状态栏那个按钮同样的取舍：它是「点一下就走」的动作，
        # 抢键盘焦点只会让回车误触发它（主按钮才是 setDefault 的那个）。
        self.logout_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.logout_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.logout_button.setToolTip(_Logout.TIP)
        self.logout_button.clicked.connect(self.logout)
        # 初值：还没查过，先不显示（查到「已登录」时由 _show_status 打开）
        self.logout_button.setVisible(False)

        banner = QtWidgets.QWidget()
        banner.setObjectName('statusBanner')
        banner.setStyleSheet(f'#statusBanner {{ {BANNER_QSS} }}')
        row = QtWidgets.QHBoxLayout(banner)
        # ⚠️ 右边留 8：扁平按钮自己几乎不留边距，不留的话它看上去会贴着边框。
        row.setContentsMargins(0, 0, 8, 0)
        row.setSpacing(6)
        # 文字吃掉全部剩余宽度（它可能换行），按钮只占自己那一份并垂直居中 ——
        # 这样横幅换行时按钮不会跟着上下跳。
        row.addWidget(self.status_label, 1)
        row.addWidget(self.logout_button, 0,
                      QtCore.Qt.AlignmentFlag.AlignVCenter)
        return banner

    def _build_status_detail(self):
        """「服务器原始答复」可折叠区（**默认展开**）。

        默认展开是有意的：这一块现在只有两行（原始字符串 + 往返耗时），内容很短，
        收起反而让用户多点一次才能看到连接速度。用它排错时也总是要看的。

        Returns:
            QtWidgets.QGroupBox: 可勾选的容器（勾选 = 展开，扁平样式）。
        """
        box = QtWidgets.QGroupBox('服务器原始答复')
        box.setCheckable(True)
        box.setChecked(True)        # 默认展开（再次点击标题可收起）
        box.setFlat(True)           # 去掉会与卡片风格重复的那条标题线
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)

        self.status_view = QtWidgets.QPlainTextEdit()
        self.status_view.setReadOnly(True)
        # 只有「原始字符串 + 耗时」两行，所以固定成两行高即可，不必留大片空白
        self.status_view.setFixedHeight(STATUS_VIEW_HEIGHT)
        self.status_view.setPlaceholderText(
            '查询后这里显示服务器的原话，以及本次往返耗时。')
        layout.addWidget(self.status_view)

        box.toggled.connect(self.status_view.setVisible)
        self.status_view.setVisible(True)
        return box

    def _build_form(self):
        """表单区：姓名 / 单位 / 备注 / 邮箱 / 验证码 + 主按钮。

        ★ **只有这一套输入框**（单出处原则，见模块文档）：无论是「注册」还是
        「更新信息」形态，都用这几个框 —— 形态之间只切**可见性与文案**，
        绝不另建第二组控件。

        ⚠️ 几个 ``*_row`` / ``*_label`` 的引用必须留着：:meth:`_apply_mode`
        要靠它们把「验证码」那一**整行**（标签 + 输入框）藏起来 —— 只藏输入框
        会留下一个孤零零的标签，看起来像界面坏了。

        ⚠️ ``QFormLayout`` 的 ``setRowVisible`` 是 **Qt 6.4+** 才有的。取不到时
        退化成「分别隐藏标签与控件」（见 :meth:`_set_row_visible`），两条路都
        要能跑 —— 本仓库同时支持 PyQt5 / PyQt6。

        Returns:
            QtWidgets.QWidget: 配置好的表单。
        """
        box = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(box)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(GAP)
        # 标签右对齐：与输入框形成一条整齐的竖线，比默认的左对齐耐看
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                               QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._form = form

        # 姓名与单位：注册时**必填**（见 _require_identity）；更新时选填。
        # 作用是让作者认得出这份授权是谁、哪个单位的。
        self.user_edit = QtWidgets.QLineEdit()
        self.user_edit.setPlaceholderText('必填，例如：张三')
        self.user_edit.setMaxLength(MAX_USER_LEN)
        self.user_edit.setToolTip(
            '姓名：登录时必填，供作者知道是谁在用。\n'
            '（漏填之后就补不回来了，所以登录时拦住；登录后随时可改。）')
        form.addRow('姓名', self.user_edit)

        self.org_edit = QtWidgets.QLineEdit()
        self.org_edit.setPlaceholderText('必填，例如：XX大学 / XX研究院')
        self.org_edit.setMaxLength(MAX_ORG_LEN)
        self.org_edit.setToolTip('单位：登录时必填，作用同姓名。')
        form.addRow('单位', self.org_edit)

        # 备注：**注册时也可以直接填**（选填），且是**多行**框。
        # ⚠️ 但 submit 的请求体里**没有**备注 —— 所以填了它时，控件会在
        #    注册成功后**自动补一次** write_file（见 _push_pending_note）。
        #    这一步对用户是透明的。
        # ⚠️ 用 QPlainTextEdit（多行）而不是 QLineEdit：备注是唯一一个「用户可能
        #    想多说几句」的字段。取值必须用 toPlainText()（见 _ProfileBox.note_of）。
        self.note_edit = QtWidgets.QPlainTextEdit()
        self.note_edit.setPlaceholderText('选填，可以写多行，例如：博士生 / 用途说明')
        self.note_edit.setFixedHeight(_ProfileBox.NOTE_HEIGHT)
        # ⚠️ 多行控件**没有** setMaxLength，所以长度靠两处兜：① set_note 时截断；
        #    ② 输入时就地拦（见 _on_note_changed），否则用户敲超了却毫无提示，
        #    发出去被服务端截断 —— 他会以为全存进去了。
        self.note_edit.textChanged.connect(self._on_note_changed)
        # ⚠️ **备注从 2026-10 起存在服务端的 ``note.txt`` 里**（用户文件接口），
        #    不再是许可记录里的 ``note`` 字段 —— 所以它**不会**再覆盖注册时那句
        #    出处标记（上一版会，那时两者是同一个字段）。
        #    ⚠️ 仍要告诉用户「换行会被折成分号」：那是**本地**的折行（见
        #    note_to_wire），与存到哪儿无关。
        self.note_edit.setToolTip(
            '备注（选填）：可以写多行，会一并保存，供作者参考。\n'
            '它存在服务端的独立文件里，不影响你的登录信息。\n'
            f'（保存时换行会折成「{_ProfileBox.NOTE_LINE_SEP}」。\n'
            '清空这个框并保存，会删掉服务端那份备注。）')
        form.addRow('备注', self.note_edit)

        email_row = QtWidgets.QHBoxLayout()
        email_row.setSpacing(GAP)
        self.email_edit = QtWidgets.QLineEdit()
        self.email_edit.setPlaceholderText('you@example.com')
        self.email_edit.returnPressed.connect(self.send_code)
        # ★★ 改动邮箱 = 想换绑 -> 立刻切回注册形态（见 _on_email_edited）。
        #    ⚠️ 用 textEdited 而不是 textChanged：前者**只在用户真的敲键盘时**发，
        #    后者在我们自己 setText 预填时也会发 —— 那会让「刚查完就被切成注册
        #    形态」，界面自己把自己翻乱。
        self.email_edit.textEdited.connect(self._on_email_edited)
        email_row.addWidget(self.email_edit, 1)

        self.send_button = QtWidgets.QPushButton('发送验证码')
        self.send_button.setToolTip(
            '向该邮箱发送 6 位验证码（有效期一天，10 分钟内只能发一次）。\n'
            '登录与信息更新共用这一个动作。')
        self.send_button.clicked.connect(self.send_code)
        email_row.addWidget(self.send_button)
        form.addRow('邮箱', email_row)
        # ⚠️ 只记「发送验证码」这个按钮：邮箱标签在更新形态下**不**隐藏
        #    （用户要看得见自己在用哪个邮箱），只是输入框变只读。
        self.email_label = form.labelForField(self.email_edit)

        self.code_edit = QtWidgets.QLineEdit()
        self.code_edit.setPlaceholderText('邮件里收到的 6 位数字')
        self.code_edit.setMaxLength(6)
        self.code_edit.returnPressed.connect(self.register)
        form.addRow('验证码', self.code_edit)
        # 这两个引用专供 _apply_mode 整行隐藏用
        self.code_label = form.labelForField(self.code_edit)

        # 主按钮通栏并加高：一屏只让一个「最该点的按钮」跳出来。
        # ★ 同一个按钮在两种形态下只换**文案**与**点击后干的事**（见
        #   _on_primary_clicked / _apply_mode），不另建一个按钮。
        self.register_button = QtWidgets.QPushButton(
            _ProfileBox.BUTTON_REGISTER)
        self.register_button.setMinimumHeight(BUTTON_HEIGHT)
        self.register_button.setDefault(True)
        self.register_button.setToolTip(
            '用验证码把本机与该邮箱关联起来。\n'
            '邮箱若从未登录过，会顺手为它完成登录。\n'
            '登录成功后即可正常使用本软件。')
        self.register_button.clicked.connect(self._on_primary_clicked)
        form.addRow('', self.register_button)

        # 「刷新状态」挪到表单末尾、注册按钮下面，样式上与主按钮拉开
        # （它是辅助动作，原先却和主按钮平级放在状态框顶部）。
        refresh_row = QtWidgets.QHBoxLayout()
        refresh_row.setSpacing(GAP)
        refresh_row.addStretch(1)
        self.check_button = QtWidgets.QPushButton('刷新登录状态')
        self.check_button.setFlat(True)     # 扁平 = 视觉上的次级按钮
        self.check_button.setToolTip(
            '重新查一次本机的登录状态。\n'
            '强制重新连服务器（read_cache=False），不用缓存里的旧结果。')
        self.check_button.clicked.connect(self.refresh_status)
        refresh_row.addWidget(self.check_button)
        form.addRow('', refresh_row)
        return box

    def _build_log_box(self):
        """可收起的「日志」那一块。
        Returns:
            QtWidgets.QGroupBox: 配置好的分组框（默认收起，扁平样式）。
        """
        box = QtWidgets.QGroupBox('日志（排错用）')
        box.setCheckable(True)
        box.setChecked(False)
        box.setFlat(True)
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)     # 别让日志无限涨
        layout.addWidget(self.log_view)

        # QGroupBox 可勾选时，未勾选 = 收起
        box.toggled.connect(self.log_view.setVisible)
        self.log_view.setVisible(False)
        return box

    @staticmethod
    def _separator():
        """一条细分隔线（代替分组框的边框来划分区域）。

        Returns:
            QtWidgets.QFrame: 水平细线。
        """
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        return line

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------

    def set_machine_code(self, machine_code):
        """换一个硬件码（一般不用；正常应当来自 ``web_license.machine_id()``）。

        它只影响「这台机器能不能发请求」这一判断（空 = 不能），界面上没有
        任何东西会跟着变。

        Args:
            machine_code: 新的硬件码；空值直接忽略（空硬件码没有意义）。
        """
        value = str(machine_code or '').strip()
        if not value:
            return
        self.machine_code = value
        self._update_buttons()

    def closeEvent(self, event):
        """窗口关闭时等后台请求收尾，避免线程还在跑时对象被销毁。

        ⚠️ **本方法只覆盖「控件被单独 close()」这一条路径**（例如直接运行
        :func:`test_1`）。走**标签页关闭**（``TabWidget.close_tab``）时用的是
        ``deleteLater()``，**不发** ``closeEvent`` —— 那条路径由
        :meth:`cleanup_before_tab_close` 负责，两者缺一不可。

        ⚠️ ``wait(3000)`` 只是「给 3 秒收尾」，兜不住长请求（最长 60 秒）：
        所以线程本身没有 parent、能活到自然结束（见 :data:`_RUNNING_WORKERS`），
        这里等待只是让**正常收尾**的情况更干净。

        Args:
            event: Qt 关闭事件。
        """
        for worker in list(self._workers.values()):
            if worker.isRunning():
                worker.wait(3000)
        event.accept()

    # ------------------------------------------------------------------
    # 槽函数（界面回调）
    # ------------------------------------------------------------------

    def _on_primary_clicked(self):
        """主按钮被点：按当前形态分发到 :meth:`register` 或 :meth:`update_info`。

        ★ **同一个按钮、两种行为**（文案由 :meth:`_apply_mode` 换）：未绑定时是
        「注册并绑定本机」，已绑定时是「更新信息」。

        ⚠️ **不要在 ``clicked`` 上直接连 :meth:`register`**：那样已绑定状态下
        点按钮会去走注册（要求验证码），而验证码那一行此时是藏着的 —— 用户会
        遇到「点了一个按钮，它要我填一个看不见的框」。
        """
        if self._mode == _ProfileBox.MODE_UPDATE:
            self.update_info()
        else:
            self.register()

    def send_code(self):
        """「发送验证码」：调 ``web_license.send_code``（服务端 ``send_code`` 动作）。

        姓名与单位**在发码之前就要先填好**（见 :meth:`_require_identity`）：服务端
        的发码动作并不需要它们，但这份授权一旦由本次注册创建，署名就定下来了
        —— 让用户在收到邮件之后再发现「还得回去补名字」，多半就是漏填着提交。

        ⚠️ 已绑定形态下这个按钮是**藏着的**（改资料不需要验证码），所以本方法
        正常只会从未绑定形态被调到。
        """
        user = self._require_identity()
        if user is None:
            return
        email = self._require_email()
        if email is None:
            return

        self._log(f'请求发送验证码：{email}（姓名={user}）')
        # ⚠️ 横幅改成「正在发送验证码…」：用户等的是邮件，这一步最长 60 秒
        #    （服务端要走一次完整的 SMTP 会话）。⚠️ 失败时由 _show_failure 收回。
        self.status_label.setText(_Pending.SEND_CODE)
        self._start(
            'send_code',
            # ⚠️ web_license.send_code **不抛异常**：连不上 / 服务端报错都以正文返回，
            #    所以这里直接给状态位 True（「拿到答复了」），判定看正文。
            lambda: (True, web_license.send_code(email, purpose=PURPOSE_BIND)),
            on_ok=lambda status, text: self._after_sent(email))

    def register(self):
        """「注册并绑定本机」：调 ``web_license.submit``。

        ⚠️ 机器码由 ``web_license.submit`` **在 C++ 侧自己算**，控件不传也传不了：
        少传一个值就少一类「传错了却每一步都成功」的故障。

        姓名（``user``）与单位（``org``）是**必填**的（见
        :meth:`_require_identity`）：任一为空就直接拦下，连请求都不发。

        ★ **备注不进这个请求**：``submit`` 的请求体里没有 ``note`` 字段，所以
        备注由 :meth:`_after_bound` 在注册成功后**自动补一次**
        （:meth:`_push_pending_note`）—— 对用户是透明的。
        """
        user = self._require_identity()
        if user is None:
            return
        email = self._require_email()
        if email is None:
            return

        user, org = user
        # ★ 这两个字段由**服务端严格拒绝**（含 ``|`` / ``:`` / 零宽字符就 400），
        #    所以本地先查一遍（省一次往返、也能当场说清是哪一项）。
        #    ⚠️ **不做客户端转义** —— 那套已整体删除。
        for label, value in (('姓名', user), ('单位', org)):
            problem = _ProfileBox.validate_identity(label, value)
            if problem:
                self._warn('有不能使用的字符', problem)
                return

        code = self.code_edit.text().strip()
        if not (len(code) == 6 and code.isascii() and code.isdigit()):
            self._warn('验证码不正确', '请填写邮件里收到的 6 位数字验证码。')
            return

        if not self.machine_code:
            self._warn('无法绑定', '本机硬件码为空（zml.dll 未加载？），无法绑定。')
            return

        self._log(f'请求绑定：email={email} user={user} org={org}'
                  f'（机器码由 C++ 侧自算）')
        # ★★ 横幅改成「正在登录…」—— **这一刻是真的在登录**（用户刚点了「登录」，
        #    ``submit`` 正在飞，最长 60 秒）。⚠️ 失败时由 _show_failure 把它收回来
        #    （见 _Pending.FAILED），否则会永远停在这一句。
        self.status_label.setText(_Pending.LOGIN)
        self._start(
            'bind',
            # ⚠️ 同上：不抛异常，失败以正文返回。
            lambda: (True, web_license.submit(email, code, user=user, org=org)),
            on_ok=self._after_bound)

    def _free_text_fields(self):
        """取出两个**身份字段**（姓名 / 单位），已净化 + 已限长。

        ★★ **这是这两个字段发出去之前的唯一出口**。
        ⚠️ **本地不做任何转义 / 编码**：``user`` / ``org`` 由服务端**严格拒绝**
        （本地只做一次快速校验）。

        ⚠️ **备注不在这里**：它已经改用**用户文件**接口（``write_file`` 写
        ``note.txt``），取值 / 编码 / 限长的路子与这两个都不同，见
        :meth:`_ProfileBox.note_of` 与 :meth:`_ProfileBox.note_to_file_body`。
        把它们混在一个函数里会让「谁走哪个动作」变得看不出来。

        Returns:
            dict: ``{'user': …, 'org': …}``，未填的项是空串
            （调用方据此「整段不发」那个字段）。
        """
        return {
            'user': self.user_edit.text().strip()[:MAX_USER_LEN],
            'org': self.org_edit.text().strip()[:MAX_ORG_LEN],
        }

    def update_info(self):
        """「更新信息」：姓名 / 单位走 ``update_user_info``，备注走文件接口。

        ★★ **本方法现在最多发两次请求，因为它们落在两个不同的服务端动作上**：

            ========  ==========================  ==================
            界面项      服务端动作                   成功记号
            ========  ==========================  ==================
            姓名/单位   ``update_user_info``        ``Updated``
            备注        ``write_file`` / ``delete_file``  ``FileWritten`` / ``FileDeleted``
            ========  ==========================  ==================

        ⚠️ **为什么备注不再跟着 ``update_user_info`` 走**：备注已改存用户文件
        ``note.txt``（见 :data:`_ProfileBox.NOTE_FILE_NAME`），而那两个文件动作
        是**各自独立**的服务端动作 —— 名字 / 单位那份请求里带不上它。

        ⚠️ **顺序：先身份、后备注**。理由与 :meth:`_after_bound` 同一条 ——
        身份那一步可能被服务端拒绝（例如姓名含 ``|``），而备注**没有任何理由
        陪葬**。两步各自独立成败，也各自记日志。

        ★ **不需要验证码**：两个动作都以机器码为凭证（与「提交反馈」同一
        信任级），所以本方法既不读 ``code_edit``、也不碰发码按钮。

        ★ **机器码由 C++ 侧自己算**（``web_license`` 在拼请求体时补上 ``machine_id``），
        控件不传也传不了 —— 与 :meth:`register` 同一条设计。这里的
        :attr:`machine_code` 只当「zml.dll 可用吗」的探针。

        ⚠️ **姓名 / 单位「留空 = 不改」**（服务端契约）：所以下面**必须真的删键**，
        不能发一个空串出去 —— 服务端把「空串」也当没给，但不发更干净。

        ⚠️ **备注「留空 = 删除」**（★ 与身份字段语义**相反**，这是本次改动的
        刻意选择）：备注框被清空时，服务端那份 ``note.txt`` 会被
        ``delete_file`` 删掉 —— 否则用户删光了备注一保存，下次刷新它又冒出来。
        ⚠️ 之所以能这么做，是因为 ``delete_file`` 是**单独一个动作**；
        ``write_file`` 收空值仍然是 400（服务端刻意不让空值降级成删除）。

        ⚠️ **邮箱不参与**：两个动作都绝不动 ``email``（身份字段），所以请求体里
        都**没有** email 字段。
        """
        if not self.machine_code:
            self._warn('无法更新', '本机硬件码为空（zml.dll 未加载？），无法更新。')
            return

        # ★ 先校验姓名 / 单位（服务端对这两个字段严格拒绝）。
        #   ⚠️ **空值不用校验**：更新模式下「留空 = 不改」，空串根本不会发出去。
        for label, edit in (('姓名', self.user_edit), ('单位', self.org_edit)):
            value = edit.text().strip()
            if not value:
                continue
            problem = _ProfileBox.validate_identity(label, value)
            if problem:
                self._warn('有不能使用的字符', problem)
                return

        # ⚠️ 限长与去空白在 :meth:`_free_text_fields` 一处做（见那里）。
        values = self._free_text_fields()
        # ⚠️ 空串 = 不改这一项 -> **整段不发这个字段**。
        fields = {key: value for key, value in values.items() if value}

        # ★ 备注：非空 -> 写文件；空 -> 删文件（但**只在框里本来有东西**时才删，
        #   否则每次点「更新信息」都会白发一个删除请求）。判据用「服务端那份
        #   是什么」而不是「框是不是空的」—— 见 _note_dirty。
        note = _ProfileBox.note_of(self.note_edit)
        note_action = self._note_pending_action(note)

        if not fields and note_action is None:
            self._warn('还差一点', '请至少填写一项（姓名 / 单位 / 备注）。\n\n'
                       '留空的项不会被改动。')
            return

        self._log(f'请求更新信息：{sorted(fields)}'
                  f'（备注：{note_action or "无改动"}；机器码由 C++ 侧自算）')
        self._start(
            'update_info',
            # ⚠️ web_license.request **不抛异常**：连不上 / 服务端报错 / 旧 DLL
            #    缺 lic_request 都以一句正文返回，所以状态位恒给 True，
            #    判定看正文（与 send_code / bind 两路同一条做法）。
            #
            # ⚠️⚠️ **没有身份字段要改时，直接回一个合成的 ``Updated``** —— 否则
            #    ``update_user_info`` 会收到一个空请求体并被判 400。它的形状必须
            #    与 ``_Worker`` 的契约一致：``(状态位, 正文)``，正文是 **str**。
            #    ⚠️ **括号要包住整个三元表达式**：写成
            #    ``(True, web_license.request(...) if fields else (True, '...'))``
            #    会把三元放进元组里，于是 ``when fields`` 为空时正文变成一个
            #    **元组** ``(True, 'Updated')``，``is_updated()`` 必然判失败 ——
            #    界面上表现为「明明存成了却报『更新信息失败』」（真踩过）。
            lambda: (True, web_license.request(
                action='update_user_info', **fields)) if fields
            else (True, _ProfileBox.SUCCESS_UPDATED),
            on_ok=lambda s, t: self._after_identity_saved(s, t, note_action, note))

    def _note_pending_action(self, note):
        """本次「更新信息」对备注该做什么：写、删、还是不动。

        ★★ **判据是「服务端那份是什么」而不是「框是不是空的」**，否则每次点
        「更新信息」都会白发一个请求（含一次网络往返），而绝大多数点击根本没
        碰备注。

        三种结果：

        - ``'write'`` —— 框里有内容，且与服务端那份**不同**（比对下方那个
          ``stored``）；
        - ``'delete'`` —— 框是空的，而服务端**确实存着**一份备注（用户删光了
          它，要让它真的消失）；
        - ``None`` —— 无需动作（框空且服务端也没有；或内容与已存的一模一样）。

        ⚠️ **``_note_dirty`` 的语义**：它记着「服务端那份是什么」。窗口期内它
        可能不准（例如读备注那一趟还没回来），此时**按「要发」处理** ——
        多发一次幂等的写，好过静默吞掉用户刚敲的备注。

        Args:
            note: 备注框里当前的备注（已折行、已限长）。

        Returns:
            str | None: ``'write'`` / ``'delete'`` / ``None``。
        """
        stored = self._note_dirty
        if note:
            # 与服务端那份相同就不发（省一次往返）。
            if stored is not None and note == stored:
                return None
            return 'write'
        # 框是空的：只有服务端确实存着东西时才需要删。
        if stored:
            return 'delete'
        return None

    def _after_identity_saved(self, status, text, note_action, note):
        """姓名 / 单位那一趟回来了：成功才接着处理备注。

        ⚠️ **身份那一步失败时不再发备注那一趟**：用户看到的是「更新失败」，
        此时偷偷把备注写进去只会让状态更难解释；而且他多半会改完再点一次，
        那时备注会跟着一起走。

        Args:
            status: 状态位。
            text: ``update_user_info`` 的答复（``Updated``）。
            note_action: :meth:`_note_pending_action` 的结论。
            note: 备注原文。
        """
        # ⚠️ 没有身份字段要改时，上面那个 lambda 直接回了一个合成的
        #    ``'Updated'`` —— 那条路必然成功，照常往下走。
        if not _ProfileBox.is_updated(text):
            self._show_failure('update_info', status, text)
            return
        if note_action is None:
            self._after_saved(True, text)
            return
        self._push_note_change(note_action, note)

    def _push_note_change(self, action, note):
        """把备注的改动发出去：``write`` 写文件、``delete`` 删文件。

        ⚠️ **两处编码上的不对称**（最容易踩的一处）：

        - ``write_file`` 收的是 **base64 编码后**的 ``data_base64``；
        - ``delete_file`` 只收 ``file_name``，**不碰内容**。

        ⚠️ **失败不清空输入框**：写失败时把备注留在框里，用户再点一次即可。

        Args:
            action: ``'write'`` 或 ``'delete'``。
            note: 备注原文（``'delete'`` 时忽略）。
        """
        if action == 'delete':
            self._log('备注已清空：删除服务端的 note.txt')
            self._start(
                'note_write',
                lambda: (True, web_license.request(
                    action='delete_file',
                    file_name=_ProfileBox.NOTE_FILE_NAME)),
                # ⚠️ 传 finalize：这一趟跑完才算「更新信息」整体结束
                #    （由 _after_saved 弹「已更新」）。
                on_ok=lambda s, t: self._after_note_pushed(
                    s, t, finalize=self._after_saved))
            return

        body = _ProfileBox.note_to_file_body(note)
        if not body:
            # ⚠️ 理论上到不了这里（``note`` 非空时 b64encode 必然非空）——
            #    但空 ``data_base64`` 会换来一个 400，所以宁可就地停住。
            self._log('备注没发出去：编码后为空')
            self._after_saved(True, _ProfileBox.SUCCESS_UPDATED)
            return
        self._log(f'备注有改动（{len(note)} 字），写入服务端的 note.txt')
        self._start(
            'note_write',
            lambda: (True, web_license.request(
                action='write_file',
                file_name=_ProfileBox.NOTE_FILE_NAME,
                data_base64=body)),
            on_ok=lambda s, t: self._after_note_pushed(
                s, t, finalize=self._after_saved))

        # ★ 先校验姓名 / 单位（服务端对这两个字段严格拒绝）。
        #   ⚠️ **空值不用校验**：更新模式下「留空 = 不改」，空串根本不会发出去。
        for label, edit in (('姓名', self.user_edit), ('单位', self.org_edit)):
            value = edit.text().strip()
            if not value:
                continue
            problem = _ProfileBox.validate_identity(label, value)
            if problem:
                self._warn('有不能使用的字符', problem)
                return

        # ⚠️ 限长与去空白在 :meth:`_free_text_fields` 一处做（见那里）。
        values = self._free_text_fields()
        # ⚠️ 空串 = 不改这一项 -> **整段不发这个字段**。
        fields = {key: value for key, value in values.items() if value}
        if not fields:
            self._warn('还差一点', '请至少填写一项（姓名 / 单位 / 备注）。\n\n'
                       '留空的项不会被改动。')
            return

        self._log(f'请求更新信息：{sorted(fields)}（机器码由 C++ 侧自算）')
        self._start(
            'update_info',
            # ⚠️ web_license.request **不抛异常**：连不上 / 服务端报错 / 旧 DLL
            #    缺 lic_request 都以一句正文返回，所以状态位恒给 True，
            #    判定看正文（与 send_code / bind 两路同一条做法）。
            lambda: (True, web_license.request(
                action='update_user_info', **fields)),
            on_ok=self._after_saved)

    # ------------------------------------------------------------------
    # 「在这台电脑上退出」
    # ------------------------------------------------------------------

    def logout(self):
        """「在这台电脑上退出」：确认之后请服务端解除本机的登记。

        ★★ **为什么非要有确认框**：按钮文案刻意取得轻（它只陈述**范围**，
        不吓人），所以**后果全部由这一个对话框承担** —— 文案见
        :data:`_Logout.ASK`，它必须说清「本机马上不能用 / 恢复要能收邮件 /
        只影响这一台」三件事。**不要**把确认框去掉或写轻。

        ⚠️ **不需要验证码**：服务端上机器码即凭证（与「更新信息」同一信任级），
        所以这里不读 ``code_edit``、也不需要用户先填任何输入框。

        ⚠️ **计算运行期间不许退出**：退出会让**服务端**立刻解除本机的登记，而
        本机这一次运行仍握着内核侧那份缓存（见 :meth:`_after_logout` 的「已知
        限制」）—— 于是界面会显示「未登录」、计算却照跑，是个自相矛盾的状态。
        与其让用户对着这种界面猜，不如请他把计算停下来再退出。按钮在运行期间
        本来就是禁用的（见 :meth:`_update_buttons`），这里再判一次是第二道保险
        （禁用只是交互层的，``clicked`` 仍可能被程序调用）。

        ⚠️ **真正的状态清理在 :meth:`_after_logout`**：本方法只负责「问一句 +
        发请求」。服务端没删成功时**什么都不清**（见那里的说明）。
        """
        if self._busy:
            # 理论上按钮已禁用，点不到；第二道保险（与 _start 同一条做法）
            self._log('上一个请求还没结束，请稍候')
            return

        # ⚠️ 与 :meth:`_update_buttons` **共用同一个判据**（``_is_running``）：
        #    这里再判一次是第二道保险（禁用只是交互层的，``clicked`` 仍可能被
        #    程序调用），但**不要**另写一份 —— 两处判据一旦漂开，就会出现
        #    「按钮明明是灰的、程序调一下却真退了」。
        if self._is_running():
            self._warn('有计算正在运行',
                       '请先停止正在运行的计算，再在这台电脑上退出。\n\n'
                       '（退出后本机处于「未登录」状态，与正在进行中的计算'
                       '放在一起会自相矛盾。）')
            return

        if not self.machine_code:
            self._warn('无法退出', '本机硬件码为空（zml.dll 未加载？），无法退出。')
            return

        if not self._confirm_logout():
            self._log('用户取消了「在这台电脑上退出」')
            return

        self._log('请求在这台电脑上退出（机器码由 C++ 侧自算）')
        self._start(
            'unbind',
            # ★ **直接用公开的 request()，不给 WebLicense 加具名方法**：
            #   动作名收口（v1.10.8）的本意就是「服务端再加动作，客户端只多写
            #   一行调用」—— 本功能因此**一行内核代码都没动、也没重编 DLL**。
            # ⚠️ **整段不传 ``target_machine``**：界面只退自己。服务端明确规定
            #   「**给了空串 ≠ 没给**」（空串按非法机器码 400），而 ``request``
            #   对没传的字段**整段不发** —— 这正是它默认的行为，别去补一个空串。
            # ⚠️ ``request`` **不抛异常**：连不上 / 服务端报错 / 老服务器都以一句
            #   正文返回，所以状态位恒给 True，判定看正文
            #   （与 send_code / bind / update_info 三路同一条做法）。
            lambda: (True, web_license.request(action='unbind')),
            on_ok=self._after_logout)

    def _confirm_logout(self) -> bool:
        """弹确认框问一次（**默认焦点在「取消」**）。

        ★ **默认按钮必须是「取消」**：这是一个破坏性动作，而它唯一的安全默认
        就是「什么都不做」。回车键因此不会意外退出。

        ⚠️ 两个按钮的**文字**用动作名与「取消」而不是 Yes / No：用户在弹窗上
        再读一遍自己要点的是什么，比「是 / 否」少一次翻译。

        Returns:
            bool: 用户确认了返回 True。
        """
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        box.setWindowTitle(_Logout.TITLE)
        box.setText(_Logout.TITLE)
        box.setInformativeText(_Logout.ASK)
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        no = QtWidgets.QMessageBox.StandardButton.No
        box.setStandardButtons(yes | no)
        # ⚠️ 改按钮文字而不是用 addButton(text, role)：StandardButton 是本项目
        #    已经在用的那一套（见 style_sheet_edit.py 的「恢复默认」），
        #    ButtonRole 反而没有先例。
        box.button(yes).setText(_Logout.BUTTON)
        box.button(no).setText('取消')
        box.setDefaultButton(no)
        box.exec()
        return box.clickedButton() is box.button(yes)

    def _on_note_changed(self):
        """备注框内容变了：**就地**把「折成单行之后」的长度卡在上限内。

        ⚠️ **为什么需要它**：``QLineEdit`` 有 ``setMaxLength``，而多行控件
        ``QPlainTextEdit`` **没有**。不拦的话用户能敲到几千字，发出去被服务端
        静默截断到 512 —— 他会以为全存进去了（这正是本项目最忌讳的那类「假成功」）。

        ⚠️ **按「折成单行之后」的长度判，不是按框里的字符数**：折行时换行会变成
        ``；``（一换一），但空行会被丢掉，所以两者不一致。以发出时的形态为准，
        才不会出现「界面里没超、发出去被截」的错位。

        ⚠️ **超长时截断而不是拒绝输入**：拒绝会让用户敲不进字（以为键盘坏了）。
        截断 + 光标回到末尾是可预期的行为。

        ⚠️ 这里用 ``blockSignals`` 防止 ``setPlainText`` 再触发本槽一次
        （否则会递归）。
        """
        if self._note_guard:
            return
        widget = self.note_edit
        text = widget.toPlainText()
        if len(_ProfileBox.note_to_wire(text)) <= _ProfileBox.MAX_NOTE_LEN:
            return
        # 逐行累加，把能放下的部分留下（比「按字符数硬切」更贴近发出时的形态）
        kept, used = [], 0
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cost = len(line) + (len(_ProfileBox.NOTE_LINE_SEP) if kept else 0)
            if used + cost <= _ProfileBox.MAX_NOTE_LEN:
                kept.append(line)
                used += cost
                continue
            # ⚠️⚠️ 这一行放不下。**不能直接 break** —— 若整个备注就是**一行**
            #    超长文本（常见：粘贴一段没换行的文字），break 会让结果变成
            #      **空串**，用户的输入被**整段丢掉**（真踩过，自测逮住）。
            #      所以按剩余额度在这行里**切一段**留下，再去掉可能落在末尾的
            #      分隔符。
            room = _ProfileBox.MAX_NOTE_LEN - used
            if kept:
                room -= len(_ProfileBox.NOTE_LINE_SEP)
            if room > 0:
                kept.append(line[:room])
            break
        trimmed = _ProfileBox.NOTE_LINE_SEP.join(kept)
        self._note_guard = True
        try:
            widget.setPlainText(trimmed)
            # 光标回到末尾（setPlainText 会把它重置到开头）
            cursor = widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            widget.setTextCursor(cursor)
        finally:
            self._note_guard = False
        self._log(f'备注超长，已截至 {_ProfileBox.MAX_NOTE_LEN} 字符（服务端上限）')

    def auto_query(self):
        """首次显示时自动查一次在线状态（在后台线程里）。
        与「刷新状态」的差别只有一条：**不用弹窗、不打扰用户**。查不到就安静
        作罢（未联网、没绑定都是常态），结果仍照常显示在状态框里，用户想看
        细节自己点「刷新状态」。

        ⚠️ 硬件码为空（zml.dll 没加载）时直接跳过 —— 那种情况下查询必定返回
        「dll not found」，只会往日志里灌一条没用的错误。
        """
        if not self.machine_code:
            self._log('跳过自动查询：硬件码为空（zml.dll 未加载）')
            # ⚠️ 必须把横幅从进行时（:data:`_Pending.CHECK`）改掉：压根不查就永远
            #    等不到结果，留在那儿会让人以为程序卡住了。
            self.status_label.setText('无法查询：本机 zml.dll 未加载。')
            return
        self._log('自动查询一次在线状态（后台线程，不阻塞显示）')
        self._start('check', self._check_task(), on_ok=self._prefill)

    def _check_task(self):
        """构造「查一次授权」的后台任务。

        ⚠️ 返回的闭包把 ``check_web`` 的 ``(答复, 耗时)`` **解包**后重新打包成
        :class:`_Worker` 要的 ``(状态码, 正文)`` —— 耗时挤进正文里会污染
        :func:`_on_result` 里那套「只看开头」的成功判定，所以走日志与状态框的
        独立通道（见 :meth:`_on_result`）。

        Returns:
            callable: 无参函数，返回 ``(状态码, 正文)``。
        """
        def task():
            text, elapsed = check_web(CHECK_FEATURE, read_cache=False)
            return 0, pack_elapsed(text, elapsed)
        return task

    def refresh_status(self):
        """「刷新状态」：查一次本机授权。

        ⚠️ 一律带 ``read_cache=False``：结果缓存是按查询名长期保留的，读缓存会
        让刚注册完的自检看到**注册之前**的旧结果。带 ``False`` 只是跳过「读」，
        新结果照旧写回缓存，所以「关于」页面随后看到的也是最新的那份。

        查完（无论查到什么）还要顺带刷新状态栏右下角的授权显示（见
        :meth:`_after_refresh`）：那里的结论来自**另一次**查询，本控件刷新了
        它并不会跟着变，不刷新就会出现「上面说已绑定、右下角还挂着尚未注册」。
        """
        self._log(f'查询登录状态：web_license.check({CHECK_FEATURE!r}, '
                  f'read_cache=False)')
        # ⚠️ 先把横幅改成进行时：这一步最长 30 秒，期间界面上什么都没变的话，
        #    用户会以为「刷新」这个按钮坏了。⚠️ 这一路的结果**必定**会走
        #    _show_status（查询没有失败分支），所以横幅一定会被结论覆盖掉 ——
        #    不需要像 bind / send_code 那样在失败时回收。
        self.status_label.setText(_Pending.CHECK)
        self._start('check', self._check_task(), on_ok=self._after_refresh)

    def _after_refresh(self, status, text):
        """「刷新授权状态」查完之后：预填输入框，并同步刷新状态栏的授权显示。

        两件事的先后**不能颠倒**：先 :meth:`_prefill`（把答复里的姓名 / 单位 /
        邮箱填进空输入框），再刷新状态栏 —— 状态栏那边要自己起后台线程、自己
        解析一次答复，放在前面只会让「界面先动」的时机变得不可预期。

        ⚠️ **状态栏这一路用缓存**（``read_cache=True``）：本次刷新刚带
        ``read_cache=False`` 查过一遍，拿到有效结果时已写回 C++ 侧的缓存，状态栏
        直接读它即可 —— 秒回，也**不会**再发一次网络请求。

        ⚠️ 与 :meth:`_after_bound` 的区别有两条：绑定那次必须 ``read_cache=False``
        （要确认服务端真的认了这份新授权，读缓存会拿到绑定之前的旧结论）；而那条
        路径还会整段置忙，这里**不自动置忙** —— 状态栏的查询在它自己的线程里跑
        （见 :meth:`LicenseButton.update_license_state`），刷新期间本控件的按钮
        照旧可用。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: ``web_license.check`` 的答复（可能是失败文案，照样刷新 —— 此时
                缓存没被更新，状态栏显示的是上一次的结论，而横幅里写着本次查到了
                什么，两者互不掩盖）。
        """
        self._prefill(status, text)
        self._update_system_state(read_cache=True)

    # ------------------------------------------------------------------
    # 预填
    # ------------------------------------------------------------------

    def _prefill(self, status, text):
        """把「已绑定的那份授权」里的邮箱 / 姓名 / 单位 / 备注填进输入框，并切形态。

        ★★ **这是「服务端值」的唯一入口**（单出处原则，见模块文档）：切形态与
        填框都只在这里发生。⚠️ 任何别处想改输入框，先问一句「这是服务端的新
        事实吗」—— 不是就别动；是的话就调本方法。

        ⚠️ **未绑定 / 查不到时也要切形态**：那正是「注册形态」的判据。所以本方法
        在**任何**路径上都会调 :meth:`_apply_mode`，绝不提前 return 而不切。

        ⚠️ **只在输入框为空时才填**：用户可能已经在敲字了（查询要联网，回来得
        比人慢），覆盖掉他刚输入的内容是最讨厌的一类交互。

        ⚠️ **未绑定时什么都不填**：那种情况下答复里的姓名 / 单位并不属于本机
        用户 —— 填进去会让用户以为自己的名字已经在系统里了。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: ``web_license.check`` 的答复。
        """
        del status
        info = bound_info(text)
        if not info:
            # ⚠️ 分两种「没有 info」：
            #    * ``is_yes`` 为真 = **确认未绑定**（答复是成功的，只是没绑邮箱）
            #      -> 切到注册形态；
            #    * ``is_yes`` 为假 = **查不到**（断网 / 超时 / 授权无效）
            #      -> 形态**不动**，避免网络抖动让界面来回翻（那会让人以为自己的
            #         机器一会儿绑了一会儿没绑）。
            if is_yes(text):
                self._bound_email = ''
                self._apply_mode(_ProfileBox.MODE_REGISTER)
                self._log('未登录（答复里没有 Source 段，或来源是兜底记录）')
            else:
                self._log('没拿到可用的登录状态，界面形态保持不变')
            return

        # ★ 记下「服务端说本机绑的是哪个邮箱」：_on_email_edited 靠它判断用户
        #   有没有把邮箱改掉（改掉就是换绑）。必须在 _apply_mode 之前更新，
        #   否则 _apply_mode 之后紧接着的那次判断会拿旧值。
        self._bound_email = str(info.get('email') or '').strip()

        self._apply_mode(_ProfileBox.MODE_UPDATE)

        filled = []
        absent = []
        occupied = []
        # ⚠️ 备注是**多行**控件，与另外三个不是一个类型：取值/写值要走
        #    _ProfileBox.note_of / set_note，不能直接 .text() / .setText()
        #    （那是 QLineEdit 的接口）。所以它单独处理，不塞进下面这个循环。
        for edit, key, label in ((self.email_edit, 'email', '邮箱'),
                                 (self.user_edit, 'user', '姓名'),
                                 (self.org_edit, 'org', '单位')):
            value = str(info.get(key) or '').strip()
            # ⚠️ **本地不做任何转义 / 还原**：服务端已把禁用字符折成全角后才
            #    回传，直接显示即可 —— 再过一道反而与服务端不一致。
            if not value:
                # ⚠️ 取不到是**正常**的：老授权文件里可能本来就没有这些字段。
                self._log(f'已登录，但答复里没有「{label}」，跳过预填')
                absent.append(label)
            elif edit.text().strip():
                self._log(f'「{label}」已有内容，不覆盖（预填只填空的）')
                occupied.append(label)
            else:
                edit.setText(value)
                filled.append(label)

        # ★★ **备注要单独取**：许可查询的响应里**没有备注**，它改由另一个动作以
        #     **base64** 回传，所以这里只能**另起一个后台请求**。
        #
        #     ⚠️ 三条纪律：
        #       ① **只在框为空时取**：用户可能正在里面敲字，多一次请求
        #          不能变成一次覆盖；
        #       ② **不阻塞**：走 :class:`_Worker`（单次最长 60 秒）；
        #       ③ **失败安静**：读不到就什么都不做（备注本来就可以是空的），
        #          绝不弹窗。
        #     ⚠️ 它不进下面那个 `filled` / `absent` 统计（那是同步的），
        #        而是自己记一行日志。
        if not self.note_edit.toPlainText().strip():
            self._fetch_note()

        source = info.get('source') or '(未知)'
        if filled:
            self._log(f'已登录到 {source}，预填了：{"、".join(filled)}')
        elif occupied and not absent:
            self._log(f'已登录到 {source}，输入框都已有内容，未改动')
        else:
            # 有字段缺失，也有可能是用户在敲字：把「没填成」的原因说清楚
            self._log(f'已登录到 {source}，没有可预填的字段'
                      f'（缺失：{"、".join(absent) or "无"}；'
                      f'已有内容：{"、".join(occupied) or "无"}）')

    def _fetch_note(self):
        """后台取一次备注（``read_file`` 读 ``note.txt`` + base64 解码）。

        ★★ **为什么要单独取**：备注存在**用户文件**里（``note.txt``），而许可
        查询的响应只带 ``User:`` / ``Org:`` 那几个字段 —— 所以进入已绑定形态时
        **多一次网络往返**。

        ⚠️ **只取一次**（:attr:`_note_fetched` 闸门）：``refresh_status`` 可能被反复
        调（每次刷新都会走 ``_prefill``），而备注是**不怎么变**的展示
        字段 —— 每次都取等于把一次刷新变成两次请求。
        ⚠️ 但**保存/更新成功后要把闸门重置**（见 :meth:`_after_saved`），
        否则刚改完的备注不会被重新读回来校验。

        ⚠️ 读不到就**安静地什么都不做**：备注本来就可以是空的，为它弹窗只会
        打扰用户。失败只记一行日志。
        """
        if self._note_fetched:
            return
        self._note_fetched = True
        if not self.machine_code:
            return
        self._log('后台取一次备注（它存在 note.txt 里）')
        self._start(
            'note',
            lambda: (True, web_license.request(
                action='read_file', file_name=_ProfileBox.NOTE_FILE_NAME)),
            on_ok=self._after_note_fetched)

    def _after_note_fetched(self, status, text):
        """备注取回来了：解 base64 并填进多行框。

        ⚠️ **三种结果分开处理**（见 :meth:`_ProfileBox.decode_note`）：
        ``None`` = 读不到（不动框）；``''`` = 备注本来就是空的（同样不动）；
        其余 = 原文（填进去）。

        ⚠️ **只填空框**：与其余字段同一条纪律（用户可能已经在敲字了）。
        ⚠️ 不进那个同步的统计（它早已结束），只记日志。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: ``read_file`` 的答复（``File: <base64>``）。
        """
        del status
        note = _ProfileBox.decode_note(text)
        if note is None:
            self._log('备注没取到（答复不是成功正文或 base64 解不开），框保持不变')
            return
        # ★ 记下「服务端那份是什么」—— 后续 _note_pending_action 靠它判断
        #   用户有没有真的动过备注（见那里的说明）。⚠️ 这两行必须在下面那些
        #   「框已有内容 / 本来就是空的」提前 return **之前**执行，否则会漏记：
        #   服务端事实与用户框里有没有字是**两件事**。
        self._note_dirty = note
        if not note:
            self._log('备注本来就是空的')
            return
        if self.note_edit.toPlainText().strip():
            self._log('「备注」已有内容，不覆盖（预填只填空的）')
            return
        _ProfileBox.set_note(self.note_edit, note)
        self._log(f'已回填备注（{len(note)} 字）')

    # ------------------------------------------------------------------
    # 形态（未绑定 / 已绑定）
    # ------------------------------------------------------------------

    def _apply_mode(self, mode):
        """切换界面形态：注册（未绑定 / 换绑中）或更新信息（已绑定）。

        ★★ **换绑邮箱靠的就是「切回注册形态」** —— 这是本方法最重要的一条：

        服务端换绑走的是 ``submit``（带 ``machine_code``），而不是
        ``update_user_info``（那个**永远改不了 email**，它是身份字段）。所以
        「想换邮箱」必须回到注册形态才能拿到验证码、才能发出 ``submit``。
        触发入口是**邮箱框**,见 :meth:`_on_email_edited`。

        ⚠️ **只切「可见性 / 只读 / 文案」，绝不重建控件** —— 输入框只有一套，
        重建会把用户正在输入的内容丢掉，也就违背了单出处原则。

        ⚠️ **隐藏的是「整行」**（标签 + 输入框），不是只藏输入框：留下一个
        孤零零的「验证码」标签看起来像界面坏了。用的是
        :meth:`_set_row_visible`（兼容 Qt 6.4 以下）。

        ⚠️⚠️ **邮箱框在两种形态下都必须可编辑**（只切换占位提示）：
        上一版在已绑定时把它 ``setEnabled(False)``，于是**用户没有任何办法换绑
        邮箱**（真踩过）。「这里不能改」的正确表达不是置灰，而是**让它能改**
        —— 改了自然进入换绑流程，而 ``email`` 本身也从来不是靠本地拦住的
        （``update_user_info`` 的请求体里根本不带 email）。

        Args:
            mode: :data:`_ProfileBox.MODE_REGISTER` / ``MODE_UPDATE``。
        """
        if mode == self._mode:
            return
        self._mode = mode
        bound = (mode == _ProfileBox.MODE_UPDATE)

        # 主按钮：同一个按钮，换文案 + 换提示
        self.register_button.setText(_ProfileBox.BUTTON_UPDATE if bound
                                     else _ProfileBox.BUTTON_REGISTER)
        if bound:
            self.register_button.setToolTip(
                '把上面的姓名 / 单位 / 备注保存到服务端。\n'
                '⚠️ 不需要验证码 —— 本机硬件码就是凭证。\n'
                '留空的项不会被改动。\n'
                '（要换邮箱请直接改上面的邮箱，界面会自动切回登录流程。）')
        else:
            self.register_button.setToolTip(
                '用验证码把本机与该邮箱关联起来。\n'
                '邮箱若从未登录过，会顺手为它完成登录。\n'
                '若本机此前用的是另一个邮箱，这一步就是**更换邮箱**。')

        # 顶部说明：跟着形态换，否则界面自相矛盾
        self.hint_label.setText(_ProfileBox.HINT_UPDATE if bound
                                else _ProfileBox.HINT_REGISTER)

        # 验证码那一整行：只在注册形态下存在
        self._set_row_visible(self.code_edit, self.code_label, not bound)
        self.send_button.setVisible(not bound)

        # 邮箱：**两种形态都可编辑**，只换占位提示（见方法文档里那条 ⚠️⚠️）
        self.email_edit.setPlaceholderText(
            _ProfileBox.EMAIL_HINT_BOUND if bound
            else _ProfileBox.EMAIL_HINT_FREE)
        self.email_edit.setToolTip(
            ('当前绑定的邮箱就是上面这个。\n'
             '要换成别的邮箱：直接改这里 → 点「发送验证码」→ 填码 → '
             '点「登录」。\n'
             '⚠️ 这一步会把姓名与单位也写到**新邮箱**名下。')
            if bound else
            '登录用的邮箱。\n'
            '（换一台机器 / 换邮箱，也是改这里再走一次验证码。）')

        # 姓名 / 单位的「必填」提示只在注册形态下成立
        self.user_edit.setPlaceholderText(
            '留空 = 不改' if bound else '必填，例如：张三')
        self.org_edit.setPlaceholderText(
            '留空 = 不改' if bound else '必填，例如：XX大学 / XX研究院')

        self._log(f'界面形态切换为：{"更新信息" if bound else "登录"}')
        self._update_buttons()

    def _on_email_edited(self):
        """邮箱框被改动：**这是一次换绑动作，立刻切回注册形态**。

        ★★ **为什么要这么做**：换绑邮箱必须走 ``submit``（带验证码），而
        ``update_user_info`` 永远改不了 email。所以只要用户动了邮箱，就必须
        把验证码那一行与「注册并绑定本机」还给他 —— 否则他会卡在「我改了邮箱，
        但按钮是『更新信息』、它并不管邮箱」这个死胡同里（那正是上一版的缺陷）。

        ⚠️ **判据是「与当前绑定的邮箱是否相同」，不是「有没有敲过键盘」**：
        用户可能改了又改回去（或者只是点进来按了一下退格再撤回）。改回原值就
        应该回到更新形态 —— 否则界面会停在一个「我并不需要验证码」的状态上。

        ⚠️ **只有「本机确实绑过邮箱」时才有意义**：``_bound_email`` 为空说明本机
        未绑定（或还没查到）—— 那时本来就该是注册形态，改邮箱不切任何东西。
        ⚠️⚠️ **判据必须用 ``_bound_email``，不能写成 ``self._mode != MODE_UPDATE``**
        （真踩过）：一旦切进注册形态，那个判据就让本方法**再也切不回来** ——
        用户把邮箱改回原值后界面仍停在换绑流程，验证码行收不回去。

        ⚠️ **这里不碰任何输入框的内容**（只切形态）：用户在敲字的过程中被改写
        内容是最讨厌的一类交互。
        """
        bound_email = (self._bound_email or '').strip()
        if not bound_email:
            # 本机没绑定过邮箱（或还没查到）：改邮箱不改变任何事
            return
        current = self.email_edit.text().strip()
        # 改了邮箱 -> 进注册形态（换绑）；又改回去 -> 回更新形态
        want = _ProfileBox.MODE_UPDATE if current == bound_email \
            else _ProfileBox.MODE_REGISTER
        if want == self._mode:
            return
        self._apply_mode(want)
        if want == _ProfileBox.MODE_REGISTER:
            self.hint_label.setText(_ProfileBox.HINT_REBIND)
            self._log(f'邮箱被改动（原为 {bound_email}），'
                      f'切到更换邮箱流程：需要重新收验证码')
        else:
            self._log('邮箱改回了当前绑定的那个，切回更新形态')


    def _set_row_visible(self, field, label, visible):
        """显示 / 隐藏 ``QFormLayout`` 里的**一整行**（标签 + 字段）。

        ⚠️ **两条路都要留着**：``QFormLayout.setRowVisible`` 是 **Qt 6.4+** 才有
        的，而本仓库同时支持 PyQt5 / PyQt6。取不到时退化成「分别隐藏标签与
        控件」—— 效果一样，只是要自己管两个对象。

        ⚠️ **不要**只 ``field.setVisible(False)``：``QFormLayout`` 会保留那一行的
        标签，界面上就留下一个「验证码」孤零零地挂着。

        Args:
            field: 该行的输入控件（用来定位行）。
            label: 该行的标签控件（``form.labelForField(field)`` 的结果）。
            visible: True = 显示。
        """
        setter = getattr(self._form, 'setRowVisible', None)
        if setter is not None:
            # Qt 6.4+：一步到位（传控件即可）
            setter(field, bool(visible))
            return
        # 退路：自己管标签 + 控件（PyQt5 / 老 Qt6）
        field.setVisible(bool(visible))
        if label is not None:
            label.setVisible(bool(visible))

    def _push_pending_note(self):
        """把备注补写到服务端（``submit`` 的请求体里没有备注）。

        ★★ **为什么需要这一步**：服务端的 ``submit`` 只收 ``email`` / ``code`` /
        ``machine_code`` / ``user`` / ``org`` —— **没有**备注。所以「注册时
        直接写备注」只能是两步：先 ``submit`` 注册，再 ``write_file`` 把备注
        写进 ``note.txt``。本方法就是第二步，对用户是透明的（他只觉得
        「我填了就生效了」）。

        ⚠️ **备注为空时就一次都不发**：留空是常态，多发一次就是白等一个往返。

        ⚠️ **失败【不】回滚注册、也【不】弹「注册失败」**：注册已经成功了，
        那时说失败是**谎报**。所以只记一行日志，并把备注留在输入框里 ——
        用户点「更新信息」可以再试一次（那时形态已是更新，按钮也已经是它）。

        ⚠️ **必须在形态已切到「更新」之后才调**：否则会被判成注册形态而不发
        请求（见 :meth:`_on_primary_clicked`）。所以本方法**直接走**
        :meth:`_start`，不经过 ``_on_primary_clicked``。
        """
        # ★ 备注**发之前必须自己 base64 编一次**（`write_file` 收的是编码后的
        #   字节，与旧的 `update_user_info(note=…)` 直接收原文不同）。
        note = _ProfileBox.note_of(self.note_edit)
        if not note:
            return
        body = _ProfileBox.note_to_file_body(note)
        if not body:
            return
        if not self.machine_code:
            self._log('备注没补上：硬件码为空')
            return
        self._log(f'登录成功，接着补写备注（submit 不支持备注）：{note!r}')
        self._start(
            'note_write',
            lambda: (True, web_license.request(
                action='write_file',
                file_name=_ProfileBox.NOTE_FILE_NAME,
                data_base64=body)),
            # ⚠️ 用**本动作自己的**收尾：它只记日志、不弹「注册成功」那种框
            #    （注册的框已经弹过了），详见 _after_note_pushed。
            on_ok=self._after_note_pushed)

    def _after_note_pushed(self, status, text, finalize=None):
        """备注那一趟（写 / 删）回来之后的收尾。

        ⚠️ **两个调用者的收尾不一样，所以有 ``finalize``**：

        - **注册那条路**（:meth:`_push_pending_note`）：不传 —— 只记日志 + 刷一次
          服务端。⚠️ **不弹窗**：注册那次已经弹过「登录成功」了，再弹一个会让
          人以为操作了两次；而且注册成功是既成事实，这里报「失败」是**谎报**。
        - **「更新信息」那条路**（:meth:`_push_note_change`）：传
          :meth:`_after_saved` —— 那一趟才负责弹「已更新」并做完整刷新。⚠️
          必须等备注也落地了才弹，否则用户看到「已保存」而备注还在飞。

        ★ **要顺带把「服务端那份是什么」更新掉**，否则用户刚写完备注，紧接着
        点一次「更新信息」会因为 ``_note_dirty`` 还是旧值而**再发一遍**同样的写。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: ``write_file`` / ``delete_file`` 的答复。
            finalize: 可选的收尾回调 ``finalize(status, text)``。
        """
        del status
        text = str(text or '').strip()
        if _ProfileBox.is_file_written(text):
            # ★ 写成功了：服务端那份**就是**框里这份。
            self._note_dirty = _ProfileBox.note_of(self.note_edit)
            self._log('备注已写入服务端（note.txt）')
        elif _ProfileBox.is_file_deleted(text):
            # ★ 删成功了：服务端那份**已经没有**了。
            self._note_dirty = ''
            self._log('备注已从服务端删除（note.txt）')
        else:
            # ⚠️ 失败**不动** ``_note_dirty``：服务端到底存着什么我们并不知道
            #    （写可能已生效但答复丢了），保持旧值最保守 —— 用户再点一次
            #    会重发，而写与删**都是幂等**的。
            self._log(f'备注没写进去：{text}')
            # ⚠️ 把备注**留在输入框里**（不清空）：用户点「更新信息」可再试。
        if finalize is not None:
            finalize(True, text)
            return
        # 无论成败都重新读一次服务端，让界面显示的是**服务端真的存下了什么**
        self.refresh_status()

    def _after_saved(self, status, text):
        """「更新信息」全部成功后的收尾（姓名 / 单位已写入，备注那一趟也完成了）。

        ★★ **必须重新读一次服务端**（:meth:`refresh_status`）：否则界面上显示的
        是**用户刚敲进去的文本**，而不是「服务端真的存下了什么」。虽然多半一致，
        但两者含义不同 —— 而本控件的既有纪律正是「只显示服务端原话」。
        ⚠️ 这也顺带解决了「改完之后界面还是旧的」这一类观感问题。

        ⚠️ 那一趟用 ``read_cache=False``（由 ``refresh_status`` 保证）：读缓存会
        拿回**改之前**的那份，界面上就等于「改了没生效」。

        ⚠️ **本方法在「备注那一趟也跑完了」之后才被调到**（由
        :meth:`_after_note_pushed` 转发）—— 否则会弹出「已保存」而备注还在飞。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: 响应正文（``Updated``）。
        """
        del status
        self._log('信息已更新：服务端已写入')
        # ★ 重置备注闸门：刚改完，要让接下来的 refresh_status -> _fetch_note
        #   把**服务端真的存下的那份**读回来校验（而不是留着用户
        #   刚敲的文本）。⚠️ 不重置的话，改完后框里的内容**永远**
        #   不会被服务端那份覆盖，与其余字段的行为不一致。
        self._note_fetched = False
        QtWidgets.QMessageBox.information(
            self, '已更新',
            '信息已保存到服务端。\n\n'
            '（留空的项没有被改动。）')
        # ⚠️ 刷新状态栏让右下角的姓名也跟着变，并重新读一次服务端回填输入框。
        self._update_system_state(read_cache=False)
        self.refresh_status()

    def _after_logout(self, status, text):
        """「在这台电脑上退出」成功后的收尾（**只在服务端确实删掉了才走到这里**）。

        ★ **要清的东西有四类，少一样都会留下不一致**：

        1. **闸门**（``web_license.checked_features``）：它是「本次运行已经查过这个
           feature」的登记，不清则余下的迭代**不再复查**。⚠️ 这是本控件**够得着
           的唯一一层**缓存 —— 见下面那条限制。
        2. **界面上的「服务端事实」**：姓名 / 单位 / 邮箱 / 备注输入框、
           ``_bound_email``、备注闸门 ``_note_fetched``。⚠️ **不清就等于把上一个人
           的姓名留在屏幕上** —— 机器一旦转手，下一个人打开看到的就是别人的名字。
        3. **横幅与退出按钮**：靠随后的 :meth:`refresh_status` 走一遍
           :meth:`_show_status`（它会切到「尚未登录」并藏起按钮）。
        4. **状态栏**：右下角那一个也要跟着变，否则上方已经「尚未登录」、
           右下角还挂着「已登录：某某」。

        ⚠️⚠️ **已知限制（不要以为本地已经清干净了）**：内核侧
        ``System::CheckLicense`` 还有一层**按 feature 的进程内缓存**，而它的
        **成功结论不会被失败覆盖**（要连续失败 10 次才冻住）。本控件**够不着**
        那一层（动它就要改 ``_lic.py`` / 重编 DLL，而本功能刻意不动内核）。
        后果：**本次运行里已经成功查过的 feature，退出后仍可能照跑**，直到软件
        重启（新进程 = 空缓存）为止。
        → 所以确认框里**不写**「本机将无法继续使用」（见 :data:`_Logout.ASK`）。
        → 但**服务端确实已经解绑**（那是唯一的事实来源），重启后必然生效。

        ⚠️ **失败时什么都不清**：服务端没删成功（503 / 断网 / 老服务器），本机
        就**仍然是登录态** —— 清掉本地状态只会让界面与事实不符。

        Args:
            status: 状态位（未使用，只为与 :meth:`_start` 的回调签名一致）。
            text: 响应正文（``Unbound``）。
        """
        del status
        self._log('已在这台电脑上退出：服务端已解除本机的登记')
        # ① 闸门：让本轮余下的迭代**重新去问一次**服务器。
        try:
            web_license.checked_features.clear()
        except Exception as err:      # 防御：内部状态万一不可用也不能把退出打断
            self._log(f'清理查询闸门失败（不影响退出本身）：{err}')
        # ② 清掉属于上一个登录身份的信息
        self._clear_profile()
        QtWidgets.QMessageBox.information(
            self, '已退出',
            '已在这台电脑上退出。\n\n'
            '本机当前不可用于计算；需要时用同一个邮箱重新登录即可恢复。')
        # ③④ 重新读一次服务端（read_cache=False，不吃退出前的旧结论），
        #     并把右下角状态栏一起刷新。
        self.refresh_status()
        self._update_system_state(read_cache=False)

    def _clear_profile(self):
        """把界面上那份**属于上一个登录身份**的信息全部清掉。

        ★★ **为什么必须清**：这些字段是「服务端事实」的本地副本，而退出之后
        那份事实已经不存在了。⚠️ 留着它们的后果不是「显示过时」，而是
        **把上一个人的姓名 / 单位 / 备注留在屏幕上** —— 机器转手、或者多人共用
        一台电脑时，下一个人一打开就看到别人的名字。

        ⚠️ 备注走 :meth:`_ProfileBox.set_note` 而不是 ``setPlainText``：
        它是多行控件，取值 / 写值必须走那一对方法（见那里的说明）。

        ⚠️ **纯界面清理**：不置忙、不发请求 —— 调它的地方自己负责后续刷新。
        """
        self.user_edit.setText('')
        self.org_edit.setText('')
        self.email_edit.setText('')
        self.code_edit.setText('')
        _ProfileBox.set_note(self.note_edit, '')
        # ⚠️ 这三样是「服务端事实」的影子，必须跟着清：
        #    ``_bound_email`` 留着会让 _on_email_edited 以为用户「改了邮箱」；
        #    ``_note_fetched`` 留着会让备注**再也不去服务端取**；
        #    ``_note_dirty`` 留着会让下一个登录的人点「更新信息」时，被拿去
        #    与**上一个人的**备注比较（判据就此失真）。
        self._bound_email = ''
        self._note_fetched = False
        self._note_dirty = None
        self._log('已清空界面上的姓名 / 单位 / 邮箱 / 备注')

    # ------------------------------------------------------------------
    # 请求编排
    # ------------------------------------------------------------------

    def _start(self, key, func, on_ok=None):
        """起一个后台请求，并把它接到结果处理上。

        Args:
            key: 请求标识（同一时刻只允许一个，所以它同时也是「当前动作」）。
            func: 无参可调用对象，返回 ``(状态码, 正文)``。
            on_ok: 成功时的回调 ``on_ok(状态码, 正文)``。
        """
        if self._busy:
            # 理论上按钮已禁用，点不到；这里是第二道保险（例如回车键触发）
            self._log('上一个请求还没结束，请稍候')
            return

        # ⚠️ **parent 留空**（不是 ``parent=self``）：本控件会随标签页被
        #    deleteLater 销毁，parent 设成自己的线程会被连带析构 —— 请求还在飞
        #    的时候就是进程崩溃。改由模块级 _RUNNING_WORKERS 持有强引用。
        worker = _Worker(key, func, parent=None)
        worker.finished_with.connect(
            lambda k, s, t: self._on_result(k, s, t, on_ok))
        worker.finished.connect(lambda: self._workers.pop(key, None))
        worker.finished.connect(lambda w=worker: _forget_worker(w))
        worker.finished.connect(worker.deleteLater)

        self._workers[key] = worker
        _RUNNING_WORKERS.append(worker)
        self._set_busy(True)
        worker.start()

    def cleanup_before_tab_close(self):
        """关闭本标签页时调用（``TabWidget.close_tab``）：**不等**在飞的请求。

        ⚠️ **本方法刻意不 ``wait()``**：请求最长 60 秒，在这里同步等会把「关标签」
        变成冻结界面；线程本来就没有 parent（见 :data:`_RUNNING_WORKERS`），
        因此它**不会**随控件一起被销毁，关标签只是让结果失去接收者 —— 线程照旧
        跑完，然后被 :func:`_forget_worker` 摘掉。

        ⚠️ 与 :meth:`closeEvent` 的分工：那个只在控件被**单独** ``close()``
        （例如直接跑 :func:`test_1`）时触发，走标签页关闭是**不会**触发的 ——
        那条路径由本方法负责。

        ⚠️ 必须把 :meth:`_set_busy` 的残留状态清掉：控件若被「复显」（同一实例
        再次 addTab）会带着 ``_busy=True`` 回来，所有按钮都是灰的、点不动。
        """
        self._workers.clear()
        self._busy = False

    def _on_result(self, key, status, text, on_ok):
        """后台请求回来了（**在主线程里跑**）。

        ⚠️ 判定成功用的是本模块的 :func:`is_sent` / :func:`is_bound`
        （**只看开头**），不是 ``text == 'Sent'`` —— 服务端的成功正文目前恰好
        就是那三个字，但严格相等是一条会随服务端演进而失效的隐含假设；而且
        限流答复 ``'a code was sent recently, please wait 412s'`` 里**含**
        ``sent`` 却不以它开头，所以「包含」判断同样不能用。

        Args:
            key: 请求标识。
            status: 状态位。⚠️ ``send_code`` / ``bind`` 这两路现在**恒为 True**：
                ``web_license.send_code`` / ``web_license.submit`` 按契约不抛异常，一切失败都以
                正文返回，所以「拿到答复」本身没有失败态。保留这个参数是为了与
                :meth:`refresh_status` 共用同一条结果通道。
            text: 响应正文（可能为空）。
            on_ok: 成功回调。
        """
        # ⚠️ **控件可能已经被销毁**（用户关掉了本标签页，而请求还在飞）：
        #    此时线程仍会把结果发回来，而槽里的 self 只余一个 Python 壳子
        #    （底层 C/C++ 对象已 delete）—— 再碰 self.send_button 之类就会抛
        #    ``RuntimeError: wrapped C/C++ object of type ... has been deleted``。
        #    这类「迟到结果」必须直接丢弃：界面已经不存在，没什么可更新的。
        #    判断方式用 sip/shiboken 的 isdeleted（PyQt5/PyQt6 通用），
        #    取不到该属性时按「没被删」处理（宁可不跳过，也不要漏掉正常结果）。
        if _is_deleted(self):
            return
        self._set_busy(False)
        # ⚠️ 先拆出耗时再 strip / 判开头：耗时是 pack_elapsed 附加的私有尾巴，
        #    留在正文里会让 is_sent / is_bound 和 _show_status 都读到脏数据。
        text, elapsed = unpack_elapsed(text)
        text = str(text or '').strip()
        self._log(f'响应 {text or "(空响应)"}')

        if key == 'check':
            # ⚠️ 查询没有「成功 / 失败」之分（答复一律是服务器原话），所以不走
            #    下面那条 is_sent / is_bound 判定，直接显示 + 交给 on_ok 处理。
            self._show_status(text, elapsed)
            # ⚠️ on_ok 必须在 _show_status **之后**：预填会改输入框，万一它以
            #    某种方式抛异常，状态框里至少已经显示出「服务器到底说了什么」。
            if on_ok is not None:
                on_ok(status, text)
            return

        if key == 'note':
            # ⚠️ **备注是独立一路**：成功记号是 ``File:``（不是 ``Yes`` /
            #    ``Updated`` / ``Bound``），而且结果是 **base64**，所以判定与解码
            #    都交给 :meth:`_after_note_fetched`。
            #    ⚠️ 这里**不**走 _show_failure：读不到备注不是错误（它本来就
            #    可以是空的），弹窗只会打扰用户。
            if on_ok is not None:
                on_ok(True, text)
            return

        if key == 'note_write':
            # ⚠️ **备注的写 / 删也是独立一路**（第六、第七个动作、两个记号：
            #    ``FileWritten`` / ``FileDeleted``）。
            #    ⚠️⚠️ **必须在这里显式分流**：落到下面那行兜底（``is_bound``）
            #    会被判成失败，于是用户在**注册成功之后**收到一个「操作失败」
            #    弹窗 —— 而那一步失败本来只该记日志（见 _after_note_pushed）。
            #    ⚠️ 成功与否交给 _after_note_pushed 自己判（它同时要负责把
            #    ``_note_dirty`` 更新对），所以这里一律调 on_ok。
            if on_ok is not None:
                on_ok(True, text)
            return

        if key == 'update_info':
            # ⚠️ 更新信息用**它自己的**成功记号 'Updated'：拿 is_bound（'Bound'）
            #    去判会永远失败（'Updated' 不以 'bound' 开头），拿 is_sent
            #    同样不行。这是本控件第四个动作，也是第四个记号。
            if _ProfileBox.is_updated(text):
                if on_ok is not None:
                    on_ok(True, text)
                return
            self._show_failure(key, status, text)
            return

        if key == 'unbind':
            # ⚠️ **只认 'Unbound' 前缀**（第五个动作、第五个记号）。
            #    ⚠️ 绝不能写成「不是错误就算成功」：服务端对**不认识的动作**会
            #    当成一次许可查询（**旧服务器**收到 unbind 正是如此），那时回的
            #    是 ``Yes | …`` —— 按「不是错误」判就会把一次**没发生**的退出
            #    读成成功（假成功），用户的机器其实还没解绑。
            #    ⚠️ 也不要用 is_bound（'Bound'）：Unbound 不以 bound 开头。
            if _Logout.is_unbound(text):
                if on_ok is not None:
                    on_ok(True, text)
                return
            self._show_failure(key, status, text)
            return

        ok = is_sent(text) if key == 'send_code' else is_bound(text)
        if ok:
            if on_ok is not None:
                on_ok(True, text)
            return

        self._show_failure(key, status, text)

    def _after_sent(self, email):
        """发码成功后的收尾（把焦点挪到验证码框，省一次点击）。

        Args:
            email: 收件邮箱。
        """
        self.code_edit.setFocus()
        self._log(f'验证码已发往 {email}（有效期一天，请连同垃圾箱一起找）')
        QtWidgets.QMessageBox.information(
            self, '验证码已发送',
            f'验证码已发往 {email}。\n\n'
            '请把邮件里的 6 位数字填进「验证码」框，再点「登录」。\n\n'
            '（在成功使用之前，同一个验证码可以重复使用；有效期一天。）')

    def _after_bound(self, status, text):
        """绑定成功后的收尾：提示、自动自检、并刷新状态栏的授权显示。

        绑定之后还要确认服务端真的能读到这份授权，才算注册成功 —— 所以立刻
        自检一次。

        自检之外还要更新状态栏（:meth:`LicenseButton.update_license_state`）：
        那里显示着「尚未注册」，绑定完不刷新就会一直挂着旧结论，用户会以为没
        注册上。走 ``gui.update_system_state()`` 这个统一入口 —— 它会经
        ``gui.command`` 把调用投递到 GUI 线程执行。

        ⚠️ **状态栏这一路必须 ``read_cache=False``**：本机在绑定之前多半已经查过
        一次（缓存里存着「绑定之前」的成功结果，而 C++ 侧的成功结果按 feature 名
        长期保留），读缓存会把刚绑好的机器判成「未绑定」—— 明明注册成功了，状态栏
        却还显示「尚未注册」。这与 :meth:`refresh_status` 的 ``read_cache=False``
        理由完全相同。

        ★ **注册成功后要接着把备注补上**（如果用户填了）：``submit`` 的请求体里
        没有备注，所以备注只能由 :meth:`_push_pending_note` 补第二步（``write_file``
        写 ``note.txt``）。
        ⚠️ 顺序是「先切形态、再补备注、最后自检」：形态必须先切成「更新」，否则
        补备注那一趟会被当成注册形态；而自检放最后是因为它是**可选**的观感刷新，
        不该挡在「备注到底写进去没有」前面（``_after_note_pushed`` 里还会再刷一次）。

        Args:
            status: HTTP 状态码。
            text: 响应正文（``Bound``）。
        """
        self.code_edit.clear()
        # ★ 这次是「换绑」还是「首次注册」？判据：本控件此前知不知道自己绑过邮箱。
        #   ⚠️ 必须在下面改 _bound_email **之前**算出来。
        rebind = bool(self._bound_email)
        self._log('更换邮箱成功：本机已改到该邮箱' if rebind
                  else '绑定成功：服务端已记录本机与该邮箱的关联')
        if rebind:
            QtWidgets.QMessageBox.information(
                self, '已更换邮箱',
                f'本机已从原来的邮箱换到 {self.email_edit.text().strip()}。\n\n'
                '⚠️ 这一步会把姓名与单位一并写到**新邮箱**名下。\n'
                '（旧邮箱的记录本身不受影响，它仍然属于原用户。）\n\n'
                '接下来会自动刷新一次登录状态做自检。')
        else:
            QtWidgets.QMessageBox.information(
                self, '登录成功',
                '本机已用该邮箱登录。\n\n'
                '该邮箱如果没有登录过，已顺手为它完成登录；'
                '你填的姓名与单位也在此时写入。\n\n'
                '接下来会自动刷新一次登录状态做自检。')
        # ⚠️ 先把 _bound_email 清掉再切形态：此刻「新邮箱」还没被服务端确认，
        #    留着一个**旧**值会让 _on_email_edited 以为用户又改了邮箱
        #    （旧值 != 框里的新邮箱）-> 刚切到更新形态又被翻回注册形态。
        #    真正的新值由紧接着的 refresh_status -> _prefill 填回来。
        self._bound_email = ''
        # ★ 本机从此就是「已绑定」了 -> 立刻切成更新形态，别等下一次查询。
        #   ⚠️ 这同时是 _push_pending_note 能工作的前提（它要求形态已是更新）。
        self._apply_mode(_ProfileBox.MODE_UPDATE)
        self._update_system_state(read_cache=False)
        # ★ 备注：填了才补（留空一次都不发）。
        #   ⚠️ 补备注那一路的收尾（_after_note_pushed）自己会调 refresh_status；
        #      没备注可补时，这里直接自检一次。
        note = _ProfileBox.note_of(self.note_edit)
        if note:
            self._push_pending_note()
        else:
            self.refresh_status()

    @staticmethod
    def _update_system_state(read_cache=True):
        """让主窗口状态栏重新读一次本机的授权状态（不等待联网，查询在后台线程）.

        ``gui.update_system_state()`` 取到的是 :class:`GuiBuffer.Agent` —— 它是
        **可调用对象**：``Agent.__call__`` 会把调用转发给 ``gui.command``，所以
        这一句确实会执行到 ``MainWindow.update_system_state``；关键字参数也经
        ``GuiApi.command`` 原样透传。

        ⚠️ 没有主窗口时 ``gui.command`` 直接返回 ``None``（不报错），所以本控件
        单独使用（例如 :func:`test_1`）时这里是安静跳过。

        Args:
            read_cache: 是否允许状态栏直接读结果缓存（默认 True）。传 ``False``
                则强制向服务端要最新结果 —— **刚绑定完的那一次必须传它**，
                理由见 :meth:`_after_bound`。
        """
        from zmlx.ui.gui_buffer import gui

        try:
            gui.update_system_state(read_cache=read_cache)
        except Exception as err:
            print(f'刷新状态栏登录状态失败：{err}')

    # ------------------------------------------------------------------
    # 结果显示
    # ------------------------------------------------------------------

    def _show_status(self, text, elapsed=None):
        """把 ``check_web`` 的答复显示出来：**横幅一句话 + 原始答复区**。

        分工只有两条，别把中文解释再塞回 :attr:`status_view`：

        - 横幅（:attr:`status_label`）：**判定结论** —— 能用 / 没绑定 / 失败。
        - 答复区（:attr:`status_view`）：**只有两样东西** —— 服务器的原始字符串，
          以及本次往返耗时。逐字段的中文解释（姓名、单位、备注…）已经不再重复
          罗列：那些值在横幅里（邮箱）和预填的输入框里（姓名、单位）都能看到，
          再列一遍只是把同一份数据说第二遍。

        Args:
            text: ``web_license.check`` 返回的文本。
            elapsed: 本次查询的往返耗时（秒）；``None`` 表示没记录，此时不显示
                耗时那一行。
        """
        # 答复区：原始字符串 + 耗时，两行，不附加任何解释
        lines = [text or '(空响应)']
        timing = format_elapsed(elapsed)
        if timing:
            lines.append(timing)
        self.status_view.setPlainText('\n'.join(lines))

        # 横幅：只放结论
        if not text:
            # ⚠️ 拿不到答复 = **不知道**本机是不是还登录着 -> 收起退出按钮：
            #    宁可暂时不给这个动作，也不要在一个「状态未知」的界面上留一个
            #    会改变服务端状态的按钮。
            self.logout_button.setVisible(False)
            self.status_label.setText('未拿到任何答复（可能是网络中断）。')
            return

        detail = detail_of(text)
        source = find_field(detail, 'Source')
        email = find_field(detail, 'Email')
        # ★ 「在这台电脑上退出」按钮的**唯一**可见性判据（与横幅结论同一处算，
        #   避免两处各推一次、日后漂开）。
        #   ⚠️ 只有「服务端确实认了本机」才算已登录：默认配置（兜底记录）不是
        #   一次真正的登录，对它退出没有意义（服务端会回「这台机器没登记」）。
        logged_in = bool(is_yes(text)) and not (
            source and source.lower() == DEFAULT_SOURCE)
        self.logout_button.setVisible(logged_in)
        if not is_yes(text):
            self.status_label.setText('登录无效或查询失败（见下方服务器原话）。')
        elif source and source.lower() == DEFAULT_SOURCE:
            self.status_label.setText('尚未登录：当前用的是服务端默认配置。')
        elif email:
            # 已绑定时把邮箱放进横幅 —— 这是用户确认「绑对了没有」的唯一凭据
            self.status_label.setText(f'已登录：{email}')
        elif source:
            self.status_label.setText('已登录：本机可正常使用。')
        else:
            # ⚠️ 没有来源段不是异常：那句话只在「实际来源与请求的那一项不同」
            #    时才附上，所以有来源段反而不是常态。
            self.status_label.setText('登录有效。')

    def _show_failure(self, key, status, text):
        """把失败原因显示给用户（标题按动作区分）。

        ⚠️ **还要负责把横幅从「进行时」收回来**：`bind` / `send_code` 在发起时
        会把横幅改成「正在登录…」/「正在发送验证码…」，而这两句话只在请求**在飞**
        的那段时间成立。失败时不收回，横幅就永远停在那里 —— 既不再成立，又会让
        用户以为程序卡住了（见 :data:_Pending.FAILED）。
        ⚠️ **只收这两个动作**：其余动作的横幅里放的是**登录状态结论**，那些状态
        并没有因为一次失败而改变，去动它反而把正确的信息盖掉。

        Args:
            key: 请求标识。
            status: HTTP 状态码。
            text: 服务端原话。
        """
        titles = {'send_code': '发送验证码失败', 'bind': '登录失败',
                  'update_info': '更新信息失败', 'unbind': '退出失败'}
        title = titles.get(key, '操作失败')
        reason = explain_failure(status, text)
        self._log(f'错误：{title} —— {reason}')
        failed = _Pending.FAILED.get(key)
        if failed:
            self.status_label.setText(failed)
        QtWidgets.QMessageBox.warning(self, title, reason)

    # ------------------------------------------------------------------
    # 小工具
    # ------------------------------------------------------------------

    def _require_identity(self):
        """取并检查**必填**的姓名与单位（缺任一就提示、并把焦点移过去）。

        ⚠️ 这里卡的是「发验证码」与「注册」**两个动作**（见 :meth:`send_code`
        与 :meth:`register`）：署名只在服务端【创建】授权那一刻写进去，漏填就是
        永久缺失，所以绝不能等到 ``submit`` 才拦 —— 那时验证码已经发出去了，
        等于让用户白等一封信。

        Returns:
            tuple: 通过时返回 ``(user, org)``（已去首尾空白并限长）；
            不通过时提示用户并返回 ``None``。
        """
        user = self.user_edit.text().strip()[:MAX_USER_LEN]
        if not user:
            self.user_edit.setFocus()
            self._warn('还差一点', '请先填写姓名。\n\n'
                       '（姓名与单位会一并保存供作者核对；'
                       '漏填则以后补不回来。）')
            return None

        org = self.org_edit.text().strip()[:MAX_ORG_LEN]
        if not org:
            self.org_edit.setFocus()
            self._warn('还差一点', '请先填写单位。\n\n'
                       '（姓名与单位会一并保存供作者核对；'
                       '漏填则以后补不回来。）')
            return None

        return user, org

    def _require_email(self):
        """取并粗查邮箱（细的形态校验交给服务端，它的文案最准）。

        Returns:
            str: 通过时返回邮箱；不通过时提示用户并返回 ``None``。
        """
        email = self.email_edit.text().strip()
        if not email:
            self._warn('还差一点', '请先填写邮箱。')
            return None
        if '@' not in email or email.startswith('@') or email.endswith('@'):
            self._warn('邮箱格式不正确',
                       '请填写完整的邮箱地址，例如 you@example.com。')
            return None
        return email

    def _warn(self, title, message):
        """提示用户一处输入问题（并记一行日志）。

        Args:
            title: 对话框标题。
            message: 给用户看的话。
        """
        self._log(f'错误：{message}')
        QtWidgets.QMessageBox.warning(self, title, message)

    def _set_busy(self, busy):
        """切换「请求进行中」状态（按钮全禁用，防连点）。

        Args:
            busy: True 表示有请求在飞。
        """
        self._busy = bool(busy)
        self._update_buttons()

    @staticmethod
    def _is_running() -> bool:
        """主窗口当前有没有计算在跑（拿不到就按「没在跑」处理）。

        ⚠️ **必须惰性导入 + 整段 try**：本控件要能在没有主窗口时单独使用
        （见 :func:`test_1`），而那时 ``gui`` 只是个空壳缓冲对象。
        ⚠️ **失败方向选「没在跑」**：真判不出来时不该把一个正常功能永久禁用掉
        —— 而且 :meth:`logout` 里还有一道同样的判断兜着。

        Returns:
            bool: 有计算在跑返回 True。
        """
        try:
            from zmlx.ui.gui_buffer import gui
            return bool(gui.is_running())
        except Exception:
            return False

    def _update_buttons(self):
        """按当前状态刷新按钮可用性。

        ⚠️ 早先这里还要判「有没有配置注册服务地址」（``self.url``）。现在地址
        收在 C++ 侧、不对外暴露，控件无从配置也就无从缺失 —— 所以那道判断连同
        :meth:`set_url` 一并去掉。真正还可能缺的只剩硬件码（zml.dll 没加载时为
        空）—— 它界面上**不显示**，只在内部当「DLL 可用吗」的探针。
        """
        idle = not self._busy
        has_machine = bool(self.machine_code)

        self.send_button.setEnabled(idle)
        # ⚠️ 主按钮在**两种形态**下都要硬件码：注册（submit 靠机器码绑定）与
        #    更新（update_user_info 靠机器码认人）都离不开它。
        self.register_button.setEnabled(idle and has_machine)
        self.check_button.setEnabled(idle)
        # ★ 「在这台电脑上退出」：除了「空闲 + 有硬件码」，还**要求当前没有
        #   计算在跑** —— 退出会让本机立刻变成未登录，而正在跑的迭代下一步就会
        #   报「未登录」并反复弹本窗口，那种打扰没有意义（见 :meth:`logout`）。
        #   ⚠️ 判据用 ``gui.is_running()``（与 extra_setups/license_query.py 的
        #   「查询」菜单项同一条）：主窗口的 not_running 是它内部的闭包，这里拿不到。
        self.logout_button.setEnabled(
            idle and has_machine and not self._is_running())

        # 硬件码缺失时把原因说清楚，别让用户对着禁用按钮猜。
        # ⚠️ 文案按形态给（否则「无法绑定」会出现在一个写着「更新信息」的按钮上）。
        if not has_machine:
            self.register_button.setToolTip(
                '本机硬件码为空（zml.dll 未加载？），无法'
                + ('更新' if self._mode == _ProfileBox.MODE_UPDATE else '绑定'))

    def _log(self, message):
        """往日志框追加一行（同时写到标准输出）。

        ⚠️ 标准输出那一句**必须兜住异常**：Windows 控制台默认是 GBK，装不下
        ``✗`` 这类符号（真踩过：UnicodeEncodeError 直接把控件构造打断）。所以
        日志文本只用 GBK 编得出的字符，并且仍然兜一层。

        Args:
            message: 要记的一行文本。
        """
        text = str(message)
        try:
            print(text)
        except Exception:
            pass
        if hasattr(self, 'log_view'):
            self.log_view.appendPlainText(text)


def explain_failure(status, text) -> str:
    """把一次失败翻成一句给用户看的中文说明。

    只在**能确定原因**时补一句更友好的话；其余情况原样显示服务端的文案
    —— 那本身就是最准确的说明（例如 ``The code is incorrect.``）。

    ⚠️ **判据现在看正文，不再看 HTTP 状态码**。早先本控件自己发 HTTP，所以拿
    得到 429 / 503；现在走 ``web_license.send_code`` / ``web_license.submit``，它们按契约
    **不抛异常、也不回状态码**，一切失败都折叠成一句正文。好在服务端各状态的
    文案本就互不相同，辨认得出：

    ===========================================================  =================
    正文                                                         含义
    ===========================================================  =================
    ``a code was sent recently, please wait 412s and try again``  限流（原 429）
    ``Service temporarily unavailable``                           服务端故障（原 503）
    ``email ...`` / ``code ...``（C++ 侧本地校验）                 填写内容不合法
    ``dll not found`` / ``c++ api not defined``                   DLL 不可用
    其它（``TypeName: message`` 形态，来自 C++ 的异常描述）         多半是连不上
    ===========================================================  =================

    最后一条之所以能这么判：C++ 侧连不上 / 超时 / TLS 失败时返回的是
    ``SocketException...`` / ``Win32 error ...`` / ``域名解析失败...`` 这类
    异常描述，而**服务端**的文案永远是规整的英文句子。

    Args:
        status: 状态位（保留以兼容调用点，现在**不参与判断**）。
        text: 服务端（或本地校验）返回的正文。

    Returns:
        str: 一行中文说明。
    """
    del status        # 见上面的说明：状态码已不在新接口的契约里
    text = str(text or '').strip()
    if not text:
        return '没有拿到任何答复（可能是网络中断，或 zml.dll 未加载）。'

    lowered = text.lower()

    # 限流：服务端文案里带「还要等多少秒」。⚠️ 只认这句特征，**不要**用
    # 「含 sent」之类的宽判据 —— 这条文案本身就含 sent，宽判会把它当成功。
    if 'please wait' in lowered and 'try again' in lowered:
        return f'发送得太频繁了：{text}'

    if lowered.startswith('service temporarily unavailable'):
        return f'服务器暂时不可用（多半是发信或存储没配好）：{text}'

    # 本地形态校验（C++ 侧在发请求之前就挡下的那几种），都是小写英文短句
    if lowered.startswith(('email ', 'code ')):
        return f'填写内容不合法：{text}'

    # DLL 没加载或版本太旧（缺 lic_reg_* 符号）
    if lowered in ('dll not found', 'c++ api not defined'):
        return f'本机 zml.dll 不可用：{text}'

    # 其余：能对上「连不上」的典型形态就补一句，否则原样显示
    head, sep, _ = text.partition(':')
    if sep and head and head.isascii() and ' ' not in head and head[0].isupper():
        return f'连不上服务器：{text}'

    return text


def test_1():
    """单独跑起这个控件（人工检查界面 / 走一遍真实登录）。

    ⚠️ 要看到「在这台电脑上退出」按钮，得让本机**确实已登录**（横幅显示
    「已登录：<邮箱>」）才会出现；未登录时它按设计是藏着的。
    ⚠️ 这个入口连的是**真实服务端**：点那个按钮会真的退出登录（可再登录恢复）。
    """
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = LicenseRegister()
    widget.resize(720, 560)
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()

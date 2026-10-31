"""许可证管理绑定.

本模块定义两个类，以及各自的模块级单例：

- :class:`License` —— **本机**的授权信息（授权码、序列号、硬件指纹、有效性
  检查），一律不联网，单例为 :data:`lic`；
- :class:`WebLicense` —— 需要**联网**的功能（``machine_id`` /
  ``check`` / ``feedback`` / ``mail`` / ``check_count`` / ``user_list`` /
  ``list_feedbacks`` / ``get_feedback`` /
  ``send_code`` / ``submit`` / ``version`` / ``request``），单例为 :data:`web_license`。
  ⚠️ 这些方法会阻塞（单次最长 60 秒），与「读一下本机授权码」那类本地查询是两回事。

★ **各动作的成功记号**（判成败只看**开头那个词**，不区分大小写）：

    ==========================  ================================================
    动作 / 记号                   含义
    ==========================  ================================================
    ``check``                   ``Yes``        **授权有效**
    ``feedback``                ``Succeed``    **反馈已收**
    ``mail``                    ``Mail sent``  **代发的那封信已发出**
    ``check_count``             ``Count:``     **统计结果**
    ``user_list``               ``Users:``     **名单结果**（仅管理员）
    ``list_feedbacks``          ``Feedbacks:`` **文件名列表**（复数）
    ``get_feedback``            ``Feedback:``  **一条反馈的内容**（单数）
    ``send_code``               ``Sent``       **验证码邮件已发出**
    ``submit``                  ``OK``         **邮箱已注册**
    ``submit`` + ``machine_code``  ``Bound``   **本机已绑定**
    ``version``                 版本号文本     **运维探测**（无副作用）
    ==========================  ================================================

⚠️ **绝不要**用「包含」判断，也不要拿一个动作的记号去判另一个动作。
各记号的辨别要点与服务端的保险丝见
``zmlx/_private/AUTHORIZATION_NOTES.md`` §3。

⚠️ 下面那些联网方法**永不抛异常**：一切失败（连不上、超时、服务端报错、参数
非法）都以**一句描述文本**返回。判定成功与否请比较正文开头，**不要**用 ``==``
严格相等 —— 那是一条会随服务端演进而失效的隐含假设。
判定函数由调用方自备（本模块的模块级**不提供**任何判定函数或常量）。

协议细节（请求体形态、各动作权限、服务端约束、失败模式）见
``zmlx/_private/AUTHORIZATION_NOTES.md``。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
import base64
import binascii
import json
import sys
from ctypes import c_bool, c_char_p, c_double, c_int

from zmlx.exts._dll import DllCore, core, make_c_char_p
from zmlx.exts._utils import app_data


#: 机器码在请求体里的**字段名**。
#:
#: ★★ **服务端 v3.30 起叫 ``machine_id``**（此前叫 ``name``）。本库**只发这一个
#: 字段**，旧的 ``name`` **一律不再发**（用户 2026-10-18：机器码以后一律用
#: machine_id，「这个版本中，客户端一律不再采用 name」）。服务端对 ``name`` 只是
#: **永久兼容**，v3.33 起两个都给时还会**静默忽略** ``name`` —— 静默正是我们不想
#: 再有的东西，所以从源头就不再写它。
#:
#: ⚠️ 与 ``machine_code`` **不是**一回事：那个只出现在 ``submit`` 里，含义是
#: 「**要绑定哪台**」（动作的对象）；本字段是「**我是哪台**」（调用者的身份）。
#: 方向正好相反，两个名字都要保留。
#:
#: ⚠️ 服务端日志与响应里**不出现字段名**，所以改名对它们零影响。
FIELD_MACHINE_ID = 'machine_id'


class License:
    """管理软件的授权信息。

    该类用于管理软件的授权信息，包括获取授权信息、检查授权状态、生成授权码等功能。

    ⚠️ **本类不联网**：需要访问服务器的那些功能在 :class:`WebLicense` 上，
    单例为 :data:`web_license`。
    """

    def __init__(self, core_obj: DllCore):
        """初始化 License 对象。

        Args:
            core_obj: 核心模块对象，用于调用底层功能。
        """
        self.core = core_obj
        self.license_info_has_checked = False
        if self.core.has_dll():
            self.core.use(c_bool, "lic_is_admin")
            self.core.use(c_int, "lic_webtime")
            self.core.use(c_bool, "lic_valid")
            self.core.use(c_char_p, "lic_desc")
            self.core.use(c_char_p, "lic_serial", c_bool)
            self.core.use(c_char_p, "lic_create", c_char_p)
            self.core.use(None, "lic_load", c_char_p)
            self.core.use(c_char_p, "lic_hw_fingerprint")
            self.core.use(c_double, "lic_hw_match_fingerprints", c_char_p, c_char_p)
            # ⚠️ 需要联网的那几个导出（lic_machine_id / lic_check_web /
            #    lic_request）**不在这里登记** —— 它们归 WebLicense。

    @property
    def is_admin(self) -> bool:
        """检查当前计算机是否具有管理员权限。

        Returns:
            bool: 是否具有管理员权限。
        """
        if self.core.has_dll():
            return self.core.lic_is_admin()
        else:
            return False

    @property
    def webtime(self) -> int:
        """获取网络时间戳（非实际时间）。

        程序将使用此时间戳来判断软件是否已过期。

        Returns:
            int: 网络时间戳。
        """
        if self.core.has_dll():
            return self.core.lic_webtime()
        else:
            return 100101

    @property
    def valid(self) -> bool:
        """检查当前计算机是否已经登录。

        Returns:
            bool: 当前计算机是否已经登录
        """
        if self.core.has_dll():
            return self.core.lic_valid()
        else:
            return False

    @property
    def desc(self) -> str:
        """获取当前登录信息的描述。

        Returns:
            str: 当前登录信息的描述。
        """
        if self.core.has_dll():
            return core.lic_desc().decode()
        else:
            return ""

    def get_serial(self, base64: bool = True, export_all: bool = False) -> str:
        """获取当前计算机的 USB 序列号，用于注册。

        Args:
            base64: 是否以 Base64 格式返回序列号。
            export_all: [已弃用] 该参数不再生效，将在 2027-01-01 后移除。

        Returns:
            str: USB 序列号。
        """
        if export_all:
            import warnings

            warn(
                "export_all is deprecated and has no effect. "
                "It will be removed after 2027-01-01.",
                DeprecationWarning,
                stacklevel=2,
            )
        if self.core.has_dll():
            return self.core.lic_serial(base64).decode()
        else:
            return ""

    def create(self, base64_serial: str) -> str:
        """根据 USB 序列号生成永久授权码。

        仅用于测试。

        Args:
            base64_serial (str): USB 序列号。

        Returns:
            str: 永久授权码。
        """
        if self.core.has_dll():
            return self.core.lic_create(make_c_char_p(base64_serial)).decode()
        else:
            return ""

    def load(self, code: str):
        """将给定的登录码存储到默认位置。

        Args:
            code (str): 登录码。
        """
        if self.core.has_dll():
            self.core.lic_load(make_c_char_p(code))

    @property
    def usb_serial(self) -> str:
        """获取当前计算机的 USB 序列号（其中之一），用于注册。

        Returns:
            str: USB 序列号。
        """
        return self.get_serial()

    def check(self):
        """检查登录状态。

        如果当前计算机已正确登录，则函数正常通过；否则触发异常。
        """
        assert self.valid, "The license is not valid on this computer."

    def check_once(self):
        """在迭代过程中检查登录状态。

        如果登录状态未检查过，则执行检查并输出提示信息。
        """
        if not self.license_info_has_checked:
            self.license_info_has_checked = True
            if app_data.has_tag_today("lic_checked"):
                return
            else:
                app_data.add_tag_today("lic_checked")
            if not self.valid:
                text = f"""
The software is not licensed on this computer. Please send the following 
code to author (zhangzhaobin@mail.iggcas.ac.cn):
     <{self.usb_serial}>
Thanks for using.
    """
                print(text)

    @property
    def fingerprint(self) -> str:
        """获取当前计算机的硬件指纹。

        Returns:
            str: 硬件指纹字符串。
        """
        if self.core.has_dll():
            return self.core.lic_hw_fingerprint().decode()
        else:
            return ""

    def match_fingerprints(self, fp1: str, fp2: str) -> float:
        """比较两个硬件指纹的匹配度。

        Args:
            fp1: 第一个指纹字符串
            fp2: 第二个指纹字符串

        Returns:
            float: 匹配度 (0.0 ~ 1.0)
        """
        if self.core.has_dll():
            return self.core.lic_hw_match_fingerprints(
                make_c_char_p(fp1), make_c_char_p(fp2)
            )
        else:
            return 0.0


class WebLicense:
    """管理需要**联网**的授权功能。

    与 :class:`License` 的分工：:class:`License` 只管**本机**的授权信息（授权
    码、序列号、硬件指纹、是否有效），一律不联网；本类管**与服务器打交道**的
    那几件事 —— 查在线授权、提交反馈、代发邮件、邮箱验证码注册 / 绑定。

    ★★ **对外可以调用的就是下面这些方法**（模块级单例 ``web_license`` 上的
    同名方法，例如 ``from zmlx.exts import web_license`` 之后
    ``web_license.check('flow')``）。⚠️ ``core`` 与 ``checked_features`` 是
    **内部状态**，外部一律不要碰。

    ============================  =========  ==============================
    方法                           返回       成功的记号（只看开头）
    ============================  =========  ==============================
    :meth:`machine_id`            ``str``    ——（空串 = 取不到 / 无 DLL）
    :meth:`check`                 ``str``    ``Yes``
    :meth:`check_once`            ``None``   ——（不返回结论，见该方法）
    :meth:`feedback`              ``str``    ``Succeed``
    :meth:`mail`                  ``str``    ``Mail sent``
    :meth:`check_count`           ``str``    ``Count:``
    :meth:`user_list`             ``str``    ``Users:``
    :meth:`list_feedbacks`        ``str``    ``Feedbacks:``（**复数**）
    :meth:`get_feedback`          ``str``    ``Feedback:``（**单数**）
    :meth:`get_feedback_bytes`    ``bytes``  ——（``None`` = 业务拒绝 / 连不上）
    :meth:`send_code`             ``str``    ``Sent``
    :meth:`submit`                ``str``    ``Bound``
    :meth:`version`               ``str``    版本号文本（无副作用）
    :meth:`request`               ``str``    **按 action 定**（见该方法）
    :meth:`decode_feedback`       ``bytes``  ——（纯解析，不联网）
    ============================  =========  ==============================

    ⚠️ **上表里除** :meth:`decode_feedback`（静态方法，纯解析）**之外的方法都不会
    抛异常**：连不上、超时、服务端报错、参数非法……一律以**一句文本**返回。
    所以外部**不需要**再套「有没有 DLL / 有没有这个导出」的前置判断 ——
    **没有 DLL 时它们照样返回一句描述**，照常按「返回值不是成功记号」处理即可。

    ⚠️ **本类的方法会阻塞**（底层 C++ 单次请求最长 60 秒），因此在界面里调用
    必须放进后台线程，**绝不能**直接在界面线程里调。

    热路径（如 ``Seepage.iterate()``）里请不要直接调 :meth:`check` —— 那会
    每次都联网。要「顺带查一次」请用 :meth:`check_once`。

    本类对 DLL 的依赖、``check`` 为何不走薄转发、各动作的权限模型与服务端约束，
    见 ``zmlx/_private/AUTHORIZATION_NOTES.md`` §4 / §6 / §8。
    """

    def __init__(self, core_obj: DllCore):
        """初始化 WebLicense 对象。

        Args:
            core_obj: 核心模块对象，用于调用底层功能。
        """
        self.core = core_obj
        # 本次运行**已经查过**的 feature 集合：check_once 的闸门。
        # ⚠️ 必须**按 feature 分开**存放（在线授权是按 feature 授予的），
        #    与 License.license_info_has_checked 互不影响。
        self.checked_features = set()
        if self.core.has_dll():
            # ★★ 本类只需要三个导出：机器码、唯一的网络出口、许可查询。
            #
            #    ① 机器码：只为了 machine_id()。
            self.core.use(c_char_p, "lic_machine_id")
            #    ② 唯一的网络出口：收一整段请求体 JSON，原样发出去、把服务端那句
            #       纯文本原样带回。
            self.core.use(c_char_p, "lic_request", c_char_p)
            #    ③ **许可查询**（:meth:`check`）**刻意不走** ``lic_request``。
            self.core.use(c_char_p, "lic_check_web", c_char_p, c_bool)
            #
            # ⚠️ 各导出的取舍、为何 check 是例外、旧 DLL 的兼容性，见
            #    ``zmlx/_private/AUTHORIZATION_NOTES.md`` §4 / §6。

    # ------------------------------------------------------------------
    # 机器码
    # ------------------------------------------------------------------

    def machine_id(self) -> str:
        """获取当前计算机硬件指纹的 SHA-256 短串（纯 hex，可用作文件名）。

        ⚠️ 这是**函数**不是属性 —— 取值必须带括号：``web_license.machine_id()``。
        （写成 ``web_license.machine_id`` 会拿到函数对象本身，而它恒为真，
        判空 / 拼接都会静默出错。）

        ⚠️ **取不到时返回空串**（不是 ``None``）—— 调用方一律按「空串 = 用不了」
        处理即可。

        Returns:
            str: 机器码字符串；无 DLL 或取不到时返回空串。
        """
        if not self.core.has_dll():
            return ""
        res = self.core.lic_machine_id()
        if res is None:
            return ""
        return res.decode()

    # ------------------------------------------------------------------
    # 网络出口
    #
    # ⚠️ 除 :meth:`check`（走 ``lic_check_web``）之外，本类**所有**网络动作都从这里
    #    出去 —— 拼 JSON 的那件事只在本节里发生。
    # ------------------------------------------------------------------

    def _send(self, payload: dict) -> str:
        """（私有）把一份**已经拼好**的 payload 编码成请求体并走 ``lic_request``。

        ⚠️ 本函数**不碰字段**：只负责 ``json.dumps`` 与 :meth:`_call`。
        ★ **全类的 JSON 序列化只在本函数里发生**。

        Args:
            payload: 完整的请求体字典。

        Returns:
            str: 服务端回应正文；或一句本地错误描述。**不抛异常**。
        """
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        return self._call(body)

    def _request(self, action: str, **fields) -> str:
        """（私有）拼好**带机器码**的请求体并走 ``lic_request``。

        ⚠️ 与公开的 :meth:`request` 的分工：那个是**给调用方用的新动作入口**，
        这个是**给本类自己的那几个方法用的内部出口**（字段由方法自己算好）。

        ⚠️ **它只往请求体里塞两样东西**：``action`` 与机器码 ``machine_id``
        （★ 2026-10-18 起不再发旧字段 ``name``，见 :data:`FIELD_MACHINE_ID`）。
        少数几个动作**不该带**机器码，它们走 :meth:`_request_plain`。

        Args:
            action: 服务端动作名。
            **fields: 该动作的其余字段；值 ``None`` 的**整段不发**。

        Returns:
            str: 服务端回应正文；或一句本地错误描述。**不抛异常**。
        """
        try:
            machine = str(self.machine_id() or '')
        except Exception as e:
            return f"Failed to get the machine code: {e}"
        if not machine:
            return "Failed to get the machine code (empty)"
        payload = {'action': action, FIELD_MACHINE_ID: machine}
        for key, value in fields.items():
            if value is None:
                continue
            payload[key] = value
        return self._send(payload)

    def _request_plain(self, action: str, **fields) -> str:
        """（私有）拼好**不带机器码**的请求体并走 ``lic_request``。

        ⚠️ 只在**确实不需要认人**的动作上调用它（当前只有 ``send_code`` / ``version``）：
          * ``send_code`` —— 服务端只按邮箱发码，不认机器；
          * ``version`` —— 服务端在校验请求体之前就答了。
        ★ ``submit`` **不在**这里：它要带机器码（只是字段名同样是 ``machine_id``），
        走 :meth:`_request`。
        ⚠️ **不要**为了「少一次取机器码」而把别的动作改到这里。

        Args:
            action: 服务端动作名。
            **fields: 该动作的字段；值 ``None`` 的**整段不发**。

        Returns:
            str: 服务端回应正文；或一句本地错误描述。**不抛异常**。
        """
        payload = {'action': action}
        for key, value in fields.items():
            if value is None:
                continue
            payload[key] = value
        return self._send(payload)

    def _call(self, body: str) -> str:
        """（私有）把一整段请求体交给 ``lic_request``，原样带回答复。

        ⚠️ 只有**一处**碰 DLL 的返回：空/None 都折叠成一句描述。本方法承诺
        **不抛异常**（``DllCore.run()`` 在 C++ 侧报告错误时会 raise RuntimeError，
        这里就地处住）。

        Args:
            body: 完整请求体 JSON。

        Returns:
            str: 服务端回应正文，或一句本地错误描述。
        """
        if not self.core.has_dll():
            return "dll not found"
        # ⚠️⚠️ **必须查一次「这个导出到底在不在」**：``lic_request`` 是后加的导出，
        #    **旧 DLL 里没有它**。判据只能用 ``is_null_func()``（``use()`` 找不到
        #    符号时会登记 ``_NullFunction`` 占位符，故
        #    ``get_dll_funcs().get(name) is None`` **测不出来**）。
        if self.core.is_null_func('lic_request'):
            return "dll not found"
        try:
            res = self.core.lic_request(make_c_char_p(body))
        except Exception as e:
            return f"Failed to query the license server: {e}"
        if res is None:
            return "Failed to query the license server."
        return res.decode()

    def request(self, **opts) -> str:
        """把 ``action`` 与若干字段发给服务端，答复**原样**带回（**永不抛异常**）。

        ★★ **本方法存在的意义**：服务端只有一个接口（``POST /``），靠请求体里的
        ``action`` 分流、回**一句纯文本**。有了本方法，**服务端以后再加动作，
        只需要在调用方多写一行** —— 不用改 C++、不用重编 DLL（本类里那些
        专用方法都是它的特例）。

        ★★ **本方法替你拼好请求体**：

            ``action``            **必需**
            ``machine_id``        **默认自动填本机机器码**（:meth:`machine_id`）；
                                  显式传就按你给的那个发；传空串则该字段**不发**
                                  ★ 旧的 ``name`` 仍接受**当别名**（就地映射过来，
                                  **绝不**原样发出去）
            其余关键字            **原样进请求体**（值 ``None`` 的**整段不发**）

        ⚠️ 认不出的动作名**不会在本地被拦下**，服务端对未知 action 一律当许可查询
        —— 所以**拼错一个字母是看不出来的**，请对着服务端协议抄那个名字。

        Args:
            **opts: 请求体的字段。两个**保留名**：

                * ``action`` —— 动作名（例如 ``'check_count'`` / ``'user_list'``）。
                  **必填**、非空、ASCII。
                * ``machine_id`` —— 机器码。**不传就自动填本机机器码**（推荐）；
                  传字符串就原样用它（调试别的机器码时才需要）；传空串表示
                  **不发这个字段**（``version`` 这类不认人的动作）。
                  ★ 旧的 ``name`` 是它的**别名**（映射过来、**不**原样发出）；
                  两个都给且不一致时**本地就拒** —— 服务端 v3.33 会静默忽略
                  ``name``，那种静默正是本库刻意避免的。

                其余关键字**原样进请求体**。值可以是 JSON 原生类型
                （``str`` / ``int`` / ``float`` / ``bool`` / ``dict`` / ``list``）；
                ⚠️ **值 ``None`` 的字段整段不发**。
                ⚠️ **刻意不在这里做服务端那套形态校验**（日期是不是
                ``YYYY-MM-DD``、邮箱合不合法）：那些文案归服务端拥有，本地复写
                一份必然漂。

        Returns:
            str: 服务端回应正文（成功或业务拒绝，见服务端协议）；或一句本地错误
            描述（**无 DLL** / **旧 DLL 里没有 ``lic_request``** / 缺 ``action`` /
            机器码取不到 / 连不上）。**任何情况下都不抛异常**。
            ⚠️ **判成功请按该动作的成功记号看开头**，**不要**用整串比较，也**不要**
            把某一个动作的记号拿去判另一个动作。

        ⚠️ **本方法不做缓存、不记失败次数**，每次调用都真的发出去 —— 与
        :meth:`check` **刻意不同**（那是查询，同一结论可复用）。本方法**绝不**
        能用来替代 :meth:`check`。

        示例::

            # 认人的动作：machine_id 自动填本机机器码
            web_license.request(action='user_list')

            # 带参数的
            web_license.request(action='check_count',
                                email='someone@example.com',
                                **{'from': '2026-10-01', 'to': '2026-10-07'})

            # 不认人的动作：显式给空 machine_id，那个字段就不发
            web_license.request(action='version', machine_id='')

        Added by DeepSeek, 2026-10-10
        """
        # ⚠️ 本地就挡下**缺 action / 空 action**：服务端会把空 action 当成「默认
        #    动作 = 许可查询」，于是传错参数的调用方会收到一个看起来正常的 ``Yes``
        #    —— 这种「假成功」正是本项目最忌讳的。⚠️ 文案是 ASCII，且不以任何
        #    动作的成功记号开头（与其余本地错误同一条纪律）。
        action = opts.pop('action', None)
        if not isinstance(action, str) or not action.strip():
            return 'Bad request: "action" is required'

        # ★★ 机器码字段：``machine_id``（服务端 v3.30 起；本库只发这一个，见
        #    :data:`FIELD_MACHINE_ID`）。
        # ⚠️ 旧的 ``name`` 关键字**仍接受**（外部脚本可能还在用），但只当**别名**：
        #    就地映射成 ``machine_id``，**绝不会**原样进请求体。
        #    ⚠️ 两个都给且不一致 -> **本地**就拒。服务端 v3.33 起会静默忽略
        #    ``name``（按 machine_id 执行），那种「看着成功、其实按另一台机器办」
        #    正是本库最忌讳的，所以在自己家门口就挡掉。
        if 'name' in opts:
            legacy_machine = opts.pop('name')
            if FIELD_MACHINE_ID not in opts:
                opts[FIELD_MACHINE_ID] = legacy_machine
            elif (str(legacy_machine or '').strip()
                  and str(opts[FIELD_MACHINE_ID] or '').strip()
                  and str(legacy_machine).strip() != str(opts[FIELD_MACHINE_ID]).strip()):
                return ('Bad request: "machine_id" and "name" conflict')

        # ⚠️ ``machine_id`` 的三条规则：没传 -> 自动填机器码；传了 -> 原样用；
        #    传空串 / 全空白 -> **不发这个字段**（不认人的动作走这条）。
        #    ⚠️ 绝不能发一个**空串**出去：实测那会换来一句与真实原因无关的
        #    ``Bad request``。
        if FIELD_MACHINE_ID not in opts:
            try:
                machine = str(self.machine_id() or '')
            except Exception as e:
                return f"Failed to get the machine code: {e}"
            if not machine:
                return ("Failed to get the machine code "
                        "(empty) - pass machine_id='' explicitly if this action "
                        "does not need one")
            opts[FIELD_MACHINE_ID] = machine
        else:
            given = opts[FIELD_MACHINE_ID]
            if given is None or not str(given).strip():
                del opts[FIELD_MACHINE_ID]
            else:
                opts[FIELD_MACHINE_ID] = str(given)

        payload = {'action': action, **opts}
        return self._send(payload)

    # ------------------------------------------------------------------
    # 在线授权查询
    # ------------------------------------------------------------------

    def check(self, feature: str, read_cache: bool=True) -> str:
        """从web上检查，给定的 feature 是否授权。

        ⚠️ **不抛异常**：连不上 / 超时 / TLS 失败都以**一句文本**返回
        （就是底层错误原文）。

        判定成功请**只看开头**（前 3 字符忽略大小写为 ``yes``），不要整串比较。

        ⚠️ **本方法是本类唯一【不走】** :meth:`request` 的网络动作 —— 它走
        ``lic_check_web``，那里有薄转发拿不到的东西（本地白名单、按 feature 的
        长期缓存、失败到上限就冻住）。理由与取舍见
        ``zmlx/_private/AUTHORIZATION_NOTES.md`` §4。

        ★★ **``read_cache`` 的语义**（它只对本方法有效）：

            ``True`` （默认） 允许复用**线上查询**的缓存 —— 本机已有结论时**不发**
                              网络请求；
            ``False``         **绕过缓存、强制连一次服务器**。
                              ⚠️ 新注册 / 新绑定之后做自检**必须**传 ``False``，
                              否则会读到绑定前缓存下来的那句
                              ``Please register with your email first.``

        Args:
            feature: 功能名称
            read_cache: 是否允许复用**线上查询**的缓存，默认 ``True``。

        Returns:
            str: 已授权返回 "Yes" 开头（可能带 `` | `` 说明段）；否则返回失败原因
            （未授权、连不上、无 DLL 等）。
        """
        if not self.core.has_dll():
            return "dll not found"
        # ⚠️ 与其余方法不同：**这里不查 is_null_func**。``lic_check_web`` 是
        #    **老导出**，正常 DLL 里恒有。
        try:
            res = self.core.lic_check_web(make_c_char_p(feature), read_cache)
        except Exception as e:
            # ⚠️ 防御性：本方法承诺**永不抛异常**，而 DllCore.run() 在 C++ 侧
            #    报告错误时会 raise RuntimeError。
            return f"Failed to query the license server: {e}"
        if res is None:
            return "Failed to query the license server."
        return res.decode()

    def check_once(self, feature: str = '*'):
        """在迭代过程中检查**在线**授权状态（**每个 feature 每次运行最多查一次**）。

        可以放心地放在 ``Seepage.iterate()`` 这类热路径里调用：**每个 feature**
        在一次运行里只有第一次可能联网，其余调用都在闸门处直接返回。

        ⚠️ **闸门按 feature 分开**（不是全局一个）—— 共用一道闸门会让同一轮里
        后面的 feature 被静默跳过（**漏检**）。

        ⚠️ **闸门是「先登记、后查询」**：这一次查询**无论成败都算查过**（断网的那
        一次不会被下一轮迭代重试）。这是**刻意的**。

        ⚠️ **闸门只在本次运行内有效**：每个 feature 每次运行都会真查一次，重启即
        重新检查（不再有跨进程的每日闸门）。

        闸门设计的完整理由见 ``zmlx/_private/AUTHORIZATION_NOTES.md`` §5。

        ⚠️ **本方法会联网**（走 :meth:`check`，单次请求最长 60 秒），所以它不是
        零代价的。

        ⚠️ **本方法不抛异常、也不返回任何值**：一切失败（连不上、超时、无 DLL）
        只把服务端原话打印出来，绝不影响迭代。授权与否的判断留给业务层
        —— 与 :meth:`License.check_once` 的取舍一致。

        ⚠️ **未授权时还会顺手弹注册窗口**：处于 GUI 模式（``gui.exists()``）时
        调一次 ``gui.show_reg_tool()``。该调用整段 try 住、且是惰性导入，失败绝不
        影响迭代（无 GUI 时它什么也不做）。

        Args:
            feature: 要查询的功能名。**每个功能名一套闸门**：
                迭代路径用 ``'flow'``（流动，见 ``FlowSol.iterate``）与
                ``'thermal'``（传热，见 ``ThermalSol.iterate`` /
                ``Thermal.iterate``）；界面自检用 ``'*'``（见
                ``zmlx.ui.utils.lic_utils.CHECK_FEATURE``）。
        """
        if feature in self.checked_features:
            return
        self.checked_features.add(feature)
        try:
            reply = str(self.check(feature, read_cache=True) or '')
        except Exception as err:        # 防御：check 按契约不抛异常
            reply = f'Failed to query the license server: {err}'
        # ⚠️ 在线授权的成功记号是 'Yes'（前 3 字符），**不是** 'Succeed' /
        #    'Mail sent' / 'Sent' / 'Bound' —— 那是另外几个动作的记号，
        #    拿混了会把成功读成失败。
        if reply.strip()[:3].lower() == 'yes':
            return
        try:
            machine = str(self.machine_id() or '')
        except Exception:               # 取机器码失败不能影响提示的打印
            machine = '(unavailable)'
        # ⚠️ **登录入口要写清楚**（用户看到这段字时正卡在迭代里，越具体越好）：
        #    GUI 的「帮助 -> 用户 -> 登录」菜单项（见 zmlx/ui/main.py），打开的是
        #    LicenseRegister 控件。
        text = f"""
The software is not logged in for feature <{feature}> on this computer.
Please log in in the GUI: 菜单 -> 帮助 -> 用户 -> 登录 (Menu -> Help -> User -> Login),
or send the following code to author (zhangzhaobin@mail.iggcas.ac.cn):
     <{machine}>
License server reply:
     {reply.strip()}
Thanks for using.
    """
        try:
            print(text, file=sys.stderr)
        except Exception:
            # ⚠️ 打印只是**提示**，绝不能让它把异常带进迭代：控制台编码装不下
            #    中文时（例如重定向到 cp437 的终端），降级成纯 ASCII 再打一次。
            #    本方法的契约是「不抛异常」。
            print(text.encode('ascii', 'replace').decode('ascii'))
        # ⚠️ 在 GUI 模式里**替用户点一下「菜单 -> 帮助 -> 用户 -> 登录」**（窗口会自动弹到
        #    最前面）—— 打印出来的入口提示，用户在界面上多半是看不到的。
        #    与 ``gui.*`` 家族一致地做**惰性导入**（``zmlx.exts._utils`` 反过来
        #    import 了 ``zmlx.system``，在模块顶层导入 zmlx.ui 不值得冒险），
        #    并且整段 try 住：本方法在迭代路径上，绝不能因为界面 / 导入问题
        #    把异常带进去。
        try:
            from zmlx.ui.gui_buffer import gui
            if gui.exists():
                gui.show_reg_tool()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 反馈 / 代发邮件 / 统计 / 名单 / 反馈读取
    # ------------------------------------------------------------------

    def feedback(self, text: str) -> str:
        """把一段反馈文本提交给作者。

        机器码由本方法自己补进请求体（就是 :meth:`machine_id`），**不需要也不能传**。

        ⚠️⚠️ **成功记号是 ``'Succeed'``，不是 ``'Yes'``** —— 判据是前 7 字符忽略
        大小写为 ``succeed``。拿判 ``Yes`` 的那段去判本方法会把**成功读成失败**。

        ⚠️ **限流时**返回的那句话里的秒数是**精确的剩余等待时间**，请原样显示给
        用户（不要丢掉，也不要自己编一句「稍后再试」）。

        ⚠️ **超长是「截断后成功」，不是失败**：服务端截断后仍然回 ``Succeed``，
        只在后面追加一段说明。★ **绝不要在这里做本地截断** —— 服务端要按**原文**
        算「被截掉多少」并回报；本地先截一刀会让那个数字撒谎。

        ⚠️ **本方法不做缓存、每次调用都真的发出去** —— 这是**用户的一次动作**。

        ⚠️ **本方法不抛异常**：连不上、超时、限流……一律以一句文本返回。

        Args:
            text: 反馈正文（**原样发出，不截断**）。空串或纯空白会被服务端拒绝。

        Returns:
            str: 服务端回应正文。成功时以 ``'Succeed'`` 开头。
        """
        return self._request("feedback", data=text)

    def mail(self, to: str, subject: str, text: str) -> str:
        """用服务端的邮箱**代发一封普通邮件**（通知、告警之类）。

        机器码由本方法自己补进请求体，**不需要也不能传**。

        ★ **只有「已注册且授权当前有效」的机器发得出去**（这是**服务端**的门，
        本地不重复判、也不放宽）。

        ⚠️⚠️ **成功记号是 ``'Mail sent'``（中间有个空格）** —— 前 9 个字符忽略
        大小写为 ``mail sent``。**不要**用判 ``Yes`` 的那段，也**不要**用判
        ``Sent`` 的那个（``Mail sent`` 的前 4 个字符是 ``mail``），都会把**成功
        读成失败**。

        ⚠️ **限流是「每个用户」而非每台机器**（同一个人的多台机器**共用**配额）。
        超限时返回的秒数是**精确的剩余等待时间**，请原样显示给用户。

        ⚠️ **正文超长是「截断后成功」，主题超长是「直接拒」**（这个不对称是刻意
        的）。★ **绝不要在这里做本地截断** —— 服务端要按**原文**算「被截掉多少」。

        ⚠️ **发件人是谁不由本方法决定**：SMTP 不接受伪造发件地址，收件人看到的
        地址恒为服务端内置账号；「发件人就是这个用户」只体现在**显示名**上。
        所以**没有**发件人参数。

        ⚠️ **本地不预检收件人 / 主题 / 正文**：明显非法的形态会**照样发出去**，
        由**服务端**回一句文案。文案仍然准确，代价是**多一次网络往返**。

        ⚠️ **本方法不抛异常**：连不上、超时、限流……一律以一句文本返回。

        Args:
            to: 收件邮箱。形态由服务端校验。
            subject: 主题。**超长会被拒**，不做截断。
            text: 正文（**原样发出，不截断**）。

        Returns:
            str: 服务端回应正文。成功时以 ``'Mail sent'`` 开头。
        """
        return self._request("send_mail", mail_to=to,
                             mail_subject=subject, mail_text=text)

    def check_count(self, email: str, from_: str = "", to: str = "") -> str:
        """查某个邮箱对应用户的**许可查询次数**（按天）.

        机器码由本方法自己补进请求体，**不需要也不能传** —— 服务端据此判断
        **你是谁**，再决定你能不能查那个邮箱。

        ★★ **权限**（服务端的门，本地不重复判、也绝不放宽）：管理员可查**任意**
        邮箱，其他人**只能查自己绑定的那个**。

        ⚠️⚠️ **防枚举：越权者的答复与「那个邮箱根本不存在」逐字相同**
        （都是 ``Not permitted.``）。所以**不要**试图区分那两种情况，也**不要**
        给用户编一句「这个邮箱不存在」。

        ⚠️ **``Not permitted.`` 是正常业务答复**（HTTP 200），不是异常、也不是
        连接失败 —— 界面应当原样显示给用户。

        ⚠️⚠️ **成功记号是 ``'Count:'``（注意那个冒号，前 6 个字符）** ——
        **不要**拿判 ``Yes`` 的那段去判本方法，也不要用判 ``Users:`` 的那段
        （两者只差前面那个词），都会把**成功读成失败**。

        ★★ **``Count:`` 后面那串数字的形状由服务端保证，调用方【不要】重新
        解析**：个数 = 区间天数（闭区间两端都含）、逐日连续不跳号、顺序是
        「最早 -> 最新」。服务端回的 ``Range:`` 段已经是权威答案。

        ⚠️ **日期一律 ``YYYY-MM-DD``（10 个字符）**。本方法**不做本地日期校验**
        —— 形态、区间顺序、上限的文案都归服务端拥有。

        ⚠️ ``from_`` / ``to`` **都留空**时服务端回**最近 60 天（含今天）**。

        ⚠️ **本方法不抛异常**：连不上、超时、越权……一律以一句文本返回。

        Args:
            email: 要统计**谁**的邮箱。非管理员传别人的邮箱只得到
                ``Not permitted.``（与「邮箱不存在」逐字相同）。
            from_: **可选**起始日（``YYYY-MM-DD``）；留空表示不发该字段。
                ⚠️ 名字带下划线是因为 ``from`` 是 Python 关键字。
            to: **可选**结束日（``YYYY-MM-DD``，**闭区间含**这一天）；留空同上。

        Returns:
            str: 服务端回应正文。成功时以 ``'Count:'`` 开头。

        Added by DeepSeek, 2026-10-05
        """
        # ⚠️ 空的日期字段**不发**（服务端把「没给」与「给了空串」都当没给，
        #    但不发更干净 —— 与 C++ 侧那几个专用导出同一条写法）。
        return self._request("check_count", email=email,
                             **{"from": from_ or None, "to": to or None})

    def user_list(self) -> str:
        """取**用户名单**（**仅管理员**）.

        机器码由本方法自己补进请求体 —— 服务端据此判断**你是不是管理员**。

        ★★ **本方法【没有参数】，这是刻意的安全设计**：列举的范围是服务端写死的
        常量，客户端**只能传机器码、不能传路径**。

        ★ **「非管理员不读」是服务端的结构性保证**（那边判权限排在列举**之前**），
        所以非管理员**连「桶里有没有用户」都探测不到**。

        ⚠️⚠️ **成功记号是 ``'Users:'``（注意那个冒号，前 6 个字符）** ——
        与 :meth:`check_count` 的 ``'Count:'`` **刻意分开**，拿混了会**永远失败**。

        ⚠️ **三种「名单类」失败必须分得开**（含糊成一句会让管理员不知道该做
        什么）：文件不存在 / 内容坏 / 文件在但没有可用条目 —— 各有各的文案。

        ⚠️ ``Not permitted.`` 表示**你不是管理员** —— 它是 HTTP 200 的**正常
        业务答复**。

        ⚠️ **``List:`` 段是分隔的邮箱串**（不是 JSON、也不解析）。本方法**原样
        返回**；要解析请由调用方自己做。⚠️ 名单里是**别人的邮箱**。

        ⚠️ **本方法不抛异常**：连不上、超时、非管理员……一律以一句文本返回。

        Returns:
            str: 服务端回应正文。成功时以 ``'Users:'`` 开头。

        Added by DeepSeek, 2026-10-05
        """
        return self._request("user_list")

    def user_list_detail(self) -> str:
        """列服务端的**全部用户**：邮箱 + 姓名（★ 服务端 v3.35，**仅管理员**）。

        与 :meth:`user_list` 是**两个动作、两个记号**（``UsersDetail:`` vs
        ``Users:``）：服务端刻意没给老动作加字段 —— 老客户端只认 ``Users:``，
        多一段会被解析成多余内容。所以「要姓名」就用本方法。

        成功正文形如（``Dropped:`` / ``Truncated:`` / ``NamesLimited:`` **只在
        非零时才出现**，所以**不要**假设段数固定）::

            UsersDetail: 3 | List: a@x.com; b@x.com; c@z.net | Names: 张; (none); 李四

        ``List:`` 与 :meth:`user_list` 的**逐字同构**（同一个解析器可以直接用）；
        ``Names:`` 与 ``List:`` **一一对应**，空姓名是占位 ``(none)``。

        ⚠️ 姓名只能靠「读每个用户自己的许可记录」拿到（每条 1 次 GET），所以服务端
        有硬上限（当前 100）：超出部分**照旧列邮箱、姓名给 ``(none)``**，并在正文里
        附 ``NamesLimited: N``。

        ⚠️ 解析交给 ``zmlx.ui.utils.lic_utils.parse_user_list_detail``（那里把两个
        段拼成 ``[(姓名, 邮箱)]``，并处理上面那些可选段）。

        Returns:
            str: 服务端回应正文。非管理员是 ``Not permitted.``（HTTP 200 的**正常
            业务答复**，不是异常）。**不抛异常。**

        Added 2026-10-18（服务端 v3.35）
        """
        return self._request("user_list_detail")

    def list_feedbacks(self, date: str = "", email: str = "") -> str:
        """列出某个用户**某一天**的反馈文件名.

        机器码由本方法自己补进请求体，**不需要也不能传** —— 服务端据此判断
        **你是谁**，再决定你能不能看那个人的反馈。

        ★ **这是唯一能列出反馈的入口**。

        ★★ **权限**（服务端的门，本地不重复判、也绝不放宽）：管理员可看**任意**
        邮箱，其他人**只能看自己**绑定的那个。

        ⚠️⚠️ **防枚举：越权者的答复与「那个邮箱根本不存在」逐字相同**
        （都是 ``Not permitted.``）—— 所以**不要**试图区分那两种情况。

        ⚠️ **``Not permitted.`` 是正常业务答复**（HTTP 200），不是异常。

        ⚠️⚠️ **成功记号是 ``'Feedbacks:'``（前 10 个字符，复数）** —— 它与
        :meth:`get_feedback` 的 ``'Feedback:'``（单数）**只差一个 's'**，也与
        :meth:`feedback` 的 ``'Succeed'`` **完全不同**。拿混了会把**成功读成
        失败**。

        ⚠️ **``date`` 留空 = 北京时间的今天**。服务端用的是**北京时间的自然日**，
        **不要**自己在本机算一个今天传进来 —— 时区差一天会列出一个**空列表**，
        而那看起来完全正常。

        ⚠️ **日期一律 ``YYYY-MM-DD``（10 个字符）**，本方法**不做本地日期校验**。

        ⚠️ **段数不固定**，解析请**按段名找**，别按下标取。⚠️ ``Files:`` 段是
        裸文件名串（不是 JSON）。本方法**原样返回**；要解析请用
        ``plugins/builtin/user_admin.py`` 里的解析器（原 ``zmlx.ui.tabs.feedbacks_view``）。

        ⚠️ **本方法不抛异常**：连不上、超时、越权……一律以一句文本返回。

        Args:
            date: **可选**日期（``YYYY-MM-DD``，北京时间自然日）；留空表示看
                **今天**。
            email: **可选**邮箱，**只有管理员**能用它看别人的反馈；留空表示看
                **自己**。

        Returns:
            str: 服务端回应正文。成功时以 ``'Feedbacks:'`` 开头。

        Added by DeepSeek, 2026-10-08
        """
        return self._request("list_feedbacks",
                             date=date or None, email=email or None)

    def get_feedback(self, file: str, email: str = "") -> str:
        """取**一条反馈的内容**（**本人或管理员**）.

        机器码由本方法自己补进请求体 —— 服务端据此判定你能不能看这个文件。所以
        本方法收**文件名**与可选邮箱。

        ★★ **``file`` 必须是裸文件名**（``'20260928223007.json'``，通常来自
        :meth:`list_feedbacks` 的 ``Files:`` 段）：完整 key 会被服务端的第一道
        名字闸挡掉；同层级的 ``license.json`` 这类文件由第二道闸挡掉。
        ⚠️ 本方法**不做本地形态校验**。

        ⚠️ **``file`` 没有默认值**：不存在「默认读最近一条」这种猜测。要「看最近
        一条」请先 :meth:`list_feedbacks` 再取末项。

        ★★ **内容以 base64 返回，本方法【不解码】**：``FileBase64:`` 段就是那份
        文件**原始字节**的 base64，服务端**不解析 JSON、不解码 UTF-8**。本方法
        适合**原样显示 / 排错**；**要真正用内容请用** :meth:`get_feedback_bytes`。

        ⚠️⚠️ **``Truncated: true`` 表示内容超限被截断**（**尾巴丢了**）。被截断的
        内容**很可能不是合法 JSON**，所以**必须先看那个标记再 ``json.loads``**。

        ⚠️ **``FileBase64:`` 段为空是成功**（那个文件是 **0 字节**），与「文件不
        存在」是**两件事**；后者 :meth:`decode_feedback` 会回 ``None``。

        ⚠️ **成功记号是 ``'Feedback:'``（前 9 个字符，单数）** —— 与
        :meth:`list_feedbacks` 的 ``'Feedbacks:'``（前 10 个，复数）**只差一个
        ``s``**。拿判列表的那段来判本方法会**永远失败**。

        ⚠️ **本方法不抛异常**：连不上、超时、越权、文件不存在……一律以一句文本
        返回。

        Args:
            file: **必填**的反馈文件名（**裸文件名**）。
            email: **可选**邮箱，**只有管理员**能用它看别人的反馈；留空表示看
                **自己**。规则与 :meth:`list_feedbacks` 的 ``email`` 逐字相同。

        Returns:
            str: 服务端回应正文。成功时以 ``'Feedback:'`` 开头（``FileBase64:``
            段是 base64 编码的内容）。

        Added by DeepSeek, 2026-10-08
        """
        return self._request("get_feedback", file=file, email=email or None)

    @staticmethod
    def decode_feedback(reply):
        """把一句 ``get_feedback`` 答复里的内容解成**原始字节**。

        ★★ **base64 的解码就在这里**。⚠️ **本方法是纯 Python 的**（不联网、
        不碰 DLL）。

        ⚠️ **它是静态方法、只吃一句答复**，于是调用方可以在**已经拿到答复**之后
        直接解，而不必再打一次服务端。

        ⚠️ 三条返回值**含义各不相同**，调用方必须分开处理：

        - ``None``：**业务拒绝 / 连不上**（答复不是 ``Feedback:`` 开头）；
        - ``b''``：那个文件是 **0 字节** —— 这是**成功**，与上面那条是两件事；
        - 其余：反馈文件里的**原始字节**（正常是缩进 2 的 JSON）。

        ⚠️ 服务端**不解析 JSON、也不解码 UTF-8**，所以解出来的也可能**不是**合法
        JSON —— 那由调用方自己判断。

        ⚠️ **任何情况下都不抛异常**：解不开一律回 ``None``。

        Args:
            reply: ``get_feedback`` 的答复正文（任意类型）。

        Returns:
            bytes | None: 原始字节，见上。
        """
        # ⚠️⚠️⚠️ 判据只看开头是不是 ``feedback:``（**单数**，前 9 个字符）：
        #    与列举的 ``feedbacks:``（**复数**，前 10 个）**只差一个 s**，与提交
        #    反馈的 ``Succeed`` 又是**同名不同义** —— 两者拿混都会把**成功读成
        #    失败**。所以下面这两个字面量**只在本方法内联**（不做成模块级常量，
        #    本模块的模块级只留两个单例），改动时数清那 9 个字符。
        text = reply if isinstance(reply, str) else str(reply or '')
        text = text.strip()
        if text[:9].lower() != 'feedback:':
            return None
        # ⚠️ 从**第一个** ``FileBase64: `` 标记处切到串尾：base64 里没有空格、
        #    没有换行、也没有 `` | ``（分段符），所以那一段不会被再切开，也就
        #    不需要判断「在哪结束」。段名里带 ``Base64`` 是服务端刻意的 ——
        #    读响应/日志的人必须一眼看出那不是正文原文。
        #    ⚠️ 段值为**空串**时是 ``b''``（0 字节的文件）—— 那是**成功**，
        #    不要把它和上面的 ``None`` 合并。
        pos = text.find('FileBase64:')
        if pos < 0:
            return None                  # 成功正文里恒有这一段；防御性返回
        payload = text[pos + len('FileBase64:'):].strip()
        # ⚠️⚠️ **必须先判「空串」再解码**：``b64decode('')`` 也是 ``b''``，而这两
        #    种情况的含义完全相反 —— 段值为空 = **0 字节的文件（成功）**，下面
        #    解码失败 = **这段内容不是 base64（数据坏了）**。不先分开，两者会
        #    混成同一个 ``b''``，界面就会把一份坏内容说成「空文件」。
        if not payload:
            return b''
        # ⚠️ 只用 ``b64decode``（不插换行的那一支）：``encodebytes`` 每 76 字符插
        #    一个 ``\n``，服务端刻意没用它（见 license-check 的 feedback_admin.py），
        #    解码侧也就不必容忍换行。
        try:
            # ⚠️⚠️ **``validate=True`` 不能省**：默认的 ``validate=False`` 会把
            #    **字母表外的字符直接丢掉**，于是 ``'!!!'`` 这种垃圾输入会被静默
            #    解成 ``b''`` —— 又变回「空文件」，正是上面那条要防的混淆。
            #    开了它，非字母表字符抛 ``binascii.Error``，下面接住回 ``None``。
            #    （实测：``b64decode('!!!') == b''`` 而不报错。）
            return base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            return None

    def get_feedback_bytes(self, file: str, email: str = ""):
        """取一条反馈的**内容字节**（= :meth:`get_feedback` + :meth:`decode_feedback`）。

        ⚠️ **本方法不抛异常**，返回值与 :meth:`decode_feedback` 逐字一致：
        ``None`` = 业务拒绝 / 连不上；``b''`` = 0 字节的**成功**文件；
        其余 = 原始字节。

        ⚠️ **只联网一次**：它把 :meth:`get_feedback` 的答复**就地**交给
        :meth:`decode_feedback`（那是个不碰网络的静态方法）。

        Args:
            file: **必填**的反馈文件名（**裸文件名**）。
            email: **可选**邮箱，**只有管理员**能用它看别人的反馈；留空表示看
                **自己**。

        Returns:
            bytes | None: 三条返回值含义各不相同，详见 :meth:`decode_feedback`。
            **任何情况下都不抛异常。**
        """
        return self.decode_feedback(self.get_feedback(file, email))

    # ------------------------------------------------------------------
    # 注册 / 绑定
    # ------------------------------------------------------------------

    def send_code(self, email: str, purpose: str = "") -> str:
        """发一封 6 位验证码邮件到指定邮箱（成功正文以 ``'Sent'`` 开头）。

        ⚠️ **同一个邮箱 10 分钟内只能发一次**，否则服务端返回 429，正文里写着
        还要等多少秒（那是**有意义**的答复，不要丢掉）。

        ⚠️⚠️ **本方法【不带机器码】**：见 :meth:`_request_plain`。

        ⚠️⚠️ **本地不预检邮箱形态**：明显非法的邮箱会**照样发出去**，由服务端回
        一句文案。文案仍然准确，代价是**多一次网络往返**。

        Args:
            email: 收件邮箱。形态由服务端校验。
            purpose: **可选**的用途声明，**只影响邮件正文的措辞**，不参与任何
                判定。留空（默认）表示**不发该字段**。

        Returns:
            str: 服务端回应正文。成功时以 ``'Sent'`` 开头（前 4 字符为 ``sent``）。
            **不抛异常。**

        Added by DeepSeek, 2026-10-02
        """
        # ⚠️ 空的 ``purpose`` **不发**（服务端把「没给」与「给了空串」都当没给，
        #    但不发更干净 —— 与 C++ 侧那个专用导出同一条写法）。
        return self._request_plain("send_code", email=email,
                                   purpose=purpose or None)

    def submit(self, email: str, code: str, user: str = "",
               org: str = "") -> str:
        """验码并**注册 + 绑定本机**（成功正文以 ``'Bound'`` 开头）。

        ⚠️ **机器码由本方法自己补**（字段名 ``machine_id``；★ 2026-10-18 起
        **不再用** ``machine_code``），**不需要也不能传** —— 少传一个值就少一类
        「传错了却每一步都成功」的故障。服务端在 ``submit`` 里接受 ``machine_id``
        作为**绑定目标**（见实现里那段注释），所以带上它就等于指定「绑定本机」。

        ⚠️ **注册成功 ≠ 立刻查得到授权**：如果自检读到的是绑定之前的旧结论，
        请用 ``read_cache=False`` 再查一次。

        Args:
            email: 邮箱（与 :meth:`send_code` 必须**逐字一致**）。
            code: 邮件里收到的 6 位数字验证码。
            user: **可选**姓名，作为这份授权的署名。
                ⚠️ 署名只在首次创建那一刻写入，已存在的授权不会被改动。
                留空表示不写该字段。
            org: **可选**单位，规则与 ``user`` 完全同构。

        Returns:
            str: 服务端回应正文。成功时以 ``'Bound'`` 开头。**不抛异常。**

        Added by DeepSeek, 2026-10-02
        """
        # ★ 2026-10-18（张老师要求）：机器码字段**统一用 ``machine_id``**，
        #    ``submit`` 也不再发 ``machine_code`` —— 客户端只认一个字段名。
        #    服务端在 ``submit`` 里接受 ``machine_id`` 作为绑定目标（v3.30 起它是
        #    ``machine_code`` 的**别名**，只在后者没给时生效；2026-10-18 实测线上
        #    v3.34 已**直接**按 ``machine_id`` 解析 —— 非字符串/空串回
        #    ``Bad request: "machine_id" must be a non-empty string.``），所以
        #    「带不带绑定目标」这条分流照样成立：只发 ``machine_id`` ⇒ 服务端按
        #    「绑定本机」处理，回 ``Bound``。
        # ⚠️⚠️ **这条依赖服务端那个别名**：万一哪天真把它删掉，本方法会因为「没有
        #    ``machine_code``」被当成一次**注册**（回 ``OK``）—— 那是一条**假成功**
        #    （机器没绑上，而响应看着完全正常）。真到那天，把这里换成
        #    ``_request_plain("submit", ..., machine_code=machine)`` 即可（v1.11.1
        #    之前就是那么写的，git 历史里有）。
        # ⚠️ 机器码判空/取值都在 ``_request`` 里做，文案与别处逐字一致。
        return self._request("submit", email=email, code=code,
                             user=user or None, org=org or None)

    def version(self) -> str:
        """查线上服务的**代码版本号**。

        这个查询不产生任何副作用（比 :meth:`send_code` 更适合拿来试「服务器在
        不在」，后者会真的寄一封信出去）。

        ⚠️⚠️ **本方法【不带机器码】**：服务端在**校验请求体之前**就把它答了。

        Returns:
            str: 版本号文本（例如 ``'3.14'``）；服务端未注入时是 ``'unknown'``。
            ⚠️ 连不上时返回的是**一句错误描述**，不是什么版本号。
            **本方法不抛异常。**

        Added by DeepSeek, 2026-10-02

        Modified 2026-10-18: 改走 ``_request_plain`` —— 文档一直说「本方法不带
        机器码」，而代码从前走的是 ``_request``（**带**机器码）。机器码字段改名
        那次顺手把这个文档与实现的不一致修掉了。
        """
        return self._request_plain("version")


lic = License(core_obj=core)
web_license = WebLicense(core_obj=core)

"""邮件发送。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-09-29: 改用服务端接口 ``lic.mail`` 代发（不再直连 SMTP）
Modified by DeepSeek, 2026-10-02: 该接口随网络功能迁到 ``web_license.mail``
"""
from typing import Optional


def sendmail(address: str, subject: Optional[str] = None, text: Optional[str] = None,
             name_from: Optional[str] = None, name_to: Optional[str] = None) -> bool:
    """发送一封电子邮件。

    ⚠️ **本函数通过服务端接口 ``web_license.mail`` 代发**，不再直连 SMTP：机器码由
    C++ 侧自己算，服务端用内置账号发信。因此有两条**服务端**的门槛（本地不重复
    判、也不放宽）：**只有「已注册且授权当前有效」的机器发得出去**，且**限流是
    「每个用户」而非每台机器**（同一个人的多台机器**共用**配额）。

    ⚠️ 成功记号是 ``'Mail sent'``（中间有个空格）：它**既不**以 ``yes`` 开头，
    也**不是** ``Sent``。用错判据会把**成功读成失败**。本函数已按正确判据处理，
    调用方只看返回值即可。

    ⚠️ **发件人不由参数决定**：SMTP 不接受伪造发件地址，收件人看到的地址恒为
    服务端内置账号。``name_from`` 因此**不再有效**（保留参数只为兼容旧签名）。

    ⚠️ **不抛异常**：连不上、超时、限流、参数非法……一律返回 ``False``。

    Args:
        address (str): 收件人邮箱地址。
        subject (str, optional): 邮件主题。**超长会被服务端拒**，不做截断。
            为 ``None`` 时用 ``'Message from <name_from>'``。
        text (str, optional): 邮件正文。**超长是「截断后成功」而非失败**。
            ⚠️ 本函数**不做本地截断** —— 服务端要按**原文**算「被截掉多少」并
            回报；本地先截一刀会让那个数字撒谎。
        name_from (str, optional): [已忽略] 发件人显示名由服务端按许可记录决定。
        name_to (str, optional): [已忽略] 收件人显示名不再随请求发送。

    Returns:
        bool: 邮件发送成功返回 True，失败返回 False。

    Note:
        - 兼容旧签名：``name_from`` / ``name_to`` 仍可传，但不再起作用
        - 旧版直连 SMTP 的实现已移除（含硬编码账号与明文口令）
    """
    try:
        import getpass

        if name_from is None:
            try:
                name_from = getpass.getuser()
            except Exception:
                name_from = 'User'
        if subject is None:
            subject = f'Message from {name_from}'
        if text is None:
            text = ''
        if not isinstance(text, str):
            raise ValueError(f"text must be str, but got {type(text)}")

        # ⚠️ **必须是惰性导入**：``zmlx/system`` 按架构约定不依赖 zmlx 的其它部分
        #    （见 zmlx/system/__init__.py 的模块说明），而 ``zmlx.exts._utils``
        #    反过来 import 了 ``zmlx.system``。在模块顶层 import ``zmlx.exts``
        #    会形成循环导入。放在函数体内即可（首次调用时，两个包都已加载完）。
        from zmlx.exts import web_license

        # ⚠️ **不在这里预判「接口可不可用」**：``web_license.mail`` 是公开方法，
        #    本来就承诺「不抛异常、失败以一句文本返回」：那些描述都不以
        #    ``Mail sent`` 开头，走到下面照样 return False。
        #    ★ 外部调用 ``web_license`` 请**只用它的公开方法**，别再摸 ``core``。
        reply = str(web_license.mail(address, subject, text) or '').strip()
        if not reply:
            return False

        # ⚠️ 成功记号是 'Mail sent'（前 9 字符，**含中间那个空格**）。
        #    ★ 不能拿判 'Sent' 的那段（前 4 字符 'sent'）来判 ——
        #    'Mail sent' 的前 4 字符是 'mail'，会把**成功读成失败**。
        #    ★ 也不能用判 'Yes' 的那段 —— 'Mail sent' 不以 yes 开头。
        if reply[:9].lower() == 'mail sent':
            return True

        # 失败也是一句可读描述（含限流那条带精确剩余秒数的答复）。
        # 旧版是静默返回 False，这里保持同样的「不回显」行为，只额外记一条日志，
        # 否则用户永远不知道自己为什么没收到信。
        from zmlx.system._log import log

        log(f'sendmail failed: {reply}')
        return False
    except Exception as e:
        from zmlx.system._log import log

        log(f'sendmail failed: {e}')
        return False

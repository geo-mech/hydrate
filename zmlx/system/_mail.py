from typing import Optional


def sendmail(address: str, subject: Optional[str] = None, text: Optional[str] = None,
             name_from: Optional[str] = None, name_to: Optional[str] = None) -> bool:
    """通过SMTP协议发送电子邮件。

    Args:
        address (str): 收件人邮箱地址
        subject (str, optional): 邮件主题，默认为发送者名称
        text (str, optional): 邮件正文内容，默认为空字符串
        name_from (str, optional): 发件人显示名称，默认获取系统用户名
        name_to (str, optional): 收件人显示名称，默认为'UserEmail'

    Returns:
        bool: 邮件发送成功返回True，失败返回False

    Note:
        - 使用固定SMTP服务器(smtp.126.com)和预配置账号
        - 邮件内容默认使用UTF-8编码
        - 包含异常处理机制，失败时静默返回False
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        if name_from is None:
            try:
                import getpass
                name_from = getpass.getuser()
            except:
                name_from = 'User'
        if name_to is None:
            name_to = 'UserEmail'
        if subject is None:
            subject = f'Message from {name_from}'
        if text is None:
            text = ''
        assert isinstance(text, str), f"text must be str, but got {type(text)}"
        message = MIMEText(text, 'plain', 'utf-8')
        message['From'] = Header(name_from)
        message['To'] = Header(name_to)
        message['Subject'] = Header(subject)
        smtp_obj = smtplib.SMTP()
        smtp_obj.connect("smtp.126.com", 25)
        smtp_obj.login("hyfrddm@126.com", "iggcas0617")
        smtp_obj.sendmail('hyfrddm@126.com',
                          [address], message.as_string())
        return True
    except:
        return False

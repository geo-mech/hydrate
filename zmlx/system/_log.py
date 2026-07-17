from typing import Optional

from zmlx.system._app_data import app_data


def log(text: str, tag: Optional[str] = None):
    """记录运行时日志信息。

    Args:
        text (str): 需要记录的日志内容
        tag (str, optional): 唯一标识标签，用于实现每日单次记录

    Returns:
        None

    Note:
        - 当指定 tag 时，确保当天只记录一次相同标签日志
        - 使用 app_data 的标签跟踪系统实现每日去重
        - 静默处理所有I/O异常
        - 实际日志存储路径由 _AppData 类管理
    """
    if tag is not None:
        if app_data.has_tag_today(tag):
            return
        else:
            app_data.add_tag_today(tag)
    app_data.log(text)

import warnings

from zmlx.system._log import log


def warn(message, category=None, stacklevel=1, tag=None):
    """
    警告，并且当tag给定的时候，则记录日志 (每天只记录一次). 这个函数用于在zmlx内部，去替换warnings的warn函数，
    实现在弹出警告的同时，还会进行必要的记录。
    Args:
        tag: 记录日志的标签（非必需）。在没有tag的时候，则使用message来替代
        message: 需要弹出的警告
        category: 类别
        stacklevel: 栈的深度

    Returns:
        None
    """
    warnings.warn(message=message, category=category, stacklevel=stacklevel + 1)
    if tag is None:
        tag = message
    if isinstance(tag, str):
        log(text=message, tag=f'{tag}.warn')

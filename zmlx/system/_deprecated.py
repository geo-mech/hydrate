import functools

from zmlx.system._warn import warn


def deprecated(func=None, *, remove_after=None, alternative=None):
    """
    弃用装饰器：标记函数为已弃用。调用时自动弹出警告并记录日志。

    支持两种用法：
        1. 不带参数：  @deprecated
        2. 带参数：    @deprecated(remove_after="2027-1-1", alternative="another function")

    Args:
        func: 被装饰的函数（自动传入）
        remove_after: 弃用日期
        alternative: 替代函数的名称

    Returns:
        包装后的函数

    Examples:
        >>> @deprecated
        ... def old_func():
        ...     pass

        >>> @deprecated(remove_after="since 2027-7")
        ... def old_func():
        ...     pass
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            msg = f'function "{f.__module__}.{f.__qualname__}" is deprecated and will be removed after {remove_after}, please use "{alternative}" instead'
            warn(msg, category=DeprecationWarning, stacklevel=2, tag=f.__name__)
            return f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator

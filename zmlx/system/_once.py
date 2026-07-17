import functools

from zmlx.system._app_data import app_data


def first_execute(name, key=None):
    """
    检查给定的文件是否是第一次运行（只有在首次启动first_execute函数的时候返回True）.
    其中name为文件的全路径。key为在app_data中存储的名字。
    """
    if name is None:
        name = ''
    if key is None:
        key = 'files_executed'
    executed = app_data.get(key, [])
    if name in executed:
        return False
    else:
        executed.append(name)
        app_data.put(key, executed)
        return True


def execute_once(func=None, *, name=None, file=None):
    """
    执行一次装饰器：标记函数只执行一次。

    支持两种用法：
        1. 不带参数：  @execute_once
        2. 带参数：    @execute_once(name="xxx")

    Args:
        func: 被装饰的函数（自动传入）
        name: 用于存储执行记录的name
        file: 函数所在的文件/模块

    Returns:
        包装后的函数
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if first_execute(
                    name=f'{f.__module__ if file is None else file}.{f.__qualname__ if name is None else name}'):
                return f(*args, **kwargs)
            else:
                return None

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator

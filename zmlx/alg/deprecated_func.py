import importlib
import warnings

from zml import log


def create(pack_name, func, date=None):
    """
    创建一个弃用的函数
    """
    return dict(pack_name=pack_name, func=func, date=date)


def get(name, data, current_pack_name):
    """
    当访问不存在的属性时，尝试从其他模块中导入
    """
    import importlib
    value = data.get(name)
    if value is not None:
        pack_name = value.get('pack_name')
        func = value.get('func')
        date = value.get('date')
        warnings.warn(
            f'<{current_pack_name}.{name}> will be removed after {date}, '
            f'please use <{pack_name}.{func}> instead.',
            DeprecationWarning,
            stacklevel=2
        )
        mod = importlib.import_module(pack_name)
        return getattr(mod, func)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def deprecated_func(deprecated_name, pack_name, func_name, date=None):
    """
    定义一个废弃的函数.
    """

    def the_function(*args, **kwargs):
        warnings.warn(f'function "{deprecated_name}" will be removed after {date}, '
                      f'please use "{pack_name}.{func_name}" instead. ',
                      DeprecationWarning)
        log(text=f'The function "{deprecated_name}" is used',
            tag=f'function_used_{deprecated_name}')
        try:
            mod = importlib.import_module(pack_name)
            f = getattr(mod, func_name)
            return f(*args, **kwargs)
        except:
            pass

    return the_function

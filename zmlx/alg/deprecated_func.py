from zml import log
import warnings
import importlib


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



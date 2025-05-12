import importlib
import warnings

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)
from zml import log
from zmlx.alg.sys import create_deprecated as create, get_deprecated as get


def deprecated_func(deprecated_name, pack_name, func_name, date=None):
    """
    定义一个废弃的函数.
    """

    def the_function(*args, **kwargs):
        warnings.warn(
            f'function "{deprecated_name}" will be removed after {date}, '
            f'please use "{pack_name}.{func_name}" instead. ',
            DeprecationWarning, stacklevel=2)
        log(text=f'The function "{deprecated_name}" is used',
            tag=f'function_used_{deprecated_name}')
        try:
            mod = importlib.import_module(pack_name)
            f = getattr(mod, func_name)
            return f(*args, **kwargs)
        except:
            pass

    return the_function


__all__ = ['deprecated_func', 'get', 'create']

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

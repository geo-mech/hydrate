import importlib
import zmlx.alg.sys as warnings


class RuntimeFunc:
    def __init__(self, pack_name, func_name, deprecated_name=None,
                 deprecated_date=None):
        self.pack_name = pack_name
        self.func_name = func_name
        self.deprecated_name = deprecated_name
        self.deprecated_date = deprecated_date

    def get_func(self):
        if self.deprecated_name is not None:
            from zmlx.base.zml import log
            warnings.warn(
                f'function "{self.deprecated_name}" will be removed after {self.deprecated_date}, '
                f'please use "{self.pack_name}.{self.func_name}" instead. ',
                DeprecationWarning, stacklevel=2)
            log(text=f'The function "{self.deprecated_name}" is used',
                tag=f'function_used_{self.deprecated_name}')

        try:
            mod = importlib.import_module(self.pack_name)
            return getattr(mod, self.func_name)
        except Exception as e:
            warnings.warn(
                f'meet error when import "{self.func_name}" from "{self.pack_name}". error = "{e}"')
            return None

    def __call__(self, *args, **kwargs):
        f = self.get_func()
        if f is not None:
            return f(*args, **kwargs)
        return None

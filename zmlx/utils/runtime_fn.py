"""延迟加载函数包装器，用于代码迁移过程中的向后兼容。

将目标函数包装为在调用时动态导入，可选发出弃用警告并记录日志。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
import importlib


class RuntimeFunc:
    """延迟加载函数包装器。

    存储目标包名和函数名，在调用时通过 ``importlib.import_module`` 动态导入目标函数。
    若配置了 deprecated_name 和 deprecated_date，每次调用时会发出 DeprecationWarning
    并通过 ``zmlx.exts.log`` 记录使用日志。
    """

    def __init__(self, pack_name, func_name, deprecated_name=None,
                 deprecated_date=None):
        """初始化包装器。

        Args:
            pack_name: 目标函数的包名（如 ``"zmlx.plt"``）。
            func_name: 目标函数名（如 ``"show_xy"``）。
            deprecated_name: 旧的函数名，用于弃用警告。
            deprecated_date: 旧函数的移除日期，用于警告消息。
        """
        self.pack_name = pack_name
        self.func_name = func_name
        self.deprecated_name = deprecated_name
        self.deprecated_date = deprecated_date

    def get_func(self):
        """动态导入并返回目标函数。

        若配置了弃用信息，发出 DeprecationWarning 并记录使用日志。
        若导入失败，发出警告并返回 None。

        Returns:
            callable | None: 目标函数，导入失败时为 None。
        """
        if self.deprecated_name is not None:
            from zmlx.exts import log
            warn(
                f'function "{self.deprecated_name}" will be removed after {self.deprecated_date}, '
                f'please use "{self.pack_name}.{self.func_name}" instead. ',
                DeprecationWarning, stacklevel=2)
            log(text=f'The function "{self.deprecated_name}" is used',
                tag=f'function_used_{self.deprecated_name}')

        try:
            mod = importlib.import_module(self.pack_name)
            return getattr(mod, self.func_name)
        except Exception as e:
            warn(
                f'meet error when import "{self.func_name}" from "{self.pack_name}". error = "{e}"')
            return None

    def __call__(self, *args, **kwargs):
        """调用目标函数。

        Args:
            *args: 传递给目标函数的位置参数。
            **kwargs: 传递给目标函数的关键词参数。

        Returns:
            任意 | None: 目标函数的返回值，导入失败时为 None。
        """
        f = self.get_func()
        if f is not None:
            return f(*args, **kwargs)
        return None

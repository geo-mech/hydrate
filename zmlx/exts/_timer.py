import functools
import timeit
from ctypes import c_char_p, c_double, c_bool
from typing import Callable, Dict, Tuple, Optional

from zmlx.exts._dll import DllCore, core, make_c_char_p


class Timer:
    """用于统计函数执行时间的辅助工具类。

    该类通过字典结构记录函数名称与执行时间的映射关系，支持通过装饰器或上下文管理器方式使用。

    Attributes:
        co (DllCore): 与底层C++核心模块交互的接口实例
    """

    def __init__(self, co: DllCore):
        """初始化计时器实例。

        Args:
            co (DllCore): 必须为DllCore类型实例，用于底层C++交互

        Raises:
            AssertionError: 当co参数类型不匹配时抛出
        """
        assert isinstance(
            co, DllCore), f'the type of <co> should be {type(DllCore)}'
        co.use(c_char_p, 'timer_summary')
        co.use(None, 'timer_log', c_char_p, c_double)
        co.use(None, 'timer_reset')
        co.use(c_bool, 'timer_enabled')
        co.use(None, 'timer_enable', c_bool)
        self.__key2t = {}
        self.co = co  # core

    def __call__(self, key: str, func: Callable, *args, **kwargs):
        """执行函数并记录耗时（支持异常传播）。

        Args:
            key (str): 函数标识符，建议使用__name__属性
            func (Callable): 要计时的可调用对象
            *args: 传递给func的位置参数
            **kwargs: 传递给func的关键字参数

        Returns:
            Any: 被调用函数的返回结果

        Raises:
            异常类型: 传播被调用函数抛出的任何异常
        """
        self.beg(key)
        r = func(*args, **kwargs)
        self.end(key)
        return r

    def __str__(self) -> str:
        """生成耗时统计摘要。

        Returns:
            str: 格式化字符串，包含各函数累计耗时和调用次数的统计信息
        """
        return self.summary()

    def summary(self) -> str:
        """生成耗时统计摘要。

        Returns:
            str: 格式化字符串，包含各函数累计耗时和调用次数的统计信息
        """
        return self.co.timer_summary().decode()

    @property
    def key2nt(self) -> Dict[str, Tuple[int, float]]:
        """获取函数耗时统计字典。

        Returns:
            Dict[str, Tuple[int, float]]:
                键为函数名称，值为(n次调用, 总秒数)的元组。
        """
        try:
            tmp = eval(self.summary())
            tmp.pop('enable', None)
            return tmp
        except:
            return {}

    def log(self, name: str, seconds: float):
        """记录指定名称的耗时数据。

        Args:
            name (str): 过程名称标识符
            seconds (float): 耗时秒数，需为浮点数
        """
        self.co.timer_log(make_c_char_p(name), seconds)

    def clear(self):
        """重置。
        """
        self.co.timer_reset()

    def enabled(self, value: Optional[bool] = None) -> bool:
        """控制或查询计时器开关状态。

        Args:
            value (bool|None):
                当为None时返回当前状态；
                当为bool时设置启用状态

        Returns:
            bool: 当前/更新后的启用状态
        """
        if value is not None:
            self.co.timer_enable(value)
        return self.co.timer_enabled()

    def beg(self, key: str):
        """启动指定键的计时。

        Args:
            key (str): 需要启动计时的唯一标识符
        """
        self.__key2t[key] = timeit.default_timer()

    def end(self, key: str):
        """结束指定键的计时并记录结果。

        Args:
            key (str): 已启动计时的唯一标识符

        Raises:
            KeyError: 当未找到对应key的计时起点时
        """
        t0 = self.__key2t.get(key)
        if t0 is not None:
            assert isinstance(t0, (float, int)), f"t0 must be float|int, but got {type(t0)}"
            cpu_t = timeit.default_timer() - t0
            self.log(key, cpu_t)


timer = Timer(co=core)


def clock(func: Callable, *, key=None) -> Callable:
    """函数耗时统计装饰器（支持异常传播）。

    通过Timer实例自动记录被装饰函数的执行耗时，需配合全局timer实例使用。

    Args:
        func (Callable): 需要计时的函数
        key (str|None): 自定义计时键名，默认使用函数名

    Returns:
        Callable: 装饰后的函数

    示例:
        >>> @clock
        ... def function_a():
        ...     pass

        >>> @clock(key='My function')
        ... def function_b():
        ...     pass
    """

    @functools.wraps(func)
    def clocked(*args, **kwargs):
        if isinstance(key, str) and len(key) > 0:
            name = key
        else:
            name = f"{func.__module__}.{func.__qualname__}"

        timer.beg(name)
        try:
            result = func(*args, **kwargs)
            timer.end(name)
            return result
        except Exception as e:
            timer.end(name)
            raise e

    return clocked

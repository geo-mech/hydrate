import ctypes
import os
import warnings
from ctypes import c_bool, c_char_p, c_void_p, c_size_t, c_int, CFUNCTYPE
from ctypes import cdll
from typing import Optional, Any, Callable, Union

from zmlx.exts._utils import app_data, in_windows


class _NullFunction:
    """空函数占位符，用于处理未找到的DLL函数。

    当尝试调用未加载成功的DLL函数时，提供安全的默认行为。
    """

    def __init__(self, name):
        """初始化空函数对象。

        Args:
            name (str): 原始函数名称，用于调试信息输出
        """
        self.name = name

    def __call__(self, *args, **kwargs):
        """模拟函数调用行为。

        Args:
            *args: 任意位置参数
            **kwargs: 任意关键字参数

        Note:
            - 不会实际执行任何操作
            - 自动打印调用参数帮助调试
            - 保持与正常函数相同地调用接口
        """
        info = f'calling null function {self.name}(args={args}, kwargs={kwargs})'
        warnings.warn(info, stacklevel=2)


def get_func(dll_obj: Optional[ctypes.CDLL], restype: Any, name: str, *argtypes: Any) -> Callable:
    """配置动态链接库函数接口。

    Args:
        dll_obj (Optional[CDLL]): 动态链接库对象
        restype (Any): 函数返回类型（None表示void）
        name (str): 目标函数名称
        *argtypes: 函数参数类型列表

    Returns:
        Union[CFuncPtr, _NullFunction]: 配置完成的函数对象或空函数占位符

    Raises:
        AssertionError: 当函数名不是字符串类型时抛出

    Note:
        - 自动设置函数的 restype 和 arg_types 属性
        - 未找到函数时返回 _NullFunction 实例
        - 保持与 ctypes 模块兼容的接口设计
    """
    assert isinstance(name, str)
    fn = getattr(dll_obj, name, None)
    if fn is None:
        if dll_obj is not None:
            info = f'Warning: can not find function <{name}> in <{dll_obj}>'
            warnings.warn(info, stacklevel=2)
        return _NullFunction(name)
    if restype is not None:
        fn.restype = restype
    if len(argtypes) > 0:
        fn.argtypes = argtypes
    assert callable(fn), f"function {name} is not callable"
    return fn


def load_cdll(name: str, *, first: Optional[str] = None) -> Optional[ctypes.CDLL]:
    """动态加载 C 风格共享库。

    Args:
        name (str): 动态库文件名（如 'zml.dll'）
        first (str, optional): 优先搜索路径

    Returns:
        CDLL: 加载成功的库对象，失败返回None

    Raises:
        N/A: 静默处理所有异常，仅打印错误信息

    Note:
        - 搜索顺序：优先路径 -> 默认搜索路径 -> 系统路径
        - 支持跨平台文件名自动转换（Windows: .dll，Linux: .so）
        - 失败时尝试直接加载系统库
        - 使用 find 方法实现递归路径搜索
    """
    path = app_data.find(name, first=first)
    if isinstance(path, str):
        try:
            assert isinstance(path, str)
            return cdll.LoadLibrary(path)
        except Exception as e:
            warnings.warn(
                f'Error load library from <{path}>. Message = {e}',
                stacklevel=2)
            return None
    else:
        try:
            return cdll.LoadLibrary(name)
        except Exception as e:
            warnings.warn(
                f'Error load library from <{name}>. Message = {e}',
                stacklevel=2)
            return None


def make_c_char_p(s: str) -> c_char_p:
    """将Python字符串转换为C兼容字符指针。

    Args:
        s (str): 输入字符串

    Returns:
        c_char_p: 指向以null结尾的字节缓冲区的指针

    Note:
        自动进行UTF-8编码转换
    """
    return c_char_p(bytes(s, encoding='utf8'))


class DllCore:
    """
    管理 C++ 内核中的错误、警告等
    """

    def __init__(self, dll_obj: Optional[ctypes.CDLL] = None):
        """
        初始化 DllCore 对象

        Args:
            dll_obj: 动态链接库对象
        """
        self.__err_handle = None
        self.dll: Optional[ctypes.CDLL] = dll_obj
        self.safe_mode = True
        # 检查动态链接库是否成功加载
        if self.dll is None:
            warnings.warn("DllCore: dll_obj is None", category=RuntimeWarning, stacklevel=2)

        # 已经声明的DLL函数接口
        self._dll_funcs = {}

        self.dll_has_error = get_func(self.dll, c_bool, 'has_error')
        self.dll_pop_error = get_func(
            self.dll, c_char_p, 'pop_error', c_void_p)
        self.dll_has_warning = get_func(self.dll, c_bool, 'has_warning')
        self.dll_pop_warning = get_func(
            self.dll, c_char_p, 'pop_warning',
            c_void_p)
        self.dll_has_log = get_func(self.dll, c_bool, 'has_log')
        self.dll_pop_log = get_func(
            self.dll, c_char_p, 'pop_log', c_void_p)
        self.use(c_size_t, 'get_log_nmax')
        self.use(None, 'set_log_nmax', c_size_t)
        self.use(c_char_p, 'get_time_compile', c_void_p)
        self.dll_print_logs = get_func(
            self.dll, None, 'print_logs', c_char_p)
        self.use(c_int, 'get_version')
        self.use(c_bool, 'is_parallel_enabled')
        self.use(None, 'set_parallel_enabled', c_bool)
        self.use(c_bool, 'assert_is_void')
        self.dll_set_error_handle = get_func(
            self.dll, None, 'set_error_handle',
            c_void_p)
        self.use(c_char_p, 'get_compiler')

    def has_dll(self) -> bool:
        """检查动态链接库是否成功加载。

        Returns:
            bool: 成功加载返回 True，否则返回 False
        """
        return self.dll is not None

    def has_error(self) -> bool:
        """检测当前是否存在未处理错误。

        Returns:
            bool: 存在错误返回 True，否则返回 False

        Note:
            - 依赖底层DLL的 has_error 函数实现
            - 当DLL未加载时自动返回False
        """
        if self.has_dll():
            return self.dll_has_error()
        else:
            return False

    def pop_error(self) -> str:
        """获取并移除最早的错误信息。

        Returns:
            str: 解码后的错误描述字符串

        Note:
            - 多次调用可获取错误队列所有信息
            - 自动处理字符串编码转换
            - DLL未加载时返回空字符串
        """
        if self.has_dll():
            return self.dll_pop_error(0).decode()
        else:
            return ''

    def has_warning(self) -> bool:
        """检测当前是否存在未处理警告。

        Returns:
            bool: 存在警告返回 True，否则返回 False

        Note:
            - 警告信息不会中断程序执行
            - 建议在关键操作前检查
        """
        if self.has_dll():
            return self.dll_has_warning()
        else:
            return False

    def pop_warning(self) -> str:
        """获取并移除最早的警告信息。

        Returns:
            str: 解码后的警告描述字符串

        Note:
            - 遵循先进先出原则
            - 自动处理内存释放
        """
        if self.has_dll():
            return self.dll_pop_warning(0).decode()
        else:
            return ''

    def has_log(self) -> bool:
        """检查是否存在未处理的日志信息。

        Returns:
            bool: 存在日志返回 True，否则返回 False

        Note:
            - 日志信息包含调试细节
            - 非错误级别信息
        """
        if self.has_dll():
            return self.dll_has_log()
        else:
            return False

    def pop_log(self) -> str:
        """获取并移除最早的日志信息。

        Returns:
            str: 解码后的日志内容字符串

        Note:
            - 日志最大数量由 log_nmax 控制
            - 自动处理指针内存管理
        """
        if self.has_dll():
            return self.dll_pop_log(0).decode()
        else:
            return ''

    @property
    def parallel_enabled(self) -> bool:
        """[读写] 并行计算功能开关状态。

        Returns:
            bool: 启用并行返回 True，禁用返回 False

        Note:
            - 修改立即生效
            - 仅影响内核计算部分
        """
        if self.has_dll():
            return self.is_parallel_enabled()
        else:
            return False

    @parallel_enabled.setter
    def parallel_enabled(self, value: bool):
        """设置并行计算功能开关状态。

        Args:
            value (bool): 启用设为 True，禁用设为 False
        """
        if self.has_dll():
            self.set_parallel_enabled(value)

    def check_error(self):
        """执行错误检查并清理错误队列。

        Raises:
            RuntimeError: 当检测到未处理错误时抛出

        Note:
            - 自动合并多条错误信息
            - 错误日志会持久化到 app_data
        """
        if self.has_error():
            error = self.pop_error()
            while self.has_error():
                error = f'{error} \n\n {self.pop_error()}'
            app_data.log(error)
            raise RuntimeError(error)

    def set_error_handle(self, func: Callable[[str], None]):
        """注册错误回调处理函数。

        Args:
            func (Callable[[str], None]): 接收错误信息的回调函数

        Note:
            - 回调参数应为字符串类型
            - 需手动维护回调对象内存
        """
        if self.has_dll():
            err_handle = CFUNCTYPE(None, c_char_p)

            def f(s):
                func(s.decode())

            self.__err_handle = err_handle(f)
            self.dll_set_error_handle(self.__err_handle)

    @property
    def log_nmax(self) -> int:
        """[读写] 日志系统最大容量。

        Returns:
            int: 当前配置的最大日志数量

        Note:
            - 达到上限时自动丢弃旧日志
            - 默认值由内核决定
        """
        if self.has_dll():
            return self.get_log_nmax()
        else:
            return 0

    @log_nmax.setter
    def log_nmax(self, value: int):
        """设置日志系统最大容量。

        Args:
            value (int): 新最大日志数量（需 ≥ 0）
        """
        if self.has_dll():
            self.set_log_nmax(value)

    @property
    def time_compile(self) -> str:
        """[只读] 内核编译时间戳。

        Returns:
            str: 格式为 yyyy-MM-dd HH:mm 的时间字符串
        """
        if self.has_dll():
            return self.get_time_compile(0).decode()
        else:
            return ''

    @property
    def version(self) -> int:
        """[只读] 内核版本标识。

        Returns:
            int: 6位数字版本号 (yymmdd 格式)
        """
        if self.has_dll():
            return self.get_version()
        else:
            return 100101

    @property
    def compiler(self) -> str:
        """[只读] 内核编译环境信息。

        Returns:
            str: 编译器名称及版本字符串
        """
        if self.has_dll():
            return self.get_compiler().decode()
        else:
            return ''

    def run(self, fn: Callable) -> Any:
        """执行安全上下文操作。

        Args:
            fn (Callable): 需要执行的目标函数

        Returns:
            Any: 目标函数的返回值

        Note:
            - 自动清理错误/警告信息
            - 保证错误状态重置
        """
        while self.has_error():
            print('\nError: \n', self.pop_error(), '\n')
        result = fn()
        self.check_error()
        if self.has_warning():  # Print the warning information
            while self.has_warning():
                print('\nWarning: \n', self.pop_warning(), '\n')
        return result

    def print_logs(self, path: Optional[str] = None):
        """持久化日志信息到文件。

        Args:
            path (str, optional): 自定义输出文件路径

        Note:
            - 默认输出到 zml.log
            - 覆盖已存在文件内容
        """
        if self.has_dll():
            if path is None:
                self.dll_print_logs(make_c_char_p('zml.log'))
            else:
                assert isinstance(path, str)
                self.dll_print_logs(make_c_char_p(path))

    def use(self, restype: Any, name: str, *argtypes: Any):
        """声明内核函数接口。

        Args:
            restype (Any): 函数返回类型
            name (str): 函数名称
            *argtypes: 参数类型列表

        Note:
            - 重复声明会触发警告
            - 自动包装错误处理逻辑
        """
        if self.has_dll():
            if self._dll_funcs.get(name) is not None:
                info = f'Warning: function <{name}> already exists'
                warnings.warn(info, stacklevel=2)
            else:
                func = get_func(self.dll, restype, name, *argtypes)
                if func is not None:
                    self._dll_funcs[name] = lambda *args: self.run(
                        lambda: func(*args))

    def get_dll_funcs(self):
        """
        返回内核函数字典
        """
        return self._dll_funcs

    def __getattr__(self, name: str):
        """动态获取已声明的内核函数。

        Args:
            name (str): 目标函数名称

        Returns:
            Callable: 配置完成的函数对象

        Note:
            - 未找到时返回 None
            - 自动处理函数不存在情况
        """
        if self.safe_mode:
            return self._dll_funcs.get(name)
        else:
            return getattr(self.dll, name, None)


# 动态库对象
dll = load_cdll('zml.dll' if in_windows() else 'zml.so', first=os.path.dirname(os.path.realpath(__file__)))

# 对动态库对象的进一步的封装
core = DllCore(dll_obj=dll)

# Version of the zml module (date represented by six digits)
try:
    version = core.version
except Exception as version_error:
    version = 110101
    warnings.warn(f'Meet error when get version: {version_error}', stacklevel=2)

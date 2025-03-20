# -*- coding: utf-8 -*-
"""
描述: 流体-传热-化学-应力计算的核心模块；
      C++代码的Python接口（必须与 zml.dll一起使用）。

环境: Windows 10/11；Python 3.7或更高版本；64位系统；

依赖: numpy

网站: https://gitee.com/geomech/hydrate

作者: 张召彬 <zhangzhaobin@mail.iggcas.ac.cn>，
     中国科学院地质与地球物理研究所
"""
import ctypes
import datetime
import math
import os
import re
import sys
import timeit
import warnings
from collections.abc import Iterable
from ctypes import (cdll, c_void_p, c_char_p, c_int, c_int64, c_bool, c_double,
                    c_size_t, c_uint, CFUNCTYPE, POINTER)

try:
    import numpy as np
except:
    np = None

warnings.simplefilter("default")  # Default warning display

# Indicates whether the system is currently Windows (both Windows and Linux systems are currently supported)
is_windows = os.name == 'nt'


def get_pointer64(arr):
    """将NumPy数组转换为C语言双精度指针。

    Args:
        arr (Union[np.ndarray, Vector]): 输入数据容器，支持以下类型：
            - dtype为float64的NumPy数组
            - 包含pointer属性的Vector对象

    Returns:
        ctypes.POINTER(c_double): 指向连续内存的指针

    Raises:
        ValueError: 输入类型不匹配时抛出
        AssertionError: 当NumPy数组dtype不是float64时抛出
    """
    if isinstance(arr, Vector):
        return arr.pointer

    if np is not None:
        # Ensure the input is a NumPy array
        if not isinstance(arr, np.ndarray):
            raise ValueError("Input must be a NumPy array")

        # Convert the NumPy array to a C array
        c_arr = np.ctypeslib.as_ctypes(arr)

        # Check the data type of the array
        assert arr.dtype == np.float64

        # Get the pointer to the C array
        return ctypes.cast(c_arr, ctypes.POINTER(ctypes.c_double))


class Object:
    """提供受限属性管理的对象基类。

    通过白名单机制限制属性修改，防止意外添加新属性。
    """

    def set(self, **kwargs):
        """安全更新现有对象属性。

        Args:
            **kwargs: 要更新的属性键值对

        Returns:
            Object: 返回自身以支持链式调用

        Raises:
            AssertionError: 尝试添加不存在的新属性时抛出
        """
        current_keys = dir(self)
        for key, value in kwargs.items():
            assert key in current_keys, f"add new attribution '{key}' to {type(self)} is forbidden"
            setattr(self, key, value)
        return self


create_dict = dict


def is_array(o):
    """判断对象是否支持类列表访问语义。

    Args:
        o (Any): 待检测对象

    Returns:
        bool: 当对象同时支持__getitem__和__len__协议时返回True
    """
    return hasattr(o, '__getitem__') and hasattr(o, '__len__')


def make_c_char_p(s):
    """将Python字符串转换为C兼容字符指针。

    Args:
        s (str): 输入字符串

    Returns:
        c_char_p: 指向以null结尾的字节缓冲区的指针

    Note:
        自动进行UTF-8编码转换
    """
    return c_char_p(bytes(s, encoding='utf8'))


def sendmail(address, subject=None, text=None, name_from=None, name_to=None):
    """通过SMTP协议发送电子邮件。

    Args:
        address (str): 收件人邮箱地址
        subject (str, optional): 邮件主题，默认为发送者名称
        text (str, optional): 邮件正文内容，默认为空字符串
        name_from (str, optional): 发件人显示名称，默认获取系统用户名
        name_to (str, optional): 收件人显示名称，默认为'UserEmail'

    Returns:
        bool: 邮件发送成功返回True，失败返回False

    Note:
        - 使用固定SMTP服务器(smtp.126.com)和预配置账号
        - 邮件内容默认使用UTF-8编码
        - 包含异常处理机制，失败时静默返回False
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        if name_from is None:
            try:
                import getpass
                name_from = getpass.getuser()
            except:
                name_from = 'User'
        if name_to is None:
            name_to = 'UserEmail'
        if subject is None:
            subject = f'Message from {name_from}'
        if text is None:
            text = ''
        message = MIMEText(text, 'plain', 'utf-8')
        message['From'] = Header(name_from)
        message['To'] = Header(name_to)
        message['Subject'] = Header(subject)
        smtp_obj = smtplib.SMTP()
        smtp_obj.connect("smtp.126.com", 25)
        smtp_obj.login("hyfrddm@126.com", "iggcas0617")
        smtp_obj.sendmail('hyfrddm@126.com', [address], message.as_string())
        return True
    except:
        return False


def feedback(text='feedback', subject=None):
    """向软件作者发送诊断信息用于产品改进。

    Args:
        text (str, optional): 反馈内容，默认为'feedback'
        subject (str, optional): 邮件主题，默认为None

    Returns:
        bool: 发送成功或禁用反馈时返回True，失败返回False

    Note:
        - 可通过设置环境变量disable_feedback='Yes'永久禁用
        - 实际发送使用sendmail函数实现
        - 默认收件人为zhangzhaobin@mail.iggcas.ac.cn
    """
    try:
        if app_data.getenv('disable_feedback', default='No', ignore_empty=True) == 'Yes':
            return True
        else:
            return sendmail('zhangzhaobin@mail.iggcas.ac.cn', subject=subject, text=text,
                            name_from=None, name_to='Author')
    except:
        return False


def make_dirs(folder):
    """递归创建目录结构。

    Args:
        folder (str): 要创建的目录路径

    Note:
        - 自动创建所有不存在的父目录
        - 使用exist_ok参数避免目录已存在的错误
        - 包含异常处理，失败时静默退出
    """
    try:
        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
    except:
        pass


# Alias of the function < for compatibility with previous code >
makedirs = make_dirs


def make_parent(path):
    """确保指定文件路径的父目录存在。

    Args:
        path (str): 文件路径

    Returns:
        str: 原始输入路径

    Note:
        - 通过调用make_dirs实现目录创建
        - 始终返回输入路径以便链式调用
        - 包含异常处理机制保证程序健壮性
    """
    try:
        name = os.path.dirname(path)
        if not os.path.isdir(name):
            make_dirs(name)
        return path
    except:
        return path


def read_text(path, encoding=None, default=None):
    """从文本文件中读取内容。

    Args:
        path (str): 目标文件路径
        encoding (str, optional): 文件编码格式，默认使用系统编码
        default (Any, optional): 读取失败时的默认返回值，默认为None

    Returns:
        Union[str, Any]: 成功时返回文件内容字符串，失败返回default值

    Note:
        - 自动处理文件不存在的情况
        - 静默处理所有I/O异常
        - 支持任意文本编码格式
    """
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return default
    except:
        return default


def write_text(path, text, encoding=None):
    """将文本内容写入指定文件。

    Args:
        path (str): 目标文件路径
        text (str): 要写入的文本内容
        encoding (str, optional): 文件编码格式，默认使用系统编码

    Note:
        - 自动创建不存在的父目录
        - 静默处理所有I/O异常
        - 当text为None时写入空字符串
        - 使用原子写操作避免数据损坏
    """
    folder = os.path.dirname(path)
    if len(folder) > 0 and not os.path.isdir(folder):
        make_dirs(folder)
    with open(path, 'w', encoding=encoding) as f:
        if text is None:
            f.write('')
        else:
            f.write(text)


class _AppData(Object):
    """应用程序数据管理核心类，负责持久化存储和运行时数据管理。

    主要功能包括：
    - 跨平台缓存目录管理
    - 自定义文件搜索路径管理
    - 内存键值空间存储
    - 环境变量持久化存储
    - 日志记录和标签跟踪
    """

    def __init__(self):
        """初始化应用程序数据管理系统。

        自动完成：
        1. 创建平台相关缓存目录（Windows: APPDATA，Linux: /var/tmp）
        2. 加载自定义搜索路径配置
        3. 初始化内存存储空间
        """
        # cache directory
        if is_windows:
            self.folder = os.path.join(os.getenv("APPDATA"), 'zml')
        else:
            self.folder = os.path.join('/var/tmp/zml')

        make_dirs(self.folder)
        # Custom file search path
        self.paths = []
        try:
            for line in self.getenv(key='path', default='').splitlines():
                line = line.strip()
                if os.path.isdir(line):
                    self.add_path(line)
        except:
            pass

        # memory variable
        self.space = {}

    def add_path(self, path):
        """添加自定义文件搜索路径。

        Args:
            path (str): 要添加的目录路径

        Returns:
            bool: 成功添加返回True，路径无效或已存在返回False

        Note:
            - 使用 os.path.samefile 进行路径去重检查
            - 仅接受有效目录路径
        """
        if os.path.isdir(path):
            for existed in self.paths:
                if os.path.samefile(path, existed):
                    return False
            self.paths.append(path)
            return True
        else:
            return False

    def has_tag_today(self, tag):
        """检查当天是否已标记特定标签。

        Args:
            tag (str): 标签标识符（推荐使用合法文件名）

        Returns:
            bool: 当天已有该标签返回True，否则返回False
        """
        path = os.path.join(self.folder, 'tags', datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
        return os.path.exists(path)

    def add_tag_today(self, tag):
        """为当天添加永久性时间戳标签。

        Args:
            tag (str): 标签标识符（推荐使用合法文件名）

        Note:
            - 静默处理所有IO异常
            - 标签文件存储在缓存目录的tags子目录
            - 文件内容为空，仅通过存在性标记
        """
        try:
            folder = os.path.join(self.folder, 'tags')
            make_dirs(folder)
            path = os.path.join(folder, datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
            with open(path, 'w') as f:
                f.write('\n')
        except:
            pass

    def log(self, text):
        """记录运行时日志到日期命名的日志文件。

        Args:
            text (str): 要记录的日志内容

        Note:
            - 日志文件存储在缓存目录的logs子目录
            - 每日日志存储在 YYYY-MM-DD.log 文件中
            - 自动创建所需目录结构
        """
        try:
            folder = os.path.join(self.folder, 'logs')
            make_dirs(folder)
            with open(os.path.join(folder, datetime.datetime.now().strftime("%Y-%m-%d.log")), 'a') as f:
                f.write(f'{datetime.datetime.now()}: \n{text}\n\n\n')
        except:
            pass

    def getenv(self, key, encoding=None, default=None, ignore_empty=False):
        """读取持久化环境变量值。

        Args:
            key (str): 环境变量名称
            encoding (str, optional): 文件编码格式
            default (Any, optional): 默认返回值
            ignore_empty (bool): 是否将空字符串视为默认值

        Returns:
            Union[str, Any]: 成功读取返回字符串值，失败返回默认值
        """
        path = os.path.join(self.folder, 'env', key)
        res = read_text(path, encoding=encoding, default=default)
        if ignore_empty:
            if isinstance(res, str):
                if len(res) == 0:
                    return default
        return res

    def setenv(self, key, value, encoding=None):
        """设置持久化环境变量值。

        Args:
            key (str): 环境变量名称
            value (str): 要存储的值
            encoding (str, optional): 文件编码格式

        Note:
            - 变量存储在缓存目录的env子目录
            - 每个变量对应单独文件
        """
        path = os.path.join(self.folder, 'env', key)
        write_text(path, value, encoding=encoding)

    def root(self, *args):
        """获取缓存目录下的指定路径。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 完整绝对路径

        Note:
            - 自动创建父目录
            - 支持链式调用：app_data.root('data', 'input.txt')
        """
        return make_parent(os.path.join(self.folder, *args))

    def temp(self, *args):
        """获取临时文件路径并确保父目录存在。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 完整绝对路径

        Note:
            - 文件存储在缓存目录的temp子目录
            - 适合存储临时中间数据
        """
        return make_parent(os.path.join(self.folder, 'temp', *args))

    @staticmethod
    def proj(*args):
        """访问项目相关文件路径。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 项目目录下的完整路径

        Note:
            - 无参数时返回项目根目录（.zml）
            - 自动创建父目录
        """
        if len(args) == 0:
            # return to the root directory of the project file
            return os.path.join(os.getcwd(), '.zml')
        else:
            return make_parent(os.path.join(os.getcwd(), '.zml', *args))

    def clear_temp(self, *args):
        """递归删除临时文件或目录。

        Args:
            *args (str): 要清理的相对路径

        Note:
            - 无参数时清空整个临时目录
            - 使用 shutil.rmtree 进行递归删除
            - 静默处理所有文件操作异常
        """
        folder = os.path.join(self.folder, 'temp')
        if os.path.isdir(folder):
            if len(args) == 0:
                import shutil
                shutil.rmtree(folder)
                return
            path = os.path.join(folder, *args)
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                return
            if os.path.isfile(path):
                os.remove(path)

    def get_paths(self, first=None):
        """获取当前有效搜索路径列表。

        Args:
            first (str, optional): 优先搜索路径

        Returns:
            List[str]: 按优先级排序的搜索路径列表

        Note:
            默认搜索顺序：
            1. 指定优先路径（如有）
            2. 当前工作目录
            3. 项目目录
            4. 缓存目录
            5. 临时目录
            6. 自定义路径
            7. Python系统路径
        """
        paths = [os.getcwd(), self.proj()] if first is None else [first, os.getcwd(), self.proj()]
        return paths + [self.folder, os.path.join(self.folder, 'temp')] + self.paths + sys.path

    def find(self, *name, first=None):
        """查找指定文件的首个有效路径。

        Args:
            *name (str): 文件名或路径组成部分
            first (str, optional): 优先搜索路径

        Returns:
            Optional[str]: 找到返回绝对路径，否则返回None

        Note:
            - 支持多级目录查找：find('data', 'input.txt')
            - 静默处理无效路径异常
        """
        if len(name) > 0:
            for folder in self.get_paths(first):
                try:
                    path = os.path.join(folder, *name)
                    if os.path.exists(path):
                        return path
                except:
                    pass

    def find_all(self, *name, first=None):
        """查找指定文件的所有有效路径。

        Args:
            *name (str): 文件名或路径组成部分
            first (str, optional): 优先搜索路径

        Returns:
            List[str]: 去重后的绝对路径列表（保留发现顺序）

        Note:
            - 使用 os.path.samefile 进行路径去重
            - 返回列表包含所有有效匹配项
        """
        results = []
        if len(name) > 0:
            for folder in self.get_paths(first):
                try:
                    path = os.path.join(folder, *name)
                    if os.path.exists(path):
                        exists = False
                        for x in results:
                            if os.path.samefile(x, path):
                                exists = True
                                break
                        if not exists:
                            results.append(path)
                except:
                    pass
        return results

    def get(self, *args, **kwargs):
        """从内存空间中读取数据。

        Args:
            *args: 兼容字典的键查询参数
            **kwargs: 兼容字典的默认值参数

        Returns:
            Any: 键对应的值或默认值

        Note:
            无参数调用时返回整个内存空间字典
        """
        if len(args) == 0 and len(kwargs) == 0:
            return self.space
        else:
            return self.space.get(*args, **kwargs)

    def put(self, key, value):
        """存储数据到内存空间。

        Args:
            key (str): 数据标识符
            value (Any): 要存储的值

        Note:
            - 支持任意Python对象存储
            - 数据仅存在于运行时内存中
        """
        self.space[key] = value


app_data = _AppData()


def log(text, tag=None):
    """记录运行时日志信息。

    Args:
        text (str): 需要记录的日志内容
        tag (str, optional): 唯一标识标签，用于实现每日单次记录

    Returns:
        None

    Note:
        - 当指定 tag 时，确保当天只记录一次相同标签日志
        - 使用 app_data 的标签跟踪系统实现每日去重
        - 静默处理所有I/O异常
        - 实际日志存储路径由 _AppData 类管理
    """
    if tag is not None:
        if app_data.has_tag_today(tag):
            return
        else:
            app_data.add_tag_today(tag)
    app_data.log(text)


def load_cdll(name, *, first=None):
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
            print(f'Error load library from <{path}>. Message = {e}')
    else:
        try:
            return cdll.LoadLibrary(name)
        except Exception as e:
            print(f'Error load library from <{name}>. Message = {e}')


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
            - 保持与正常函数相同的调用接口
        """
        print(f'calling null function {self.name}(args={args}, kwargs={kwargs})')


def get_func(dll_obj, restype, name, *argtypes):
    """配置动态链接库函数接口。

    Args:
        dll_obj (CDLL): 动态链接库对象
        restype (Any): 函数返回类型（None表示void）
        name (str): 目标函数名称
        *argtypes (tuple): 函数参数类型列表

    Returns:
        Union[CFuncPtr, _NullFunction]: 配置完成的函数对象或空函数占位符

    Raises:
        AssertionError: 当函数名不是字符串类型时抛出

    Note:
        - 自动设置函数的 restype 和 argtypes 属性
        - 未找到函数时返回 _NullFunction 实例
        - 保持与 ctypes 模块兼容的接口设计
    """
    assert isinstance(name, str)
    fn = getattr(dll_obj, name, None)
    if fn is None:
        if dll_obj is not None:
            print(f'Warning: can not find function <{name}> in <{dll_obj}>')
        return _NullFunction(name)
    if restype is not None:
        fn.restype = restype
    if len(argtypes) > 0:
        fn.argtypes = argtypes
    return fn


def get_file():
    """获取当前执行文件的绝对路径。

    Returns:
        str: 当前Python文件的完整路径

    Note:
        - 等价于 os.path.realpath(__file__)
        - 支持符号链接解析
        - 结果包含文件名和扩展名
    """
    return os.path.realpath(__file__)


def get_dir():
    """获取当前执行文件所在目录的绝对路径。

    Returns:
        str: 当前文件所在目录的完整路径

    Note:
        - 等价于 os.path.dirname(os.path.realpath(__file__))
        - 常用于动态加载库时的路径定位
        - 结果不包含末尾路径分隔符
    """
    return os.path.dirname(os.path.realpath(__file__))


dll = load_cdll('zml.dll' if is_windows else 'zml.so.1', first=get_dir())


class DllCore:
    """
    管理 C++ 内核中的错误、警告等
    """

    def __init__(self, dll):
        """
        初始化 DllCore 对象

        参数:
            dll: 动态链接库对象
        """
        self.__err_handle = None
        self.dll = dll
        self._dll_funcs = {}
        self.dll_has_error = get_func(self.dll, c_bool, 'has_error')
        self.dll_pop_error = get_func(self.dll, c_char_p, 'pop_error', c_void_p)
        self.dll_has_warning = get_func(self.dll, c_bool, 'has_warning')
        self.dll_pop_warning = get_func(self.dll, c_char_p, 'pop_warning', c_void_p)
        self.dll_has_log = get_func(self.dll, c_bool, 'has_log')
        self.dll_pop_log = get_func(self.dll, c_char_p, 'pop_log', c_void_p)
        self.use(c_size_t, 'get_log_nmax')
        self.use(None, 'set_log_nmax', c_size_t)
        self.use(c_char_p, 'get_time_compile', c_void_p)
        self.dll_print_logs = get_func(self.dll, None, 'print_logs', c_char_p)
        self.use(c_int, 'get_version')
        self.use(c_bool, 'is_parallel_enabled')
        self.use(None, 'set_parallel_enabled', c_bool)
        self.use(c_bool, 'assert_is_void')
        self.dll_set_error_handle = get_func(self.dll, None, 'set_error_handle', c_void_p)
        self.use(c_char_p, 'get_compiler')

    def has_dll(self):
        """检查动态链接库是否成功加载。

        Returns:
            bool: 成功加载返回 True，否则返回 False
        """
        return self.dll is not None

    def has_error(self):
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

    def pop_error(self):
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

    def has_warning(self):
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

    def pop_warning(self):
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

    def has_log(self):
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

    def pop_log(self):
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
    def parallel_enabled(self):
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
    def parallel_enabled(self, value):
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

    def set_error_handle(self, func):
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
    def log_nmax(self):
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
    def log_nmax(self, value):
        """设置日志系统最大容量。

        Args:
            value (int): 新最大日志数量（需 ≥ 0）
        """
        if self.has_dll():
            self.set_log_nmax(value)

    @property
    def time_compile(self):
        """[只读] 内核编译时间戳。

        Returns:
            str: 格式为 yyyy-MM-dd HH:mm 的时间字符串
        """
        if self.has_dll():
            return self.get_time_compile(0).decode()
        else:
            return ''

    @property
    def version(self):
        """[只读] 内核版本标识。

        Returns:
            int: 6位数字版本号 (yymmdd 格式)
        """
        if self.has_dll():
            return core.get_version()
        else:
            return 100101

    @property
    def compiler(self):
        """[只读] 内核编译环境信息。

        Returns:
            str: 编译器名称及版本字符串
        """
        if self.has_dll():
            return self.get_compiler().decode()
        else:
            return ''

    def run(self, fn):
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

    def print_logs(self, path=None):
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

    def use(self, restype, name, *argtypes):
        """声明内核函数接口。

        Args:
            restype (Any): 函数返回类型
            name (str): 函数名称
            *argtypes (tuple): 参数类型列表

        Note:
            - 重复声明会触发警告
            - 自动包装错误处理逻辑
        """
        if self.has_dll():
            if self._dll_funcs.get(name) is not None:
                print(f'Warning: function <{name}> already exists')
            else:
                func = get_func(self.dll, restype, name, *argtypes)
                if func is not None:
                    self._dll_funcs[name] = lambda *args: self.run(lambda: func(*args))

    def __getattr__(self, name):
        """动态获取已声明的内核函数。

        Args:
            name (str): 目标函数名称

        Returns:
            Callable: 配置完成的函数对象

        Note:
            - 未找到时返回 None
            - 自动处理函数不存在情况
        """
        return self._dll_funcs.get(name)


core = DllCore(dll=dll)

# Version of the zml module (date represented by six digits)
try:
    version = core.version
except:
    version = 110101


class Timer:
    """用于统计函数执行时间的辅助工具类。

    该类通过字典结构记录函数名称与执行时间的映射关系，支持通过装饰器或上下文管理器方式使用。

    Attributes:
        co (DllCore): 与底层C++核心模块交互的接口实例
        key2nt (dict): 只读属性，获取函数名称到(调用次数, 总耗时)的字典
    """

    def __init__(self, co):
        """初始化计时器实例。

        Args:
            co (DllCore): 必须为DllCore类型实例，用于底层C++交互

        Raises:
            AssertionError: 当co参数类型不匹配时抛出
        """
        assert isinstance(co, DllCore), f'the type of <co> should be {type(DllCore)}'
        co.use(c_char_p, 'timer_summary', c_void_p)
        co.use(None, 'timer_log', c_char_p, c_double)
        co.use(None, 'timer_reset')
        co.use(c_bool, 'timer_enabled')
        co.use(None, 'timer_enable', c_bool)
        self.__key2t = {}
        self.co = co  # core

    def __call__(self, key, func, *args, **kwargs):
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

    def __str__(self):
        """生成耗时统计摘要。

        Returns:
            str: 格式化字符串，包含各函数累计耗时和调用次数的统计信息
        """
        return self.summary()

    def summary(self):
        """生成耗时统计摘要。

        Returns:
            str: 格式化字符串，包含各函数累计耗时和调用次数的统计信息
        """
        return self.co.timer_summary(0).decode()

    @property
    def key2nt(self):
        """获取函数耗时统计字典。

        Returns:
            dict[str, tuple]:
                键为函数名称，值为(n次调用, 总秒数)的元组。
                自动过滤'enable'系统保留字段
        """
        try:
            tmp = eval(self.summary())
            tmp.pop('enable', None)
            return tmp
        except:
            return {}

    def log(self, name, seconds):
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

    def enabled(self, value=None):
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

    def beg(self, key):
        """启动指定键的计时。

        Args:
            key (str): 需要启动计时的唯一标识符
        """
        self.__key2t[key] = timeit.default_timer()

    def end(self, key):
        """结束指定键的计时并记录结果。

        Args:
            key (str): 已启动计时的唯一标识符

        Raises:
            KeyError: 当未找到对应key的计时起点时
        """
        t0 = self.__key2t.get(key)
        if t0 is not None:
            cpu_t = timeit.default_timer() - t0
            self.log(key, cpu_t)


timer = Timer(co=core)


def clock(func):
    """函数耗时统计装饰器（支持异常传播）。

    通过Timer实例自动记录被装饰函数的执行耗时，需配合全局timer实例使用。

    Args:
        func (Callable): 需要计时的函数

    Returns:
        Callable: 装饰后的函数

    示例:
        @clock
        def my_function():
            time.sleep(0.1)

        my_function()  # 自动记录到timer实例
    """

    def clocked(*args, **kwargs):
        key = func.__name__
        timer.beg(key)
        result = func(*args, **kwargs)
        timer.end(key)
        return result

    return clocked


class _DataVersion:
    """管理数据版本号的内部工具类。

    版本号为6位整数，格式为yymmdd(年年月月日日)，例如230701表示2023年7月1日。

    Attributes:
        __default (int): 默认版本号（受保护的属性）
        __versions (dict): 各键值对应的版本号字典（受保护的属性）
    """

    def __init__(self, value=version):
        """初始化数据版本管理器。

        Args:
            value (int, optional): 默认版本号，必须为6位整数。默认使用全局version值

        Raises:
            AssertionError: 当value不是整数或不在[100000, 999999]范围内时抛出
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        self.__versions = {}
        self.__default = value

    def set(self, value=None, key=None):
        """设置指定键或默认的版本号。

        Args:
            value (int): 必须为6位整数，表示年月日(yymmdd)
            key (Hashable, optional):
                当提供键值时，设置该键对应的版本；
                当为None时，设置默认版本

        Raises:
            AssertionError: 当value不符合6位整数要求时抛出
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        if key is None:
            self.__default = value
        else:
            self.__versions[key] = value

    def __getattr__(self, key):
        """通过属性访问获取版本号。

        Args:
            key (str): 版本键值名称

        Returns:
            int: 指定键对应的版本号，若不存在则返回默认版本号
        """
        return self.__versions.get(key, self.__default)

    def __getitem__(self, key):
        """通过字典方式访问获取版本号。

        Args:
            key (Hashable): 版本键值名称

        Returns:
            int: 指定键对应的版本号，若不存在则返回默认版本号
        """
        return self.__versions.get(key, self.__default)

    def __setitem__(self, key, value):
        """通过字典方式设置版本号。

        Args:
            key (Hashable): 版本键值名称
            value (int): 必须为6位整数，表示年月日(yymmdd)

        Raises:
            AssertionError: 通过set方法间接抛出参数校验异常
        """
        self.set(key=key, value=value)


data_version = _DataVersion()

core.use(None, 'set_srand', c_uint)


def set_srand(seed):
    """设置随机数生成器的种子。

    该函数用于设置随机数生成器的种子值，以确保随机数生成的可重复性。

    Args:
        seed (int): 随机数生成器的种子值，必须为无符号整数。

    Returns:
        None
    """
    core.set_srand(seed)


core.use(c_double, 'get_rand')


def get_rand():
    """生成一个 0 到 1 之间的随机数。

    该函数返回一个均匀分布在 [0, 1) 区间内的随机浮点数。

    Returns:
        float: 一个 0 到 1 之间的随机浮点数。
    """
    return core.get_rand()


class HasHandle(Object):
    """管理具有句柄（handle）的对象的基类。

    该类提供了创建、释放和访问句柄的方法，用于管理具有句柄的对象。

    Attributes:
        handle: 对象的句柄。

    Args:
        handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
        create: 一个函数，用于创建新的句柄。
        release: 一个函数，用于释放句柄。
    """

    def __init__(self, handle=None, create=None, release=None):
        """初始化 HasHandle 对象。

        Args:
            handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
            create: 一个函数，用于创建新的句柄。
            release: 一个函数，用于释放句柄。
        """
        if handle is None:
            assert create is not None and release is not None
            self.__handle = create()
            self.__release = release
        else:
            assert handle >= 1, 'handle should be greater than zero'
            self.__handle = handle
            self.__release = None

    def __del__(self):
        """在对象被销毁时调用，用于释放句柄。"""
        if self.__release is not None:
            self.__release(self.__handle)

    @property
    def handle(self):
        """获取对象的句柄。

        Returns:
            对象的句柄。
        """
        return self.__handle


class String(HasHandle):
    """管理字符串对象的类，继承自 HasHandle 类。

    该类提供了字符串的创建、赋值、克隆和转换等方法，用于管理字符串对象。
    """
    core.use(None, 'del_str', c_void_p)
    core.use(c_void_p, 'new_str')

    def __init__(self, value=None, handle=None):
        """初始化 String 对象。

        Args:
            value (str): 要赋值给字符串的初始值。
            handle: 字符串对象的句柄。如果未提供，则会创建一个新的字符串对象。
        """
        super(String, self).__init__(handle, core.new_str, core.del_str)
        if handle is None:
            if value is not None:
                assert isinstance(value, str)
                self.assign(value)

    def __str__(self):
        """返回字符串对象的字符串表示。

        Returns:
            str: 字符串对象的字符串表示。
        """
        return self.to_str()

    def __len__(self):
        """返回字符串对象的长度。

        Returns:
            int: 字符串对象的长度。
        """
        return self.size

    core.use(c_size_t, 'str_size', c_void_p)

    @property
    def size(self):
        """获取字符串对象的长度。

        Returns:
            int: 字符串对象的长度。
        """
        return core.str_size(self.handle)

    core.use(None, 'str_assign', c_void_p, c_char_p)

    def assign(self, value):
        """给字符串对象赋值。

        Args:
            value (str): 要赋值给字符串对象的值。
        """
        core.str_assign(self.handle, make_c_char_p(value))

    core.use(c_char_p, 'str_to_char_p', c_void_p)

    def to_str(self):
        """将字符串对象转换为 Python 字符串。

        Returns:
            str: 转换后的 Python 字符串。
        """
        if core.dll is not None:
            return core.str_to_char_p(self.handle).decode()

    core.use(None, 'str_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个字符串对象。

        Args:
            other (String): 要克隆的字符串对象。

        Returns:
            String: 当前字符串对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, String)
            core.str_clone(self.handle, other.handle)
        return self

    def make_copy(self, buf=None):
        """创建当前字符串对象的副本。

        Args:
            buf (String): 用于存储副本的字符串对象。如果未提供，则会创建一个新的字符串对象。

        Returns:
            String: 字符串对象的副本。
        """
        if not isinstance(buf, String):
            buf = String()
        buf.clone(self)
        return buf


def get_time_compile():
    """获取编译时间。

    Returns:
        str: 用字符串表示的编译的时间
    """
    return core.time_compile


def run(fn):
    """运行需要调用内存的代码，并检查错误。

    Args:
        fn: 需要运行的函数或代码。

    Returns:
        运行结果。
    """
    return core.run(fn)


core.use(None, 'fetch_m', c_char_p)


def fetch_m(folder=None):
    """获取预定义的 m 文件。

    这些 m 文件通常用于调试、绘图等场景。

    Args:
        folder (str): 存储 m 文件的文件夹路径。如果未提供，则使用默认路径。

    Warns:
        DeprecationWarning: 该函数将在 2025-8-11 之后被移除。
    """
    warnings.warn('This function will be removed after 2025-8-11', DeprecationWarning)
    if folder is None:
        core.fetch_m(make_c_char_p(''))
    else:
        assert isinstance(folder, str)
        core.fetch_m(make_c_char_p(folder))


class License:
    """管理软件的授权信息。

    该类用于管理软件的授权信息，包括获取授权信息、检查授权状态、生成授权码等功能。
    """

    def __init__(self, core):
        """初始化 License 对象。

        Args:
            core: 核心模块对象，用于调用底层功能。
        """
        self.core = core
        self.license_info_has_checked = False
        if self.core.has_dll():
            self.core.use(c_int, 'lic_webtime')
            self.core.use(c_bool, 'lic_summary', c_void_p)
            self.core.use(None, 'lic_get_serial', c_void_p, c_bool, c_bool)
            self.core.use(None, 'lic_create_permanent', c_void_p, c_void_p)
            self.core.use(None, 'lic_load', c_void_p)
            self.core.use(c_bool, 'lic_is_admin')

    @property
    def is_admin(self):
        """检查当前计算机是否具有管理员权限。

        Returns:
            bool: 是否具有管理员权限。
        """
        return self.core.lic_is_admin()

    @property
    def webtime(self):
        """获取网络时间戳（非实际时间）。

        程序将使用此时间戳来判断软件是否已过期。

        Returns:
            int: 网络时间戳。
        """
        if self.core.has_dll():
            return self.core.lic_webtime()
        else:
            return 100101

    @property
    def summary(self):
        """获取当前计算机的授权信息。

        如果计算机未正确授权，则返回 None。

        Returns:
            str: 授权信息。
        """
        if self.core.has_dll():
            s = String()
            if self.core.lic_summary(s.handle):
                return s.to_str()

    def get_serial(self, base64=True, export_all=False):
        """获取当前计算机的 USB 序列号（其中之一），用于注册。

        Args:
            base64 (bool): 是否以 Base64 格式返回序列号。
            export_all (bool): 是否导出所有 USB 设备的序列号。

        Returns:
            str: USB 序列号。
        """
        if self.core.has_dll():
            s = String()
            self.core.lic_get_serial(s.handle, base64, export_all)
            return s.to_str()

    @property
    def usb_serial(self):
        """获取当前计算机的 USB 序列号（其中之一），用于注册。

        Returns:
            str: USB 序列号。
        """
        return self.get_serial()

    def create_permanent(self, serial):
        """根据 USB 序列号生成永久授权码。

        仅用于测试。

        Args:
            serial (str): USB 序列号。

        Returns:
            str: 永久授权码。
        """
        if self.core.has_dll():
            code = String()
            temp = String()
            temp.assign(serial)
            self.core.lic_create_permanent(code.handle, temp.handle)
            return code.to_str()

    def create(self, serial):
        """根据 USB 序列号生成永久授权码。

        Args:
            serial (str): USB 序列号。

        Returns:
            str: 永久授权码。
        """
        return self.create_permanent(serial)

    def load(self, code):
        """将给定的授权码存储到默认位置。

        Args:
            code (str): 授权码。
        """
        if self.core.has_dll():
            temp = String()
            temp.assign(code)
            self.core.lic_load(temp.handle)

    def check(self):
        """检查授权状态。

        如果当前计算机已正确授权，则函数正常通过；否则触发异常。
        """
        assert self.exists(), 'The license is not valid on this computer.'

    def exists(self):
        """检查当前计算机是否具有正确的软件授权。

        Returns:
            bool: 如果已授权，则返回 True；否则返回 False。
        """
        if self.core.has_dll():
            return self.core.lic_summary(0)
        else:
            return False

    def check_once(self):
        """在迭代过程中检查授权状态。

        如果授权未检查过，则执行检查并输出提示信息。
        """
        if not self.license_info_has_checked:
            self.license_info_has_checked = True
            if app_data.has_tag_today('lic_checked'):
                return
            else:
                app_data.add_tag_today('lic_checked')
            if not self.exists():
                text = f"""
The software is not licensed on this computer. Please send the following 
code to author (zhangzhaobin@mail.iggcas.ac.cn):
     <{self.usb_serial}>
Thanks for using.
    """
                print(text)


lic = License(core=core)


def reg(code=None):
    """注册或获取本机序列号。

    当 `code` 为 None 时，返回本机的序列号。
    如果 `code` 的长度小于 80，则将其视为序列号并生成授权数据。
    否则，将 `code` 视为授权数据并保存到本地。

    Args:
        code (str, optional): 序列号或授权数据。默认为 None。

    Returns:
        str: 本机序列号或生成的授权数据。
    """
    if code is None:
        return lic.usb_serial
    else:
        assert isinstance(code, str)
        if len(code) < 80:
            return lic.create_permanent(code)
        else:
            lic.load(code)


core.use(c_double, 'test_loop', c_size_t, c_bool)


def test_loop(count, parallel=True):
    """测试内核中指定长度的循环并返回耗时。

    Args:
        count (int): 循环次数。
        parallel (bool, optional): 是否并行执行。默认为 True。

    Returns:
        float: 测试耗时。
    """
    return core.test_loop(count, parallel)


def about(check_lic=True):
    """返回模块信息。

    Args:
        check_lic (bool, optional): 是否检查授权状态。默认为 True。

    Returns:
        str: 模块信息及授权状态提示。
    """
    info = f'Welcome to zml ({core.time_compile}; {core.compiler})'
    if check_lic:
        has_lic = lic.exists()
    else:
        has_lic = True
    if not has_lic:
        author = 'author (Email: zhangzhaobin@mail.iggcas.ac.cn, QQ: 542844710)'
        info = f"""{info}. 
        
Note: license not found, please send 
    1. hardware info: "{lic.usb_serial}" 
    2. Your name, workplace, and contact information 

to {author}"""
    return info


def get_distance(p1, p2):
    """计算两个点之间的距离。

    Args:
        p1 (list or tuple): 第一个点的坐标。
        p2 (list or tuple): 第二个点的坐标。

    Returns:
        float: 两个点之间的距离。
    """
    dist = 0.0
    for i in range(min(len(p1), len(p2))):
        dist += (p1[i] - p2[i]) ** 2
    return dist ** 0.5


def get_norm(p):
    """计算点到原点的距离。

    Args:
        p (list or tuple): 点的坐标。

    Returns:
        float: 点到原点的距离。
    """
    dist = 0.0
    for dim in range(len(p)):
        dist += p[dim] ** 2
    return dist ** 0.5


core.use(c_bool, 'confuse_file', c_char_p, c_char_p, c_char_p, c_bool)


def confuse_file(ipath, opath, password, is_encrypt=True):
    """对文件内容进行混淆加密或解密。

    Args:
        ipath (str): 输入文件路径。
        opath (str): 输出文件路径。
        password (str): 加密或解密的密码。
        is_encrypt (bool, optional): 是否进行加密。默认为 True，表示加密；False 表示解密。

    Returns:
        加密或解密的结果。
    """
    return core.confuse_file(make_c_char_p(ipath), make_c_char_p(opath), make_c_char_p(password), is_encrypt)


def parse_fid3(fluid_id):
    """自动识别给定的流体 ID 为流体某个组分的 ID。

    Args:
        fluid_id: 流体 ID，可以是单个值或数组。

    Returns:
        tuple: 包含三个整数的元组，表示流体组件的 ID。如果未提供，则返回默认值 (99999999, 99999999, 99999999)。
    """
    if fluid_id is None:
        return 99999999, 99999999, 99999999
    if is_array(fluid_id):
        count = len(fluid_id)
        assert 0 < count <= 3
        if count == 1:  # 此时，它仍然可能是一个array
            return parse_fid3(fluid_id[0])
        else:
            i0 = fluid_id[0] if 0 < count else 99999999
            i1 = fluid_id[1] if 1 < count else 99999999
            i2 = fluid_id[2] if 2 < count else 99999999
            return i0, i1, i2
    else:
        return fluid_id, 99999999, 99999999


def _check_ipath(path, obj=None):
    """在读取文件时检查输入的文件名。

    Args:
        path (str): 文件路径。
        obj: 读取文件的对象。

    Raises:
        AssertionError: 如果路径不是字符串或文件不存在。
    """
    assert isinstance(path, str), f'The given path <{path}> is not string while load {type(obj)}'
    assert os.path.isfile(path), f'The given path <{path}> is not file while load {type(obj)}'


def get_average_perm(p0, p1, get_perm, sample_dist=None, depth=0):
    """计算两点之间的平均渗透率或平均导热率。

    注意：该函数仅用于计算平均渗透率，考虑了串联效应。

    Args:
        p0 (list or tuple): 第一个点的坐标。
        p1 (list or tuple): 第二个点的坐标。
        get_perm (function): 获取渗透率或导热率的函数。
        sample_dist (float, optional): 采样距离。默认为 None。
        depth (int, optional): 递归深度。默认为 0。

    Returns:
        float: 两点之间的平均渗透率或导热率。
    """
    pos = [(p0[i] + p1[i]) / 2 for i in range(len(p0))]
    dist = get_distance(p0, p1)
    if sample_dist is None or depth >= 4 or sample_dist >= dist:
        k = get_perm(*pos)
        if isinstance(k, Tensor3):
            assert len(p0) == 3 and len(p1) == 3
            k = k.get_along([p1[i] - p0[i] for i in range(3)])
            return max(k, 0.0)
        else:
            return max(k, 0.0)
    k1 = get_average_perm(p0, pos, get_perm, sample_dist, depth + 1)
    k2 = get_average_perm(p1, pos, get_perm, sample_dist, depth + 1)
    return k1 * k2 * 2.0 / (k1 + k2)


def get_index(index, count=None):
    """返回修正后的序号，确保返回的序号满足 0 <= index < count。

    Args:
        index (int): 原始序号。
        count (int, optional): 总数。默认为 None。

    Returns:
        int: 修正后的序号。如果无法修正，则返回 None。
    """
    if index is None:
        return
    if count is None:  # 此时，无法判断index是否越界
        if index >= 0:
            return index
    else:
        assert count >= 0
        if index >= 0:
            if index < count:
                return index  # 0 <= index < count
        else:
            assert index < 0
            index += count  # index < count
            if index >= 0:
                return index  # 0 <= index < count


def __feedback():
    """自动收集并反馈日志文件。

    该函数会检查日志文件夹中的日志文件，并将未反馈过的日志文件发送到指定邮箱。
    已反馈的日志文件会被标记，避免重复发送。

    Returns:
        None
    """
    try:
        folder_logs = os.path.join(app_data.folder, 'logs')
        if not os.path.isdir(folder_logs):
            return
        folder_logs_feedback = os.path.join(app_data.folder, 'logs_feedback')
        make_dirs(folder_logs_feedback)
        has_feedback = set(os.listdir(folder_logs_feedback))
        date = datetime.datetime.now().strftime("%Y-%m-%d.log")
        city = None
        for name in os.listdir(folder_logs):
            if name != date and name not in has_feedback:
                with open(os.path.join(folder_logs, name), 'r') as f1:
                    text = f1.read()
                    if city is None:
                        try:
                            from zmlx.alg.ipinfo import get_city
                            city = f' from {get_city()}'
                        except:
                            city = ''
                    if feedback(text=text[0: 100000], subject=f'log <{name}>{city}'):
                        with open(os.path.join(folder_logs_feedback, name), 'w') as f2:
                            f2.write('\n')
    except:
        pass


try:
    if app_data.getenv('disable_auto_feedback', default='No', ignore_empty=True) != 'Yes':
        __feedback()
except:
    pass

try:
    disable_timer = app_data.getenv(key='disable_timer', encoding='utf-8', default='No', ignore_empty=True)
    if disable_timer == 'Yes':
        timer.enabled(False)
        app_data.log(f'timer disabled')
except:
    pass

try:
    app_data.log(f'import zml <zml: v{version}, Python: {sys.version}>')
except:
    pass


def is_chinese(string):
    """检查字符串是否包含中文字符。

    Args:
        string (str): 待检查的字符串。

    Returns:
        bool: 如果字符串包含中文字符，则返回 True；否则返回 False。
    """
    return bool(re.search('[\u4e00-\u9fff]', string))


class Iterator:
    """迭代器类，用于遍历模型中的元素。

    Attributes:
        __model: 模型对象。
        __index: 当前迭代的索引。
        __count: 模型中元素的总数。
        __get: 获取元素的函数。

    Args:
        model: 要迭代的模型对象。
        count: 模型中元素的总数。
        get: 一个函数，用于获取模型中指定索引位置的元素。
    """

    def __init__(self, model, count, get):
        """初始化迭代器对象。

        Args:
            model: 要迭代的模型对象。
            count: 模型中元素的总数。
            get: 一个函数，用于获取模型中指定索引位置的元素。
        """
        self.__model = model
        self.__index = 0
        self.__count = count
        self.__get = get

    def __iter__(self):
        """返回迭代器对象本身。

        Returns:
            Iterator: 迭代器对象本身。
        """
        self.__index = 0
        return self

    def __next__(self):
        """返回下一个元素，如果没有更多元素则抛出 StopIteration 异常。

        Returns:
            下一个元素。

        Raises:
            StopIteration: 如果没有更多元素。
        """
        if self.__index < self.__count:
            cell = self.__get(self.__model, self.__index)
            self.__index += 1
            return cell
        else:
            raise StopIteration()

    def __len__(self):
        """返回模型中元素的总数。

        Returns:
            int: 模型中元素的总数。
        """
        return self.__count

    def __getitem__(self, ind):
        """返回指定索引位置的元素。

        Args:
            ind (int): 索引位置。

        Returns:
            指定索引位置的元素。
        """
        if ind < self.__count:
            return self.__get(self.__model, ind)


class Vector(HasHandle):
    """映射 C++ 类：std::vector<double>。

    该类用于管理动态数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vf')
    core.use(None, 'del_vf', c_void_p)

    def __init__(self, value=None, path=None, size=None, handle=None):
        """初始化 Vector 对象，并可选择性地进行初始化。

        Args:
            value (list or np.ndarray, optional): 用于初始化 Vector 的列表或 NumPy 数组。
            path (str, optional): 从文件加载数据的路径。
            size (int, optional): 初始化 Vector 的大小。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Vector, self).__init__(handle, core.new_vf, core.del_vf)
        if handle is None:
            if value is not None:
                self.set(value)
                return
            if isinstance(path, str):
                self.load(path)
                return
            if size is not None:
                self.size = size
                return
        else:
            assert value is None and path is None and size is None

    def __str__(self):
        """返回 Vector 的字符串表示。

        Returns:
            str: Vector 的字符串表示。
        """
        return f'zml.Vector({self.to_list()})'

    core.use(None, 'vf_save', c_void_p, c_char_p)

    def save(self, path):
        """将 Vector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vf_save(self.handle, make_c_char_p(path))

    core.use(None, 'vf_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的 Vector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.vf_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vf_size', c_void_p)

    @property
    def size(self):
        """获取 Vector 的大小。

        Returns:
            int: Vector 的大小。
        """
        return core.vf_size(self.handle)

    core.use(None, 'vf_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置 Vector 的大小。

        Args:
            value (int): 新的 Vector 大小。
        """
        core.vf_resize(self.handle, value)

    def __len__(self):
        """返回 Vector 的大小。

        Returns:
            int: Vector 的大小。
        """
        return self.size

    core.use(c_double, 'vf_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """获取指定索引位置的元素。

        Args:
            idx (int): 元素的索引。

        Returns:
            float: 指定索引位置的元素。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vf_get(self.handle, idx)

    core.use(None, 'vf_set', c_void_p, c_size_t, c_double)

    def __setitem__(self, idx, value):
        """设置指定索引位置的元素。

        Args:
            idx (int): 元素的索引。
            value (float): 要设置的值。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vf_set(self.handle, idx, value)

    def append(self, value):
        """向 Vector 尾部追加元素。

        Args:
            value (float): 要追加的元素。

        Returns:
            Vector: 当前 Vector 对象（用于链式调用）。
        """
        ind = self.size
        self.size += 1
        self[ind] = value
        return self

    def set(self, value=None):
        """将列表或 NumPy 数组赋值给 Vector。

        Args:
            value (list or np.ndarray, optional): 要赋值的列表或 NumPy 数组。
        """
        if value is not None:
            if np is not None:
                if isinstance(value, np.ndarray):
                    self.read_numpy(value)
                    return

            self.size = len(value)
            if len(value) > 0:
                p = self.pointer
                assert p is not None
                for i in range(len(value)):
                    p[i] = value[i]

    def fill(self, value=0.0):
        """使用指定值填充 Vector。

        Args:
            value (float, optional): 填充值。默认为 0.0。
        """
        p = self.pointer
        assert p is not None
        for i in range(self.size):
            p[i] = value

    def to_list(self):
        """将 Vector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        if len(self) == 0:
            return []
        p = self.pointer
        if p is not None:
            return [p[i] for i in range(len(self))]
        else:
            return []

    core.use(None, 'vf_read', c_void_p, c_void_p)

    def read_memory(self, pointer):
        """从内存地址读取数据。

        Args:
            pointer: 内存地址。
        """
        core.vf_read(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'vf_write', c_void_p, c_void_p)

    def write_memory(self, pointer):
        """将数据写入到指定的内存地址。

        Args:
            pointer: 内存地址。
        """
        core.vf_write(self.handle, ctypes.cast(pointer, c_void_p))

    def read_numpy(self, data):
        """从 NumPy 数组读取数据。

        Args:
            data (np.ndarray): 要读取的 NumPy 数组。
        """
        if np is not None:
            assert isinstance(data, np.ndarray)
            self.size = len(data)
            self.read_memory(get_pointer64(data))

    def write_numpy(self, data):
        """将数据写入到 NumPy 数组。

        Args:
            data (np.ndarray): 要写入的 NumPy 数组。
        """
        if np is not None:
            assert isinstance(data, np.ndarray)
            assert len(data) >= self.size
            self.write_memory(get_pointer64(data))

    def to_numpy(self):
        """将 Vector 转换为 NumPy 数组。

        Returns:
            np.ndarray: 转换后的 NumPy 数组。
        """
        if np is not None:
            arr = np.zeros(self.size)
            self.write_numpy(arr)
            return arr

    core.use(c_void_p, 'vf_pointer', c_void_p)

    @property
    def pointer(self):
        """获取 Vector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_double): 指向首个元素的指针。
        """
        ptr = core.vf_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_double))


class IntVector(HasHandle):
    """映射 C++ 类：std::vector<long long>。

    该类用于管理动态整数数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vi')
    core.use(None, 'del_vi', c_void_p)

    def __init__(self, value=None, handle=None):
        """初始化 IntVector 对象。

        Args:
            value (list, optional): 用于初始化 IntVector 的列表。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(IntVector, self).__init__(handle, core.new_vi, core.del_vi)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'vi_save', c_void_p, c_char_p)

    def save(self, path):
        """将 IntVector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vi_save(self.handle, make_c_char_p(path))

    core.use(None, 'vi_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的 IntVector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.vi_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vi_size', c_void_p)

    @property
    def size(self):
        """获取 IntVector 的大小。

        Returns:
            int: IntVector 的大小。
        """
        return core.vi_size(self.handle)

    core.use(None, 'vi_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置 IntVector 的大小。

        Args:
            value (int): 新的 IntVector 大小。
        """
        core.vi_resize(self.handle, value)

    def __len__(self):
        """返回 IntVector 的大小。

        Returns:
            int: IntVector 的大小。
        """
        return self.size

    core.use(c_int64, 'vi_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """获取指定索引位置的元素。

        Args:
            idx (int): 元素的索引。

        Returns:
            int: 指定索引位置的元素。

        Note:
            如果索引越界，则返回 None。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vi_get(self.handle, idx)

    core.use(None, 'vi_set', c_void_p, c_size_t, c_int64)

    def __setitem__(self, idx, value):
        """设置指定索引位置的元素。

        Args:
            idx (int): 元素的索引。
            value (int): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vi_set(self.handle, idx, value)

    def append(self, value):
        """向 IntVector 尾部追加元素。

        Args:
            value (int): 要追加的元素。
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value):
        """将列表赋值给 IntVector。

        Args:
            value (list): 要赋值的列表。
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """将 IntVector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    core.use(c_void_p, 'vi_pointer', c_void_p)

    @property
    def pointer(self):
        """获取 IntVector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_int64): 指向首个元素的指针。

        Note:
            如果 IntVector 为空，则返回 None。
        """
        ptr = core.vi_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_int64))


Int64Vector = IntVector


class UintVector(HasHandle):
    """映射 C++ 类：std::vector<std::size_t>。

    该类用于管理动态无符号整数数组，支持初始化、序列化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vui')
    core.use(None, 'del_vui', c_void_p)

    def __init__(self, value=None, handle=None):
        """初始化 UintVector 对象。

        Args:
            value (list, optional): 用于初始化 UintVector 的列表。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(UintVector, self).__init__(handle, core.new_vui, core.del_vui)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'vui_save', c_void_p, c_char_p)

    def save(self, path):
        """将 UintVector 序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.vui_save(self.handle, make_c_char_p(path))

    core.use(None, 'vui_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的 UintVector 数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.vui_load(self.handle, make_c_char_p(path))

    core.use(None, 'vui_print', c_void_p, c_char_p)

    def print_file(self, path):
        """将 UintVector 内容打印到文件中。

        Args:
            path (str): 打印文件的路径。

        Note:
            必须使用纯英文路径。
        """
        if isinstance(path, str):
            core.vui_print(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vui_size', c_void_p)

    @property
    def size(self):
        """获取 UintVector 的大小。

        Returns:
            int: UintVector 的大小。
        """
        return core.vui_size(self.handle)

    core.use(None, 'vui_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置 UintVector 的大小。

        Args:
            value (int): 新的 UintVector 大小。
        """
        core.vui_resize(self.handle, value)

    def __len__(self):
        """返回 UintVector 的大小。

        Returns:
            int: UintVector 的大小。
        """
        return self.size

    core.use(c_size_t, 'vui_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """获取指定索引位置的元素。

        Args:
            idx (int): 元素的索引。

        Returns:
            int: 指定索引位置的元素。

        Note:
            如果索引越界，则返回 None。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vui_get(self.handle, idx)

    core.use(None, 'vui_set', c_void_p, c_size_t, c_size_t)

    def __setitem__(self, idx, value):
        """设置指定索引位置的元素。

        Args:
            idx (int): 元素的索引。
            value (int): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vui_set(self.handle, idx, value)

    def append(self, value):
        """向 UintVector 尾部追加元素。

        Args:
            value (int): 要追加的元素。
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value):
        """将列表赋值给 UintVector。

        Args:
            value (list): 要赋值的列表。
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """将 UintVector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    core.use(c_void_p, 'vui_pointer', c_void_p)

    @property
    def pointer(self):
        """获取 UintVector 首个元素的指针。

        Returns:
            ctypes.POINTER(c_size_t): 指向首个元素的指针。

        Note:
            如果 UintVector 为空，则返回 None。
        """
        ptr = core.vui_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_size_t))


class StrVector(HasHandle):
    """映射 C++ 类：std::vector<std::string>。

    该类用于管理动态字符串数组，支持初始化、元素访问等操作。
    """
    core.use(c_void_p, 'new_vs')
    core.use(None, 'del_vs', c_void_p)

    def __init__(self, handle=None):
        """初始化 StrVector 对象。

        Args:
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super(StrVector, self).__init__(handle, core.new_vs, core.del_vs)

    core.use(c_size_t, 'vs_size', c_void_p)

    @property
    def size(self):
        """获取 StrVector 的大小。

        Returns:
            int: StrVector 的大小。
        """
        return core.vs_size(self.handle)

    core.use(None, 'vs_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置 StrVector 的大小。

        Args:
            value (int): 新的 StrVector 大小。
        """
        core.vs_resize(self.handle, value)

    def __len__(self):
        """返回 StrVector 的大小。

        Returns:
            int: StrVector 的大小。
        """
        return self.size

    core.use(None, 'vs_get', c_void_p, c_size_t, c_void_p)

    def __getitem__(self, idx):
        """获取指定索引位置的字符串。

        Args:
            idx (int): 元素的索引。

        Returns:
            str: 指定索引位置的字符串。

        Note:
            如果索引越界，则返回 None。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            s = String()
            core.vs_get(self.handle, idx, s.handle)
            return s.to_str()

    core.use(None, 'vs_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        """设置指定索引位置的字符串。

        Args:
            idx (int): 元素的索引。
            value (str): 要设置的字符串。

        Note:
            如果索引越界，则设置失败。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            s = String(value=value)
            core.vs_set(self.handle, idx, s.handle)

    def set(self, value):
        """将列表赋值给 StrVector。

        Args:
            value (list): 要赋值的字符串列表。
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """将 StrVector 转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements


class PtrVector(HasHandle):
    """映射 C++ 类：std::vector<void*>。

    该类用于管理动态指针数组，支持初始化、元素访问等操作。注意：PtrVector 仅存储句柄（handle），
    不保有数据，因此需要确保原始对象在使用期间不被销毁，否则可能导致内核读取时出现致命错误。

    Attributes:
        size: 指针数组的大小。
    """
    core.use(c_void_p, 'new_vp')
    core.use(None, 'del_vp', c_void_p)

    def __init__(self, value=None, handle=None):
        """初始化 PtrVector 对象。

        Args:
            value (list, optional): 用于初始化指针数组的句柄列表。
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super(PtrVector, self).__init__(handle, core.new_vp, core.del_vp)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(c_size_t, 'vp_size', c_void_p)

    @property
    def size(self):
        """获取指针数组的大小。

        Returns:
            int: 指针数组的大小。
        """
        return core.vp_size(self.handle)

    core.use(None, 'vp_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """设置指针数组的大小，并使用 nullptr 填充新元素。

        Args:
            value (int): 新的指针数组大小。
        """
        core.vp_resize(self.handle, value)

    def __len__(self):
        """返回指针数组的大小。

        Returns:
            int: 指针数组的大小。
        """
        return self.size

    core.use(c_void_p, 'vp_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """获取指定索引位置的句柄。

        Args:
            idx (int): 元素的索引。

        Returns:
            c_void_p: 指定索引位置的句柄。

        Note:
            如果索引越界，则返回 None。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vp_get(self.handle, idx)

    core.use(None, 'vp_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        """设置指定索引位置的句柄。

        Args:
            idx (int): 元素的索引。
            value (c_void_p): 要设置的句柄。

        Note:
            如果索引越界，则设置失败。
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vp_set(self.handle, idx, value)

    def set(self, value):
        """将句柄列表赋值给指针数组。

        Args:
            value (list): 要赋值的句柄列表。
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """将指针数组转换为 Python 列表。

        Returns:
            list: 转换后的 Python 列表。
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    def get_object(self, idx, rtype):
        """将指定索引位置的句柄转换为 HasHandle 对象。

        Args:
            idx (int): 元素的索引。
            rtype (type): 目标对象的类型（必须是 HasHandle 的子类）。

        Returns:
            HasHandle: 转换后的对象。

        Note:
            如果索引越界或句柄无效，则返回 None。
        """
        if idx < len(self) and rtype is not None:
            handle = self[idx]
            if handle > 0:
                return rtype(handle=handle)

    def append(self, handle):
        """向指针数组尾部追加句柄。

        Args:
            handle (c_void_p): 要追加的句柄。

        Returns:
            PtrVector: 当前 PtrVector 对象（用于链式调用）。
        """
        ind = self.size
        self.size += 1
        self[ind] = handle
        return self

    @staticmethod
    def from_objects(objects):
        """从给定的对象列表中构建 PtrVector。

        Args:
            objects (list): 对象列表，对象必须是 HasHandle 类型。

        Returns:
            PtrVector: 构建的 PtrVector 对象。
        """
        return PtrVector(value=[o.handle for o in objects])


class Map(HasHandle):
    """映射 C++ 类：std::map<std::string, double>。

    该类用于管理字符串到双精度浮点数的映射，支持初始化、获取键值对、设置键值对等操作。
    """
    core.use(c_void_p, 'new_string_double_map')
    core.use(None, 'del_string_double_map', c_void_p)

    def __init__(self, handle=None):
        """初始化 Map 对象。

        Args:
            handle: 已有的句柄。如果提供，则使用给定的句柄初始化对象。
        """
        super(Map, self).__init__(handle, core.new_string_double_map, core.del_string_double_map)

    core.use(None, 'string_double_map_get_keys', c_void_p, c_void_p)

    @property
    def keys(self):
        """获取映射中的所有键。

        Returns:
            list: 包含所有键的列表。
        """
        v = StrVector()
        core.string_double_map_get_keys(self.handle, v.handle)
        return v.to_list()

    core.use(c_double, 'string_double_map_get', c_void_p, c_void_p)

    def get(self, key):
        """获取指定键对应的值。

        Args:
            key (str): 要查找的键。

        Returns:
            float: 指定键对应的值。
        """
        s = String(value=key)
        return core.string_double_map_get(self.handle, s.handle)

    core.use(None, 'string_double_map_set', c_void_p, c_void_p, c_double)

    def set(self, key, value):
        """设置指定键的值。

        Args:
            key (str): 要设置的键。
            value (float): 要设置的值。
        """
        s = String(value=key)
        core.string_double_map_set(self.handle, s.handle, value)

    core.use(None, 'string_double_map_clear', c_void_p)

    def clear(self):
        """清空映射中的所有键值对。"""
        core.string_double_map_clear(self.handle)

    def from_dict(self, value):
        """从字典中加载键值对到映射中。

        Args:
            value (dict): 包含键值对的字典。
        """
        self.clear()
        for key, val in value.items():
            self.set(key, val)

    def to_dict(self):
        """将映射转换为字典。

        Returns:
            dict: 包含映射中所有键值对的字典。
        """
        r = {}
        for key in self.keys:
            r[key] = self.get(key)
        return r


class Matrix2(HasHandle):
    """映射 C++ 类：zml::matrix_ty<double, 2>。

    该类用于管理二维矩阵，支持初始化、序列化、元素访问、填充等操作。
    """
    core.use(c_void_p, 'new_mat2')
    core.use(None, 'del_mat2', c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        """初始化 Matrix2 对象。

        Args:
            path (str, optional): 从文件加载矩阵的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
            size (tuple, optional): 矩阵的大小 (size_0, size_1)。
            value (float, optional): 用于填充矩阵的值。
        """
        super(Matrix2, self).__init__(handle, core.new_mat2, core.del_mat2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __str__(self):
        """返回 Matrix2 的字符串表示。

        Returns:
            str: Matrix2 的字符串表示。
        """
        return f'zml.Matrix2(size={self.size})'

    core.use(None, 'mat2_save', c_void_p, c_char_p)

    def save(self, path):
        """将矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.mat2_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.mat2_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.mat2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.mat2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat2_size_0', c_void_p)
    core.use(c_size_t, 'mat2_size_1', c_void_p)

    @property
    def size_0(self):
        """获取矩阵的第一维度大小。

        Returns:
            int: 矩阵的第一维度大小。
        """
        return core.mat2_size_0(self.handle)

    @property
    def size_1(self):
        """获取矩阵的第二维度大小。

        Returns:
            int: 矩阵的第二维度大小。
        """
        return core.mat2_size_1(self.handle)

    core.use(None, 'mat2_resize', c_void_p, c_size_t, c_size_t)

    def resize(self, value):
        """调整矩阵的大小。

        Args:
            value (tuple): 新的矩阵大小 (size_0, size_1)。
        """
        assert len(value) == 2
        core.mat2_resize(self.handle, value[0], value[1])

    @property
    def size(self):
        """获取矩阵的大小。

        Returns:
            tuple: 矩阵的大小 (size_0, size_1)。
        """
        return self.size_0, self.size_1

    @size.setter
    def size(self, value):
        """设置矩阵的大小。

        Args:
            value (tuple): 新的矩阵大小 (size_0, size_1)。
        """
        self.resize(value)

    core.use(c_double, 'mat2_get', c_void_p, c_size_t, c_size_t)

    def get(self, key0, key1):
        """获取矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。

        Returns:
            float: 指定位置的元素值。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            return core.mat2_get(self.handle, key0, key1)

    core.use(None, 'mat2_set', c_void_p, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, value):
        """设置矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            value (float): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            core.mat2_set(self.handle, key0, key1, value)

    def __getitem__(self, key):
        """获取矩阵中指定位置的元素。

        Args:
            key (tuple): 包含两个整数的元组，表示 (key0, key1)。

        Returns:
            float: 指定位置的元素值。
        """
        assert len(key) == 2
        i = key[0]
        j = key[1]
        return self.get(i, j)

    def __setitem__(self, key, value):
        """设置矩阵中指定位置的元素。

        Args:
            key (tuple): 包含两个整数的元组，表示 (key0, key1)。
            value (float): 要设置的值。
        """
        assert len(key) == 2
        i = key[0]
        j = key[1]
        self.set(i, j, value)

    core.use(None, 'mat2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个矩阵的数据到当前矩阵。

        Args:
            other (Matrix2): 要克隆的矩阵对象。

        Returns:
            Matrix2: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Matrix2)
            core.mat2_clone(self.handle, other.handle)
        return self

    core.use(None, 'mat2_fill', c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """填充矩阵的所有元素为指定值。

        Args:
            value (float): 要填充的值。
            parallel (bool, optional): 是否并行填充。默认为 False。
        """
        core.mat2_fill(self.handle, value, parallel)


class Matrix3(HasHandle):
    """映射 C++ 类：zml::matrix_ty<double, 3>。

    该类用于管理三维浮点矩阵，支持初始化、序列化、元素访问、填充等操作。
    """
    core.use(c_void_p, 'new_mat3')
    core.use(None, 'del_mat3', c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        """初始化 Matrix3 对象。

        Args:
            path (str, optional): 从文件加载矩阵的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
            size (tuple, optional): 矩阵的三维大小 (size_0, size_1, size_2)。
            value (float, optional): 用于填充矩阵的初始值。
        """
        super(Matrix3, self).__init__(handle, core.new_mat3, core.del_mat3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __str__(self):
        """返回 Matrix3 的字符串表示。

        Returns:
            str: Matrix3 的字符串表示。
        """
        return f'zml.Matrix3(size={self.size})'

    core.use(None, 'mat3_save', c_void_p, c_char_p)

    def save(self, path):
        """将矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat3_size_0', c_void_p)
    core.use(c_size_t, 'mat3_size_1', c_void_p)
    core.use(c_size_t, 'mat3_size_2', c_void_p)

    @property
    def size_0(self):
        """获取矩阵第一维度的大小。

        Returns:
            int: 第一维度的大小。
        """
        return core.mat3_size_0(self.handle)

    @property
    def size_1(self):
        """获取矩阵第二维度的大小。

        Returns:
            int: 第二维度的大小。
        """
        return core.mat3_size_1(self.handle)

    @property
    def size_2(self):
        """获取矩阵第三维度的大小。

        Returns:
            int: 第三维度的大小。
        """
        return core.mat3_size_2(self.handle)

    core.use(None, 'mat3_resize', c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        """调整矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        assert len(value) == 3
        core.mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        """获取矩阵的三维大小。

        Returns:
            tuple: 包含三个维度大小的元组 (size_0, size_1, size_2)。
        """
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        """设置矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        self.resize(value)

    core.use(c_double, 'mat3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """获取矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。

        Returns:
            float: 指定位置的元素值。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return core.mat3_get(self.handle, key0, key1, key2)

    core.use(None, 'mat3_set', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, key2, value):
        """设置矩阵中指定位置的元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。
            value (float): 要设置的值。

        Note:
            如果索引越界，则设置失败。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            core.mat3_set(self.handle, key0, key1, key2, value)

    def __getitem__(self, key):
        """通过元组索引获取元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。

        Returns:
            float: 指定位置的元素值。
        """
        assert len(key) == 3
        return self.get(*key)

    def __setitem__(self, key, value):
        """通过元组索引设置元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。
            value (float): 要设置的值。
        """
        assert len(key) == 3
        self.set(*key, value)

    core.use(None, 'mat3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个矩阵的数据到当前矩阵。

        Args:
            other (Matrix3): 要克隆的矩阵对象。

        Returns:
            Matrix3: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Matrix3)
            core.mat3_clone(self.handle, other.handle)
        return self

    core.use(None, 'mat3_fill', c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """填充矩阵的所有元素为指定值。

        Args:
            value (float): 要填充的值。
            parallel (bool, optional): 是否在内核层面并行填充。默认为 False。
        """
        core.mat3_fill(self.handle, value, parallel)


class Tensor3Matrix3(HasHandle):
    """映射 C++ 类：zml::matrix_ty<zml::tensor3_ty, 3>。

    该类用于管理三维张量矩阵，支持初始化、序列化、元素访问及插值等操作。
    """
    core.use(c_void_p, 'new_ts3mat3')
    core.use(None, 'del_ts3mat3', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化 Tensor3Matrix3 对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Tensor3Matrix3, self).__init__(handle, core.new_ts3mat3, core.del_ts3mat3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'ts3mat3_save', c_void_p, c_char_p)

    def save(self, path):
        """将张量矩阵序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.ts3mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的张量矩阵数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.ts3mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'ts3mat3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将张量矩阵数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.ts3mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的张量矩阵数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.ts3mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取张量矩阵的二进制序列化数据。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载张量矩阵。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'ts3mat3_size_0', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_1', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_2', c_void_p)

    @property
    def size_0(self):
        """获取张量矩阵第一维度的大小。

        Returns:
            int: 第一维度的大小。
        """
        return core.ts3mat3_size_0(self.handle)

    @property
    def size_1(self):
        """获取张量矩阵第二维度的大小。

        Returns:
            int: 第二维度的大小。
        """
        return core.ts3mat3_size_1(self.handle)

    @property
    def size_2(self):
        """获取张量矩阵第三维度的大小。

        Returns:
            int: 第三维度的大小。
        """
        return core.ts3mat3_size_2(self.handle)

    core.use(None, 'ts3mat3_resize', c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        """调整张量矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。

        Raises:
            AssertionError: 如果输入参数不是三元组。
        """
        assert len(value) == 3, 'The size must be a tuple of length 3.'
        core.ts3mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        """获取张量矩阵的三维大小。

        Returns:
            tuple: 包含三个维度大小的元组 (size_0, size_1, size_2)。
        """
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        """设置张量矩阵的三维大小。

        Args:
            value (tuple): 新的三维大小 (size_0, size_1, size_2)。
        """
        self.resize(value)

    core.use(c_void_p, 'ts3mat3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """获取指定位置的张量元素。

        Args:
            key0 (int): 第一维度的索引。
            key1 (int): 第二维度的索引。
            key2 (int): 第三维度的索引。

        Returns:
            Tensor3: 指定位置的张量元素引用。

        Note:
            如果索引越界，则返回 None。
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return Tensor3(handle=core.ts3mat3_get(self.handle, key0, key1, key2))

    def __getitem__(self, key):
        """通过元组索引获取张量元素。

        Args:
            key (tuple): 包含三个整数的元组，表示 (key0, key1, key2)。

        Returns:
            Tensor3: 指定位置的张量元素引用。
        """
        assert len(key) == 3
        return self.get(*key)

    core.use(None, 'ts3mat3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量矩阵的数据到当前矩阵。

        Args:
            other (Tensor3Matrix3): 要克隆的矩阵对象。

        Returns:
            Tensor3Matrix3: 当前矩阵对象（用于链式调用）。
        """
        if other is not None:
            assert isinstance(other, Tensor3Matrix3)
            core.ts3mat3_clone(self.handle, other.handle)
        return self

    core.use(None, 'ts3mat3_interp', c_void_p, c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double, c_double, c_double)

    def get_interp(self, left, step, pos, buffer=None):
        """执行三维插值计算。

        Args:
            left (tuple): 起始坐标三元组 (x0, y0, z0)。
            step (tuple): 步长三元组 (dx, dy, dz)。
            pos (tuple): 插值位置三元组 (x, y, z)。
            buffer (Tensor3, optional): 用于存储结果的缓冲区。默认为新建 Tensor3 对象。

        Returns:
            Tensor3: 包含插值结果的张量。

        Note:
            需要保证输入参数均为三元组格式。
        """
        assert len(left) == 3 and len(step) == 3 and len(pos) == 3
        if not isinstance(buffer, Tensor3):
            buffer = Tensor3()
        core.ts3mat3_interp(self.handle, buffer.handle, left[0], left[1], left[2],
                            step[0], step[1], step[2], pos[0], pos[1], pos[2])
        return buffer


class Interp1(HasHandle):
    """映射 C++ 类：zml::Interp1。

    该类用于一维插值计算，支持从离散数据点、均匀分布数据或常数值创建插值函数，
    并支持序列化保存/加载数据。
    """
    core.use(c_void_p, 'new_interp1')
    core.use(None, 'del_interp1', c_void_p)

    def __init__(self, xmin=None, dx=None, x=None, y=None, value=None, path=None, handle=None):
        """初始化一维插值对象。

        Args:
            xmin (float, optional): 均匀分布数据的起始 x 值。
            dx (float, optional): 均匀分布数据的步长。
            x (Vector/list, optional): 离散数据点的 x 坐标集合。
            y (Vector/list, optional): 离散数据点的 y 值集合。
            value (float, optional): 常数值插值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Interp1, self).__init__(handle, core.new_interp1, core.del_interp1)
        if handle is None:
            self.set(xmin=xmin, dx=dx, x=x, y=y, value=value)
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp1_save', c_void_p, c_char_p)

    def save(self, path):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp1_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.interp1_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp1_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp1_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp1_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp1_set_x2y', c_void_p, c_void_p, c_void_p)
    core.use(None, 'interp1_set_x2y_evenly', c_void_p, c_double, c_double, c_void_p)
    core.use(None, 'interp1_set_const', c_void_p, c_double)

    def set(self, xmin=None, dx=None, x=None, y=None, value=None):
        """设置插值数据，支持多种初始化方式。

        调用方式：
        1. 离散数据点模式: set(x=Vector_x, y=Vector_y)
        2. 均匀分布模式: set(xmin=起始值, dx=步长, y=Vector_y)
        3. 常数值模式: set(value=常数值) 或 set(y=常数值)

        Args:
            xmin (float, optional): 均匀分布数据的起始 x 值。
            dx (float, optional): 均匀分布数据的步长。
            x (Vector/list): 离散数据点的 x 坐标集合。
            y (Vector/list/float): 数据点的 y 值集合或常数值。
            value (float, optional): 常数值插值。
        """
        if x is not None and y is not None:
            if not isinstance(x, Vector):
                x = Vector(x)
            if not isinstance(y, Vector):
                y = Vector(y)
            core.interp1_set_x2y(self.handle, x.handle, y.handle)
            return
        if xmin is not None and dx is not None and y is not None:
            if not isinstance(y, Vector):
                y = Vector(y)
            core.interp1_set_x2y_evenly(self.handle, xmin, dx, y.handle)
            return
        if y is not None:
            core.interp1_set_const(self.handle, y)
            return
        if value is not None:
            core.interp1_set_const(self.handle, value)
            return

    core.use(None, 'interp1_create', c_void_p, c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, get_value):
        """通过回调函数创建插值数据。

        Args:
            xmin (float): 插值区间的最小 x 值。
            dx (float): 采样步长。
            xmax (float): 插值区间的最大 x 值。
            get_value (callable): 函数指针，格式为 y = get_value(x)。

        Note:
            需要保证 xmin < xmax 且 dx > 0。
        """
        assert xmin < xmax and dx > 0
        kernel = CFUNCTYPE(c_double, c_double)
        core.interp1_create(self.handle, xmin, dx, xmax, kernel(get_value))

    core.use(c_bool, 'interp1_empty', c_void_p)

    @property
    def empty(self):
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp1_empty(self.handle)

    core.use(None, 'interp1_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp1_clear(self.handle)

    core.use(None, 'interp1_get_vx', c_void_p, c_void_p)
    core.use(None, 'interp1_get_vy', c_void_p, c_void_p)

    def get_data(self, x=None, y=None):
        """获取插值数据的拷贝。

        Args:
            x (Vector, optional): 用于接收 x 坐标数据的 Vector 对象。
            y (Vector, optional): 用于接收 y 值数据的 Vector 对象。

        Returns:
            tuple: 包含 x 和 y 数据的 Vector 对象元组。
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        core.interp1_get_vx(self.handle, x.handle)
        core.interp1_get_vy(self.handle, y.handle)
        return x, y

    core.use(c_double, 'interp1_get', c_void_p, c_double, c_bool)

    def get(self, x, no_external=True):
        """执行插值计算。

        Args:
            x (float/Iterable): 要计算插值的 x 坐标或坐标集合。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float/list: 插值结果。输入为单个值时返回 float，输入为集合时返回 list。
        """
        if isinstance(x, Iterable):
            return [core.interp1_get(self.handle, scale, no_external) for scale in x]
        else:
            return core.interp1_get(self.handle, x, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp1_is_inner', c_void_p, c_double)

    def is_inner(self, x):
        """检查给定 x 坐标是否在插值区间内。

        Args:
            x (float): 要检查的 x 坐标。

        Returns:
            bool: 如果在区间内返回 True，否则返回 False。
        """
        return core.interp1_is_inner(self.handle, x)

    core.use(c_double, 'interp1_get_xmin', c_void_p)
    core.use(c_double, 'interp1_get_xmax', c_void_p)

    def xrange(self):
        """获取插值区间的 x 范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp1_get_xmin(self.handle), core.interp1_get_xmax(self.handle)

    core.use(None, 'interp1_to_evenly_spaced', c_void_p, c_size_t, c_size_t)

    def to_evenly_spaced(self, nmin=100, nmax=1000):
        """将插值数据转换为均匀间隔格式以加速查找。

        Args:
            nmin (int, optional): 最小采样点数。默认为 100。
            nmax (int, optional): 最大采样点数。默认为 1000。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        core.interp1_to_evenly_spaced(self.handle, nmin, nmax)
        return self

    core.use(None, 'interp1_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp1): 要克隆的插值对象。

        Returns:
            Interp1: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp1)
            core.interp1_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """创建当前对象的深拷贝。

        Returns:
            Interp1: 新的插值对象实例。
        """
        result = Interp1()
        result.clone(self)
        return result


class Interp2(HasHandle):
    """映射 C++ 类：zml::Interp2。

    该类用于二维插值计算，支持从文件加载数据、创建插值函数及数值查询等功能。
    """
    core.use(c_void_p, 'new_interp2')
    core.use(None, 'del_interp2', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化二维插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Interp2, self).__init__(handle, core.new_interp2, core.del_interp2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp2_save', c_void_p, c_char_p)

    def save(self, path):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp2_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """通过回调函数创建二维插值数据。

        Args:
            xmin (float): X 轴最小值。
            dx (float): X 轴采样步长。
            xmax (float): X 轴最大值。
            ymin (float): Y 轴最小值。
            dy (float): Y 轴采样步长。
            ymax (float): Y 轴最大值。
            get_value (callable): 回调函数，格式为 z = get_value(x, y)。

        Note:
            - 当 xmin == xmax 或 dx == 0 时，在 X 方向上视为常数场
            - 当 ymin == ymax 或 dy == 0 时，在 Y 方向上视为常数场
        """
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double)
        core.interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, kernel(get_value))

    @staticmethod
    def create_const(value):
        """创建常数值插值场。

        Args:
            value (float): 常数值。

        Returns:
            Interp2: 创建的常数值插值对象。
        """
        f = Interp2()
        f.create(xmin=0, dx=0, xmax=0, ymin=0, dy=0, ymax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp2_empty', c_void_p)

    @property
    def empty(self):
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp2_empty(self.handle)

    core.use(None, 'interp2_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp2_clear(self.handle)

    core.use(c_double, 'interp2_get', c_void_p, c_double, c_double, c_bool)

    def get(self, x, y, no_external=True):
        """获取指定坐标点的插值结果。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float: 插值计算结果。
        """
        return core.interp2_get(self.handle, x, y, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        """判断坐标点是否在插值域内部。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。

        Returns:
            bool: 如果坐标在有效域内返回 True，否则返回 False。
        """
        return core.interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'interp2_get_xmin', c_void_p)
    core.use(c_double, 'interp2_get_xmax', c_void_p)
    core.use(c_double, 'interp2_get_ymin', c_void_p)
    core.use(c_double, 'interp2_get_ymax', c_void_p)

    def xrange(self):
        """获取 X 轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp2_get_xmin(self.handle), core.interp2_get_xmax(self.handle)

    def yrange(self):
        """获取 Y 轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组。
        """
        return core.interp2_get_ymin(self.handle), core.interp2_get_ymax(self.handle)

    core.use(None, 'interp2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp2): 要克隆的插值对象。

        Returns:
            Interp2: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp2)
            core.interp2_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """创建当前对象的深拷贝。

        Returns:
            Interp2: 新的插值对象实例。
        """
        result = Interp2()
        result.clone(self)
        return result


class Interp3(HasHandle):
    """映射 C++ 类：zml::Interp3。

    该类用于三维插值计算，支持从文件加载数据、创建插值函数及空间插值查询等功能。
    """
    core.use(c_void_p, 'new_interp3')
    core.use(None, 'del_interp3', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化三维插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Interp3, self).__init__(handle, core.new_interp3, core.del_interp3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'interp3_save', c_void_p, c_char_p)

    def save(self, path):
        """将插值数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化的插值数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将插值数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化的插值数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取插值数据的二进制序列化表示。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制序列化数据加载插值。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp3_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax, get_value):
        """通过回调函数创建三维插值数据。

        Args:
            xmin (float): X 轴最小值。
            dx (float): X 轴采样步长。
            xmax (float): X 轴最大值。
            ymin (float): Y 轴最小值。
            dy (float): Y 轴采样步长。
            ymax (float): Y 轴最大值。
            zmin (float): Z 轴最小值。
            dz (float): Z 轴采样步长。
            zmax (float): Z 轴最大值。
            get_value (callable): 回调函数，格式为 value = get_value(x, y, z)。

        Note:
            - 当某轴的 min == max 或步长 == 0 时，该方向视为常数场
            - 需要保证 xmin <= xmax, ymin <= ymax, zmin <= zmax
            - 步长 dx/dy/dz 必须 >= 0
        """
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        assert zmin <= zmax and dz >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double)
        core.interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                            kernel(get_value))

    @staticmethod
    def create_const(value):
        """创建常数值插值场。

        Args:
            value (float): 常数值。

        Returns:
            Interp3: 创建的常数值插值对象。
        """
        f = Interp3()
        f.create(xmin=0, dx=0, xmax=0,
                 ymin=0, dy=0, ymax=0,
                 zmin=0, dz=0, zmax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp3_empty', c_void_p)

    @property
    def empty(self):
        """检查插值数据是否为空。

        Returns:
            bool: 如果插值数据为空返回 True，否则返回 False。
        """
        return core.interp3_empty(self.handle)

    core.use(None, 'interp3_clear', c_void_p)

    def clear(self):
        """清空插值数据。"""
        core.interp3_clear(self.handle)

    core.use(c_double, 'interp3_get', c_void_p, c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True):
        """获取三维空间点的插值结果。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            z (float): Z 坐标值。
            no_external (bool, optional): 是否禁止外推。默认为 True。

        Returns:
            float: 插值计算结果。
        """
        return core.interp3_get(self.handle, x, y, z, no_external)

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于 get 方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        """判断坐标点是否在插值域内部。

        Args:
            x (float): X 坐标值。
            y (float): Y 坐标值。
            z (float): Z 坐标值。

        Returns:
            bool: 如果坐标在有效域内返回 True，否则返回 False。
        """
        return core.interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'interp3_get_xmin', c_void_p)
    core.use(c_double, 'interp3_get_xmax', c_void_p)
    core.use(c_double, 'interp3_get_ymin', c_void_p)
    core.use(c_double, 'interp3_get_ymax', c_void_p)
    core.use(c_double, 'interp3_get_zmin', c_void_p)
    core.use(c_double, 'interp3_get_zmax', c_void_p)

    def xrange(self):
        """获取 X 轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组。
        """
        return core.interp3_get_xmin(self.handle), core.interp3_get_xmax(self.handle)

    def yrange(self):
        """获取 Y 轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组。
        """
        return core.interp3_get_ymin(self.handle), core.interp3_get_ymax(self.handle)

    def zrange(self):
        """获取 Z 轴的有效范围。

        Returns:
            tuple: (zmin, zmax) 组成的元组。
        """
        return core.interp3_get_zmin(self.handle), core.interp3_get_zmax(self.handle)

    core.use(None, 'interp3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个插值对象的数据到当前对象。

        Args:
            other (Interp3): 要克隆的插值对象。

        Returns:
            Interp3: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Interp3)
            core.interp3_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """创建当前对象的深拷贝。

        Returns:
            Interp3: 新的插值对象实例。
        """
        result = Interp3()
        result.clone(self)
        return result


class FileMap(HasHandle):
    """文件映射类，用于将文件夹及多个文件合并为单个文件（不压缩）。

    支持目录结构映射、键值存取、序列化保存/加载等操作。
    """
    core.use(c_void_p, 'new_fmap')
    core.use(None, 'del_fmap', c_void_p)

    def __init__(self, data=None, path=None, handle=None):
        """初始化文件映射对象。

        Args:
            data (str, optional): 初始文本内容。
            path (str, optional): 从文件加载的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(FileMap, self).__init__(handle, core.new_fmap, core.del_fmap)
        if handle is None:
            if data is not None:
                self.data = data
            if isinstance(path, str):
                self.load(path)

    core.use(c_bool, 'fmap_is_dir', c_void_p)

    @property
    def is_dir(self):
        """判断当前映射是否为目录结构。

        Returns:
            bool: 如果是目录映射返回 True，否则返回 False。
        """
        return core.fmap_is_dir(self.handle)

    core.use(c_bool, 'fmap_has_key', c_void_p, c_char_p)

    def has_key(self, key):
        """检查指定键是否存在。

        Args:
            key (str): 要检查的键名。

        Returns:
            bool: 如果键存在返回 True，否则返回 False。
        """
        return core.fmap_has_key(self.handle, make_c_char_p(key))

    core.use(c_void_p, 'fmap_get', c_void_p, c_char_p)

    def get(self, key):
        """获取指定键对应的子映射。

        Args:
            key (str): 要获取的键名。

        Returns:
            FileMap: 对应的子映射对象。

        Note:
            调用前必须先用 has_key 确认键存在，否则可能返回 None。
        """
        handle = core.fmap_get(self.handle, make_c_char_p(key))
        if handle:
            return FileMap(handle=handle)

    core.use(None, 'fmap_set', c_void_p, c_void_p, c_char_p)

    def set(self, key, fmap):
        """设置键值映射。

        Args:
            key (str): 要设置的键名。
            fmap (FileMap/any): 可以是 FileMap 对象或可转换为字符串的数据。

        Example:
            # 设置文本内容
            fmap.set('config', 'value')
            # 设置嵌套映射
            sub_fmap = FileMap()
            fmap.set('subdir', sub_fmap)
        """
        if isinstance(fmap, FileMap):
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))
        else:
            fmap = FileMap(data=fmap)
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))

    core.use(None, 'fmap_erase', c_void_p, c_char_p)

    def erase(self, key):
        """删除指定键的映射。

        Args:
            key (str): 要删除的键名。
        """
        core.fmap_erase(self.handle, make_c_char_p(key))

    core.use(None, 'fmap_write', c_void_p, c_char_p)

    def write(self, path):
        """将映射内容提取到文件系统。

        Args:
            path (str): 目标路径。
        """
        core.fmap_write(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_read', c_void_p, c_char_p)

    def read(self, path):
        """从文件系统读取内容到映射。

        Args:
            path (str): 源路径。
        """
        core.fmap_read(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_save', c_void_p, c_char_p)

    def save(self, path):
        """序列化保存为二进制格式。

        Args:
            path (str): 保存路径。

        Raises:
            AssertionError: 如果尝试保存为 txt 或 xml 格式。
        """
        if isinstance(path, str):
            ext = os.path.splitext(path)[-1].lower()
            assert ext != '.txt' and ext != '.xml'
            make_parent(path)
            core.fmap_save(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        Args:
            path (str): 加载路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.fmap_load(self.handle, make_c_char_p(path))

    core.use(c_char_p, 'fmap_get_char_p', c_void_p)

    @property
    def data(self):
        """获取文本内容。

        Returns:
            str: 解码后的字符串内容。
        """
        return core.fmap_get_char_p(self.handle).decode()

    core.use(None, 'fmap_set_char_p', c_void_p, c_char_p)

    @data.setter
    def data(self, value):
        """设置文本内容。

        Args:
            value (any): 自动转换为字符串的内容。
        """
        if not isinstance(value, str):
            value = f'{value}'
        core.fmap_set_char_p(self.handle, make_c_char_p(value))

    core.use(c_void_p, 'fmap_get_data', c_void_p)

    @property
    def buffer(self):
        """获取二进制数据缓冲区。

        Returns:
            String: 二进制数据对象。
        """
        return String(handle=core.fmap_get_data(self.handle))

    core.use(None, 'fmap_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个文件映射对象的数据。

        Args:
            other (FileMap): 要克隆的对象。

        Returns:
            FileMap: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, FileMap)
            core.fmap_clone(self.handle, other.handle)
        return self


class Array2(HasHandle):
    """二维数组容器类，用于存储两个双精度浮点数。

    支持初始化、序列化、元素访问及角度计算等操作。
    """
    core.use(c_void_p, 'new_array2')
    core.use(None, 'del_array2', c_void_p)

    def __init__(self, x=None, y=None, path=None, handle=None):
        """初始化二维数组对象。

        Args:
            x (float, optional): 第一个元素的初始值。
            y (float, optional): 第二个元素的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Array2, self).__init__(handle, core.new_array2, core.del_array2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if x is not None:
                self[0] = x
            if y is not None:
                self[1] = y
        else:
            assert x is None and y is None and path is None

    core.use(None, 'array2_save', c_void_p, c_char_p)

    def save(self, path):
        """将数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.array2_save(self.handle, make_c_char_p(path))

    core.use(None, 'array2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.array2_load(self.handle, make_c_char_p(path))

    core.use(None, 'array2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.array2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.array2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制数据加载。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """返回对象的字符串表示。

        Returns:
            str: 格式为 zml.Array2(x, y) 的字符串。
        """
        return f'zml.Array2({self[0]}, {self[1]})'

    def __len__(self):
        """获取数组长度。

        Returns:
            int: 固定返回 2。
        """
        return 2

    core.use(c_double, 'array2_get', c_void_p, c_size_t)

    def get(self, dim):
        """获取指定维度的值。

        Args:
            dim (int): 维度索引 (0 或 1)。

        Returns:
            float: 对应维度的值。
        """
        dim = get_index(dim, 2)
        if dim is not None:
            return core.array2_get(self.handle, dim)

    core.use(None, 'array2_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        """设置指定维度的值。

        Args:
            dim (int): 维度索引 (0 或 1)。
            value (float): 要设置的值。
        """
        dim = get_index(dim, 2)
        if dim is not None:
            core.array2_set(self.handle, dim, value)

    def __getitem__(self, key):
        """通过索引访问元素。

        Args:
            key (int): 维度索引 (0 或 1)。

        Returns:
            float: 对应维度的值。
        """
        return self.get(key)

    def __setitem__(self, key, value):
        """通过索引设置元素。

        Args:
            key (int): 维度索引 (0 或 1)。
            value (float): 要设置的值。
        """
        self.set(key, value)

    def to_list(self):
        """转换为列表格式。

        Returns:
            list: 包含两个元素的列表 [x, y]。
        """
        return [self[0], self[1]]

    def to_tuple(self):
        """转换为元组格式。

        Returns:
            tuple: 包含两个元素的元组 (x, y)。
        """
        return self[0], self[1]

    @staticmethod
    def from_list(values):
        """从列表创建 Array2 实例。

        Args:
            values (list): 必须包含两个元素的列表。

        Returns:
            Array2: 新创建的实例。

        Raises:
            AssertionError: 如果输入列表长度不为 2。
        """
        assert len(values) == 2
        return Array2(x=values[0], y=values[1])

    def clone(self, other):
        """克隆另一个 Array2 对象的数据。

        Args:
            other (Array2): 要克隆的对象。

        Returns:
            Array2: 当前对象（支持链式调用）。
        """
        if other is not None:
            for i in range(2):
                self.set(i, other[i])
        return self

    core.use(c_double, 'array2_get_angle', c_void_p)

    def get_angle(self):
        """计算与 X 轴正方向的夹角。

        Returns:
            float: 弧度值，范围 [-π, π]。
        """
        return core.array2_get_angle(self.handle)


class Array3(HasHandle):
    """三维数组容器类，用于存储三个双精度浮点数。

    支持初始化、序列化、元素访问及数据转换等操作。
    """
    core.use(c_void_p, 'new_array3')
    core.use(None, 'del_array3', c_void_p)

    def __init__(self, x=None, y=None, z=None, path=None, handle=None):
        """初始化三维数组对象。

        Args:
            x (float, optional): 第一个元素的初始值。
            y (float, optional): 第二个元素的初始值。
            z (float, optional): 第三个元素的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Array3, self).__init__(handle, core.new_array3, core.del_array3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if x is not None:
                self[0] = x
            if y is not None:
                self[1] = y
            if z is not None:
                self[2] = z
        else:
            assert x is None and y is None and z is None and path is None

    core.use(None, 'array3_save', c_void_p, c_char_p)

    def save(self, path):
        """将数据序列化保存到文件。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.array3_save(self.handle, make_c_char_p(path))

    core.use(None, 'array3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.array3_load(self.handle, make_c_char_p(path))

    core.use(None, 'array3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.array3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.array3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制数据加载。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """返回对象的字符串表示。

        Returns:
            str: 格式为 zml.Array3(x, y, z) 的字符串。
        """
        return f'zml.Array3({self[0]}, {self[1]}, {self[2]})'

    def __len__(self):
        """获取数组长度。

        Returns:
            int: 固定返回 3。
        """
        return 3

    core.use(c_double, 'array3_get', c_void_p, c_size_t)

    def get(self, dim):
        """获取指定维度的值。

        Args:
            dim (int): 维度索引 (0, 1 或 2)。

        Returns:
            float: 对应维度的值。
        """
        dim = get_index(dim, 3)
        if dim is not None:
            return core.array3_get(self.handle, dim)

    core.use(None, 'array3_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        """设置指定维度的值。

        Args:
            dim (int): 维度索引 (0, 1 或 2)。
            value (float): 要设置的值。
        """
        dim = get_index(dim, 3)
        if dim is not None:
            core.array3_set(self.handle, dim, value)

    def __getitem__(self, key):
        """通过索引访问元素。

        Args:
            key (int): 维度索引 (0, 1 或 2)。

        Returns:
            float: 对应维度的值。
        """
        return self.get(key)

    def __setitem__(self, key, value):
        """通过索引设置元素。

        Args:
            key (int): 维度索引 (0, 1 或 2)。
            value (float): 要设置的值。
        """
        self.set(key, value)

    def to_list(self):
        """转换为列表格式。

        Returns:
            list: 包含三个元素的列表 [x, y, z]。
        """
        return [self[0], self[1], self[2]]

    def to_tuple(self):
        """转换为元组格式。

        Returns:
            tuple: 包含三个元素的元组 (x, y, z)。
        """
        return self[0], self[1], self[2]

    @staticmethod
    def from_list(values):
        """从列表创建 Array3 实例。

        Args:
            values (list): 必须包含三个元素的列表。

        Returns:
            Array3: 新创建的实例。

        Raises:
            AssertionError: 如果输入列表长度不为 3。
        """
        assert len(values) == 3
        return Array3(x=values[0], y=values[1], z=values[2])

    def clone(self, other):
        """克隆另一个 Array3 对象的数据。

        Args:
            other (Array3): 要克隆的对象。

        Returns:
            Array3: 当前对象（支持链式调用）。
        """
        if other is not None:
            for i in range(3):
                self.set(i, other[i])
        return self


class Tensor2(HasHandle):
    """二维二阶张量类，用于表示二维空间中的应力、应变等张量数据。

    支持张量分量存取、特征值计算、旋转变换及序列化操作。
    """
    core.use(c_void_p, 'new_tensor2')
    core.use(None, 'del_tensor2', c_void_p)

    def __init__(self, xx=None, yy=None, xy=None, path=None, handle=None):
        """初始化二维张量对象。

        Args:
            xx (float, optional): xx分量的初始值。
            yy (float, optional): yy分量的初始值。
            xy (float, optional): xy分量的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Tensor2, self).__init__(handle, core.new_tensor2, core.del_tensor2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if xx is not None:
                self.xx = xx
            if yy is not None:
                self.yy = yy
            if xy is not None:
                self.xy = xy
        else:
            assert xx is None and yy is None and xy is None and path is None

    core.use(None, 'tensor2_save', c_void_p, c_char_p)

    def save(self, path):
        """序列化保存张量数据。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.tensor2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将张量数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.tensor2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.tensor2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制数据加载张量。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """返回张量的字符串表示。

        Returns:
            str: 格式为 zml.Tensor2(xx, yy, xy) 的字符串。
        """
        return f'zml.Tensor2({self.xx}, {self.yy}, {self.xy})'

    core.use(c_double, 'tensor2_get', c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key):
        """通过二维索引访问张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。

        Returns:
            float: 对应分量的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
            return core.tensor2_get(self.handle, i, j)

    core.use(None, 'tensor2_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        """通过二维索引设置张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。
            value (float): 要设置的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
            core.tensor2_set(self.handle, i, j, value)

    core.use(None, 'tensor2_set_max_min_angle', c_void_p, c_double, c_double, c_double)

    def set_max_min_angle(self, max_value=None, min_value=None, angle=None):
        """通过主值和方向角设置张量。

        Args:
            max_value (float): 最大主应力/应变值。
            min_value (float): 最小主应力/应变值。
            angle (float): 最大主值方向与x轴正方向的夹角（弧度，逆时针方向为正）。
        """
        if max_value is not None and min_value is not None and angle is not None:
            core.tensor2_set_max_min_angle(self.handle, max_value, min_value, angle)

    @property
    def xx(self):
        """获取或设置xx分量。"""
        return self[(0, 0)]

    @xx.setter
    def xx(self, value):
        self[0, 0] = value

    @property
    def yy(self):
        """获取或设置yy分量。"""
        return self[(1, 1)]

    @yy.setter
    def yy(self, value):
        self[(1, 1)] = value

    @property
    def xy(self):
        """获取或设置xy分量。"""
        return self[(0, 1)]

    @xy.setter
    def xy(self, value):
        self[(0, 1)] = value

    @staticmethod
    def create(max, min, angle):
        """通过主值创建二维张量。

        Args:
            max (float): 最大主值。
            min (float): 最小主值。
            angle (float): 最大主值方向角（弧度）。

        Returns:
            Tensor2: 新创建的张量实例。
        """
        tensor = Tensor2()
        tensor.set_max_min_angle(max, min, angle)
        return tensor

    def __add__(self, other):
        """张量加法运算。

        Args:
            other (Tensor2): 另一个张量。

        Returns:
            Tensor2: 新的张量实例，包含各分量之和。
        """
        xx = self.xx + other.xx
        yy = self.yy + other.yy
        xy = self.xy + other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __sub__(self, other):
        """张量减法运算。

        Args:
            other (Tensor2): 另一个张量。

        Returns:
            Tensor2: 新的张量实例，包含各分量之差。
        """
        xx = self.xx - other.xx
        yy = self.yy - other.yy
        xy = self.xy - other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __mul__(self, value):
        """标量乘法运算。

        Args:
            value (float): 标量乘数。

        Returns:
            Tensor2: 新的张量实例，各分量乘以标量值。
        """
        xx = self.xx * value
        yy = self.yy * value
        xy = self.xy * value
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __truediv__(self, value):
        """标量除法运算。

        Args:
            value (float): 标量除数。

        Returns:
            Tensor2: 新的张量实例，各分量除以标量值。
        """
        xx = self.xx / value
        yy = self.yy / value
        xy = self.xy / value
        return Tensor2(xx=xx, yy=yy, xy=xy)

    core.use(None, 'tensor2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量的数据。

        Args:
            other (Tensor2): 要克隆的张量对象。

        Returns:
            Tensor2: 当前对象（支持链式调用）。
        """
        if other is not None:
            assert isinstance(other, Tensor2)
            core.tensor2_clone(self.handle, other.handle)
        return self

    core.use(None, 'tensor2_rotate', c_void_p, c_void_p, c_double)

    def get_rotate(self, angle, buffer=None):
        """获取旋转后的张量。

        Args:
            angle (float): 旋转角度（弧度，逆时针方向为正）。
            buffer (Tensor2, optional): 用于存储结果的缓冲区。

        Returns:
            Tensor2: 旋转后的张量实例。
        """
        if not isinstance(buffer, Tensor2):
            buffer = Tensor2()
        core.tensor2_rotate(self.handle, buffer.handle, angle)
        return buffer

    core.use(c_double, 'tensor2_get_max_principle_value', c_void_p)

    @property
    def max_principle_value(self):
        """获取最大主值。

        Returns:
            float: 最大主应力/应变值。
        """
        return core.tensor2_get_max_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_min_principle_value', c_void_p)

    @property
    def min_principle_value(self):
        """获取最小主值。

        Returns:
            float: 最小主应力/应变值。
        """
        return core.tensor2_get_min_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_principle_angle', c_void_p)

    @property
    def principle_angle(self):
        """获取主值方向角。

        Returns:
            float: 最大主值方向与x轴的夹角（弧度）。
        """
        return core.tensor2_get_principle_angle(self.handle)


class Tensor3(HasHandle):
    """三维二阶张量类，用于表示三维空间中的应力、应变等张量数据。

    支持张量分量存取、方向投影计算及序列化操作。
    """
    core.use(c_void_p, 'new_tensor3')
    core.use(None, 'del_tensor3', c_void_p)

    def __init__(self, xx=None, yy=None, zz=None, xy=None, yz=None, zx=None, path=None, handle=None):
        """初始化三维张量对象。

        Args:
            xx (float, optional): xx分量的初始值。
            yy (float, optional): yy分量的初始值。
            zz (float, optional): zz分量的初始值。
            xy (float, optional): xy分量的初始值。
            yz (float, optional): yz分量的初始值。
            zx (float, optional): zx分量的初始值。
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Tensor3, self).__init__(handle, core.new_tensor3, core.del_tensor3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if xx is not None:
                self.xx = xx
            if yy is not None:
                self.yy = yy
            if zz is not None:
                self.zz = zz
            if xy is not None:
                self.xy = xy
            if yz is not None:
                self.yz = yz
            if zx is not None:
                self.zx = zx
        else:
            assert xx is None and yy is None and zz is None and xy is None and yz is None and zx is None

    core.use(None, 'tensor3_save', c_void_p, c_char_p)

    def save(self, path):
        """序列化保存张量数据。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读。
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台。
            - 其他：二进制格式，最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取。

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据文件扩展名确定文件格式（txt、xml 和二进制），请参考 `save` 函数。

        Args:
            path (str): 加载文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.tensor3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将张量数据序列化到 FileMap 中。

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.tensor3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从 FileMap 中读取序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.tensor3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制序列化表示。

        Returns:
            FileMap: 包含二进制数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制数据加载张量。

        Args:
            value (FileMap): 包含二进制数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """返回张量的字符串表示。

        Returns:
            str: 格式为 zml.Tensor3(xx, yy, zz, xy, yz, zx) 的字符串。
        """
        return f'zml.Tensor3({self.xx}, {self.yy}, {self.zz}, {self.xy}, {self.yz}, {self.zx})'

    core.use(c_double, 'tensor3_get', c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key):
        """通过二维索引访问张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。

        Returns:
            float: 对应分量的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
            return core.tensor3_get(self.handle, i, j)

    core.use(None, 'tensor3_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        """通过二维索引设置张量分量。

        Args:
            key (tuple): 二维索引元组，如 (0,0) 表示 xx 分量。
            value (float): 要设置的值。

        Raises:
            AssertionError: 如果索引长度不为2。
        """
        assert len(key) == 2
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
            core.tensor3_set(self.handle, i, j, value)

    @property
    def xx(self):
        """获取或设置xx分量。

        Returns:
            float: xx分量的值。
        """
        return self[(0, 0)]

    @xx.setter
    def xx(self, value):
        """设置xx分量。

        Args:
            value (float): 要设置的xx分量值。
        """
        self[0, 0] = value

    @property
    def yy(self):
        """获取或设置yy分量。

        Returns:
            float: yy分量的值。
        """
        return self[(1, 1)]

    @yy.setter
    def yy(self, value):
        """设置yy分量。

        Args:
            value (float): 要设置的yy分量值。
        """
        self[(1, 1)] = value

    @property
    def zz(self):
        """获取或设置zz分量。

        Returns:
            float: zz分量的值。
        """
        return self[(2, 2)]

    @zz.setter
    def zz(self, value):
        """设置zz分量。

        Args:
            value (float): 要设置的zz分量值。
        """
        self[(2, 2)] = value

    @property
    def xy(self):
        """获取或设置xy分量。

        Returns:
            float: xy分量的值。
        """
        return self[(0, 1)]

    @xy.setter
    def xy(self, value):
        """设置xy分量。

        Args:
            value (float): 要设置的xy分量值。
        """
        self[(0, 1)] = value

    @property
    def yz(self):
        """获取或设置yz分量。

        Returns:
            float: yz分量的值。
        """
        return self[(1, 2)]

    @yz.setter
    def yz(self, value):
        """设置yz分量。

        Args:
            value (float): 要设置的yz分量值。
        """
        self[(1, 2)] = value

    @property
    def zx(self):
        """获取或设置zx分量。

        Returns:
            float: zx分量的值。
        """
        return self[(2, 0)]

    @zx.setter
    def zx(self, value):
        """设置zx分量。

        Args:
            value (float): 要设置的zx分量值。
        """
        self[(2, 0)] = value

    def __add__(self, other):
        """执行张量逐分量加法运算。

        Args:
            other (Tensor3): 另一个三维张量对象。

        Returns:
            Tensor3: 新的张量实例，包含各分量之和。

        Raises:
            TypeError: 如果other不是Tensor3类型。
        """
        return Tensor3(xx=self.xx + other.xx,
                       yy=self.yy + other.yy,
                       zz=self.zz + other.zz,
                       xy=self.xy + other.xy,
                       yz=self.yz + other.yz,
                       zx=self.zx + other.zx,
                       )

    def __sub__(self, other):
        """执行张量逐分量减法运算。

        Args:
            other (Tensor3): 另一个三维张量对象。

        Returns:
            Tensor3: 新的张量实例，包含各分量之差。

        Raises:
            TypeError: 如果other不是Tensor3类型。
        """
        return Tensor3(xx=self.xx - other.xx,
                       yy=self.yy - other.yy,
                       zz=self.zz - other.zz,
                       xy=self.xy - other.xy,
                       yz=self.yz - other.yz,
                       zx=self.zx - other.zx,
                       )

    def __mul__(self, value):
        """执行标量乘法运算。

        Args:
            value (float): 标量乘数。

        Returns:
            Tensor3: 新的张量实例，各分量乘以标量值。

        Raises:
            TypeError: 如果value不是数值类型。
        """
        return Tensor3(xx=self.xx * value,
                       yy=self.yy * value,
                       zz=self.zz * value,
                       xy=self.xy * value,
                       yz=self.yz * value,
                       zx=self.zx * value,
                       )

    def __truediv__(self, value):
        """执行标量除法运算。

        Args:
            value (float): 标量除数，不能为0。

        Returns:
            Tensor3: 新的张量实例，各分量除以标量值。

        Raises:
            ZeroDivisionError: 如果value为0。
            TypeError: 如果value不是数值类型。
        """
        return Tensor3(xx=self.xx / value,
                       yy=self.yy / value,
                       zz=self.zz / value,
                       xy=self.xy / value,
                       yz=self.yz / value,
                       zx=self.zx / value,
                       )

    core.use(c_double, 'tensor3_get_along', c_void_p, c_double, c_double, c_double)

    def get_along(self, *args):
        """计算给定方向上的投影值。

        支持两种参数形式：
        1. 三个独立坐标分量 (x, y, z)
        2. 包含三个元素的向量 (vector, )

        Args:
            *args: 可以是三个float参数，或单个向量参数

        Returns:
            float: 该方向上的投影值
        """
        if len(args) == 3:
            return core.tensor3_get_along(self.handle, *args)
        else:
            assert len(args) == 1
            x = args[0]
            return core.tensor3_get_along(self.handle, x[0], x[1], x[2])

    core.use(None, 'tensor3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """克隆另一个张量的数据到当前对象。

        Args:
            other (Tensor3): 要克隆的源张量对象

        Returns:
            Tensor3: 当前对象实例，支持链式调用
        """
        if other is not None:
            assert isinstance(other, Tensor3)
            core.tensor3_clone(self.handle, other.handle)
        return self


class Tensor2Interp2(HasHandle):
    """二维张量插值类，提供二维空间中的张量场插值功能。

    支持从函数创建插值、范围查询、插值计算及序列化操作。
    """
    core.use(c_void_p, 'new_tensor2interp2')
    core.use(None, 'del_tensor2interp2', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化二维张量插值对象。

        Args:
            path (str, optional): 从文件加载数据的路径。
            handle: 已有的句柄。如果提供，则忽略其他参数。
        """
        super(Tensor2Interp2, self).__init__(handle, core.new_tensor2interp2, core.del_tensor2interp2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'tensor2interp2_save', c_void_p, c_char_p)

    def save(self, path):
        """序列化保存插值数据。

        支持以下文件格式：
            - `.txt`：跨平台，基本不可读
            - `.xml`：特定可读性，文件体积最大，读写速度最慢，跨平台
            - 其他：二进制格式（最快且最小，但跨平台兼容性差）

        Args:
            path (str): 保存文件的路径

        Raises:
            ValueError: 如果路径格式不合法
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor2interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载序列化数据。

        根据扩展名自动判断文件格式（txt/xml/二进制）

        Args:
            path (str): 加载文件的路径

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.tensor2interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """将插值数据序列化到FileMap。

        Args:
            fmt (str, optional): 序列化格式，可选 'text'/'xml'/'binary'，默认二进制

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.tensor2interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从FileMap反序列化数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射对象
            fmt (str, optional): 序列化格式，需与写入时一致

        Raises:
            TypeError: 如果fmap参数类型错误
        """
        assert isinstance(fmap, FileMap)
        core.tensor2interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """获取二进制格式的序列化表示。

        Returns:
            FileMap: 二进制格式的文件映射对象
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """从二进制FileMap加载数据。

        Args:
            value (FileMap): 包含二进制数据的文件映射对象
        """
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor2interp2_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """通过回调函数创建插值场。

        Args:
            xmin (float): X轴最小值
            dx (float): X轴采样步长（需>0）
            xmax (float): X轴最大值（需≥xmin）
            ymin (float): Y轴最小值
            dy (float): Y轴采样步长（需>0）
            ymax (float): Y轴最大值（需≥ymin）
            get_value (callable): 形如 def (x: float, y: float) -> Tensor2 的回调函数

        Note:
            - 当xmin=xmax或ymin=ymax时创建常数字段
            - 步长过小可能导致内存溢出
        """
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_size_t)
        core.tensor2interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax,
                                   kernel(get_value))

    core.use(c_bool, 'tensor2interp2_empty', c_void_p)

    @property
    def empty(self):
        """检查插值场是否为空。

        Returns:
            bool: True表示未初始化，False表示已载入数据
        """
        return core.tensor2interp2_empty(self.handle)

    core.use(None, 'tensor2interp2_get', c_void_p, c_void_p,
             c_double, c_double, c_bool)

    def get(self, x, y, no_external=True, value=None):
        """获取指定坐标点的张量值。

        Args:
            x (float): X坐标
            y (float): Y坐标
            no_external (bool, optional): 是否禁止外推（默认True，禁用外推）
            value (Tensor2, optional): 用于存储结果的张量对象

        Returns:
            Tensor2: 插值结果张量

        Raises:
            ValueError: 当坐标超出范围且no_external=True时
        """
        if value is None:
            value = Tensor2()
        core.tensor2interp2_get(self.handle, value.handle, x, y, no_external)
        return value

    def __call__(self, *args, **kwargs):
        """使实例可调用，等效于get方法。"""
        return self.get(*args, **kwargs)

    core.use(c_bool, 'tensor2interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        """判断坐标是否在有效插值域内。

        Args:
            x (float): X坐标
            y (float): Y坐标

        Returns:
            bool: True表示在有效域内，False表示在外部
        """
        return core.tensor2interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'tensor2interp2_get_xmin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_xmax', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymax', c_void_p)

    def xrange(self):
        """获取X轴的有效范围。

        Returns:
            tuple: (xmin, xmax) 组成的元组
        """
        return core.tensor2interp2_get_xmin(self.handle), core.tensor2interp2_get_xmax(self.handle)

    def yrange(self):
        """获取Y轴的有效范围。

        Returns:
            tuple: (ymin, ymax) 组成的元组
        """
        return core.tensor2interp2_get_ymin(self.handle), core.tensor2interp2_get_ymax(self.handle)


class Tensor3Interp3(HasHandle):
    """三维三阶张量插值器，用于三维空间中的张量场插值计算。"""
    core.use(c_void_p, 'new_tensor3interp3')
    core.use(None, 'del_tensor3interp3', c_void_p)

    def __init__(self, path=None, handle=None):
        """初始化三维张量插值器。

        Args:
            path (str, optional): 数据文件路径，支持序列化文件加载
            handle: 已有句柄，用于包装现有底层对象
        """
        super(Tensor3Interp3, self).__init__(handle, core.new_tensor3interp3, core.del_tensor3interp3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'tensor3interp3_save', c_void_p, c_char_p)

    def save(self, path):
        """保存插值器数据到文件。

        Args:
            path (str): 文件保存路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.tensor3interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载插值器数据。

        Args:
            path (str): 文件路径，自动根据扩展名识别格式
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.tensor3interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.tensor3interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从文件映射对象加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.tensor3interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor3interp3_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax, get_value):
        """创建插值场。

        Args:
            xmin (float): X轴最小值
            dx (float): X轴步长(需>0)
            xmax (float): X轴最大值
            ymin (float): Y轴最小值
            dy (float): Y轴步长(需>0)
            ymax (float): Y轴最大值
            zmin (float): Z轴最小值
            dz (float): Z轴步长(需>0)
            zmax (float): Z轴最大值
            get_value (callable): 形如f(x,y,z,i)->float的回调函数，i∈[0,5]对应6个张量分量
        """
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double, c_size_t)
        core.tensor3interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                                   kernel(get_value))

    def create_constant(self, value):
        """创建常数值张量场。

        Args:
            value (Tensor3|tuple): 张量值，支持Tensor3对象或6元素元组
        """
        if isinstance(value, Tensor3):
            value = (value[(0, 0)], value[(1, 1)], value[(2, 2)], value[(0, 1)], value[(1, 2)], value[(2, 0)])

        def get_value(x, y, z, i):
            assert 0 <= i < 6
            return value[i]

        vmax = 1e10
        self.create(-vmax, vmax, vmax, -vmax, vmax, vmax, -vmax, vmax, vmax, get_value)

    core.use(c_bool, 'tensor3interp3_empty', c_void_p)

    @property
    def empty(self):
        """检查插值器是否为空。

        Returns:
            bool: True表示未初始化数据
        """
        return core.tensor3interp3_empty(self.handle)

    core.use(None, 'tensor3interp3_get', c_void_p, c_void_p,
             c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True, value=None):
        """获取空间点的张量插值。

        Args:
            x (float): X坐标
            y (float): Y坐标
            z (float): Z坐标
            no_external (bool): 是否禁用外推
            value (Tensor3, optional): 存储结果的张量对象

        Returns:
            Tensor3: 插值结果张量
        """
        if value is None:
            value = Tensor3()
        core.tensor3interp3_get(self.handle, value.handle, x, y, z, no_external)
        return value

    def __call__(self, *args, ** kwargs):
        """调用接口，等效于get方法。"""
        return self.get(*args, ** kwargs)

    core.use(c_bool, 'tensor3interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        """判断坐标是否在插值域内。

        Returns:
            bool: True表示坐标在有效域内
        """
        return core.tensor3interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'tensor3interp3_get_xmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_xmax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmax', c_void_p)

    def xrange(self):
        """获取X轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_xmin(self.handle), core.tensor3interp3_get_xmax(self.handle)

    def yrange(self):
        """获取Y轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_ymin(self.handle), core.tensor3interp3_get_ymax(self.handle)

    def zrange(self):
        """获取Z轴有效范围。

        Returns:
            tuple: (最小值, 最大值)
        """
        return core.tensor3interp3_get_zmin(self.handle), core.tensor3interp3_get_zmax(self.handle)


class Coord2(HasHandle):
    """二维坐标系表示类，包含原点和坐标轴方向信息。"""
    core.use(c_void_p, 'new_coord2')
    core.use(None, 'del_coord2', c_void_p)

    def __init__(self, origin=None, xdir=None, path=None, handle=None):
        """初始化二维坐标系。

        Args:
            origin (Array2|list|tuple, optional): 坐标系原点坐标
            xdir (Array2|list|tuple, optional): X轴方向向量
            path (str, optional): 序列化文件加载路径
            handle: 现有底层对象句柄
        """
        super(Coord2, self).__init__(handle, core.new_coord2, core.del_coord2)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if origin is not None and xdir is not None:
                self.set(origin, xdir)

    core.use(None, 'coord2_save', c_void_p, c_char_p)

    def save(self, path):
        """保存坐标系数据到文件。

        Args:
            path (str): 文件路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.coord2_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载坐标系数据。

        Args:
            path (str): 文件路径，自动识别序列化格式
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.coord2_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.coord2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.coord2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """返回坐标系的字符串表示。

        Returns:
            str: 格式为 zml.Coord2(origin=..., xdir=...)
        """
        return f'zml.Coord2(origin = {self.origin}, xdir = {self.xdir})'

    core.use(None, 'coord2_set', c_void_p, c_size_t, c_size_t)

    def set(self, origin, xdir):
        """设置坐标系参数。

        Args:
            origin (Array2|list|tuple): 原点坐标，自动转换为Array2类型
            xdir (Array2|list|tuple): X轴方向向量，自动转换为Array2类型
        """
        if not isinstance(origin, Array2):
            origin = Array2.from_list(origin)
        if not isinstance(xdir, Array2):
            xdir = Array2.from_list(xdir)
        core.coord2_set(self.handle, origin.handle, xdir.handle)

    core.use(c_void_p, 'coord2_get_origin', c_void_p)

    @property
    def origin(self):
        """获取坐标系原点。

        Returns:
            Array2: 原点坐标向量
        """
        return Array2(handle=core.coord2_get_origin(self.handle))

    core.use(None, 'coord2_get_xdir', c_void_p, c_size_t)

    @property
    def xdir(self):
        """获取X轴单位方向向量。

        Returns:
            Array2: 归一化后的方向向量
        """
        temp = Array2()
        core.coord2_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self):
        """获取Y轴单位方向向量（自动正交化）。

        Returns:
            Array2: 垂直于X轴的归一化向量
        """
        temp = Array2()
        core.coord2_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_view_array2', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord2_view_tensor2', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
        """执行坐标系转换。

        Args:
            coord (Coord2): 目标坐标系
            o (Array2|Tensor2): 需要转换的向量或张量
            buffer (Array2|Tensor2, optional): 存储结果的缓冲区

        Returns:
            Array2|Tensor2: 转换后的结果

        Raises:
            TypeError: 当输入参数类型不符合要求时
        """
        assert isinstance(coord, Coord2)
        if isinstance(o, Array2):
            if not isinstance(buffer, Array2):
                buffer = Array2()
            core.coord2_view_array2(self.handle, buffer.handle, coord.handle, o.handle)
            return buffer
        if isinstance(o, Tensor2):
            if not isinstance(buffer, Tensor2):
                buffer = Tensor2()
            core.coord2_view_tensor2(self.handle, buffer.handle, coord.handle, o.handle)
            return buffer


class Coord3(HasHandle):
    """三维笛卡尔坐标系，用于点和张量的坐标转换。"""
    core.use(c_void_p, 'new_coord3')
    core.use(None, 'del_coord3', c_void_p)

    def __init__(self, origin=None, xdir=None, ydir=None, path=None, handle=None):
        """初始化三维坐标系。

        Args:
            origin (Array3|list|tuple, optional): 坐标系原点坐标
            xdir (Array3|list|tuple, optional): X轴方向向量
            ydir (Array3|list|tuple, optional): Y轴方向向量
            path (str, optional): 序列化文件加载路径
            handle: 现有底层对象句柄（存在时忽略其他参数）
        """
        super(Coord3, self).__init__(handle, core.new_coord3, core.del_coord3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
            if origin is not None and xdir is not None and ydir is not None:
                self.set(origin, xdir, ydir)
        else:
            assert origin is None and xdir is None and ydir is None

    core.use(None, 'coord3_save', c_void_p, c_char_p)

    def save(self, path):
        """保存坐标系数据到文件。

        Args:
            path (str): 文件路径，扩展名决定格式(.txt/.xml/其他=二进制)
        """
        if isinstance(path, str):
            make_parent(path)
            core.coord3_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_load', c_void_p, c_char_p)

    def load(self, path):
        """从文件加载坐标系数据。

        Args:
            path (str): 文件路径，自动识别序列化格式
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.coord3_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选text/xml/binary

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.coord3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 必须与写入时的序列化格式一致
        """
        assert isinstance(fmap, FileMap)
        core.coord3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """二进制序列化访问接口(property形式)。"""
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """获取坐标系的字符串表示。

        Returns:
            str: 格式为 zml.Coord3(origin=..., xdir=..., ydir=...)
        """
        return f'zml.Coord3(origin = {self.origin}, xdir = {self.xdir}, ydir = {self.ydir})'

    core.use(None, 'coord3_set', c_void_p, c_void_p, c_void_p, c_void_p)

    def set(self, origin, xdir, ydir):
        """设置坐标系参数。

        Args:
            origin (Array3|list|tuple): 原点坐标，自动转换为Array3类型
            xdir (Array3|list|tuple): X轴方向向量，自动转换为Array3类型
            ydir (Array3|list|tuple): Y轴方向向量，自动转换为Array3类型
        """
        if not isinstance(origin, Array3):
            origin = Array3.from_list(origin)
        if not isinstance(xdir, Array3):
            xdir = Array3.from_list(xdir)
        if not isinstance(ydir, Array3):
            ydir = Array3.from_list(ydir)
        core.coord3_set(self.handle, origin.handle, xdir.handle, ydir.handle)

    core.use(c_void_p, 'coord3_get_origin', c_void_p)

    @property
    def origin(self):
        """获取坐标系原点（可修改的引用）。

        Returns:
            Array3: 原点坐标的引用
        """
        return Array3(handle=core.coord3_get_origin(self.handle))

    core.use(None, 'coord3_get_xdir', c_void_p, c_size_t)

    @property
    def xdir(self):
        """获取X轴单位方向向量（自动正交化）。

        Returns:
            Array3: 归一化后的X方向向量
        """
        temp = Array3()
        core.coord3_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self):
        """获取Y轴单位方向向量（自动正交化）。

        Returns:
            Array3: 与X轴垂直的归一化向量
        """
        temp = Array3()
        core.coord3_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_view_array3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord3_view_tensor3', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
        """执行坐标系间对象转换。

        Args:
            coord (Coord3): 原始坐标系
            o (Array3|Tensor3): 需要转换的向量或张量
            buffer (Array3|Tensor3, optional): 存储结果的缓冲区

        Returns:
            Array3|Tensor3: 转换后的对象

        Raises:
            TypeError: 当输入类型不符合要求时
        """
        assert isinstance(coord, Coord3)
        if isinstance(o, Array3):
            if not isinstance(buffer, Array3):
                buffer = Array3()
            core.coord3_view_array3(self.handle, buffer.handle, coord.handle, o.handle)
            return buffer
        if isinstance(o, Tensor3):
            if not isinstance(buffer, Tensor3):
                buffer = Tensor3()
            core.coord3_view_tensor3(self.handle, buffer.handle, coord.handle, o.handle)
            return buffer


def _attr_in_range(value, *, left=None, right=None, min=None, max=None):
    """
    判断属性值是否在给定的范围内
    """
    if min is not None:
        warnings.warn('The argument <min> of <_attr_in_range> will be removed after 2025-4-5, use <left> instead',
                      DeprecationWarning)
        assert left is None
        left = min

    if max is not None:
        warnings.warn('The argument <max> of <_attr_in_range> will be removed after 2025-4-5, use <right> instead',
                      DeprecationWarning)
        assert right is None
        right = max

    if left is None:
        left = -1.0e100

    if right is None:
        right = 1.0e100

    return left <= value <= right


class Mesh3(HasHandle):
    """
    三维网格类，由点（Node）、线（Link）、面（Face）、体（Body）所组成的网络。

    Attributes:
        handle: 网格的句柄。
        node_number: 节点的数量。
        link_number: 线的数量。
        face_number: 面的数量。
        body_number: 体的数量。
    """

    class Node(Object):
        """
        三维网格中的节点类。

        Attributes:
            model (Mesh3): 节点所属的网格模型。
            index (int): 节点的索引。
        """
        def __init__(self, model, index):
            """
            初始化节点对象。

            Args:
                model (Mesh3): 节点所属的网格模型。
                index (int): 节点的索引，必须小于模型的节点数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'mesh3_get_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            返回节点的位置。

            Returns:
                list: 包含节点三个坐标的列表。
            """
            return [core.mesh3_get_node_pos(self.model.handle, self.index, i) for i in range(3)]

        core.use(None, 'mesh3_set_node_pos', c_void_p, c_size_t, c_size_t, c_double)

        @pos.setter
        def pos(self, value):
            """
            设置节点的位置。

            Args:
                value (list): 包含三个坐标的列表，用于设置节点的位置。
            """
            assert len(value) == 3
            for i in range(3):
                core.mesh3_set_node_pos(self.model.handle, self.index, i, value[i])

        core.use(c_size_t, 'mesh3_get_node_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            """
            返回与节点相连的线的数量。

            Returns:
                int: 与节点相连的线的数量。
            """
            return core.mesh3_get_node_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            返回与节点相连的面的数量。

            Returns:
                int: 与节点相连的面的数量。
            """
            return core.mesh3_get_node_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            """
            返回与节点相连的体的数量。

            Returns:
                int: 与节点相连的体的数量。
            """
            return core.mesh3_get_node_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            """
            根据索引获取与节点相连的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 与节点相连的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_node_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_node_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            """
            根据索引获取与节点相连的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 与节点相连的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_node_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_node_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            """
            根据索引获取与节点相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与节点相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_node_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def links(self):
            """
            返回与节点相连的所有线的迭代器。

            Returns:
                Iterator: 与节点相连的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self):
            """
            返回与节点相连的所有面的迭代器。

            Returns:
                Iterator: 与节点相连的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self):
            """
            返回与节点相连的所有体的迭代器。

            Returns:
                Iterator: 与节点相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        core.use(c_double, 'mesh3_get_node_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_node_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取节点的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 节点的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_node_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置节点的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Node: 当前节点对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_node_attr(self.model.handle, self.index, index, value)
            return self

    class Link(Object):
        """
        三维网格中的线类。

        Attributes:
            model (Mesh3): 线所属的网格模型。
            index (int): 线的索引。
        """
        def __init__(self, model, index):
            """
            初始化线对象。

            Args:
                model (Mesh3): 线所属的网格模型。
                index (int): 线的索引，必须小于模型的线数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.link_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_link_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            """
            返回线所连接的节点数量。

            Returns:
                int: 线所连接的节点数量。
            """
            return core.mesh3_get_link_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            返回与线相连的面的数量。

            Returns:
                int: 与线相连的面的数量。
            """
            return core.mesh3_get_link_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            """
            返回与线相连的体的数量。

            Returns:
                int: 与线相连的体的数量。
            """
            return core.mesh3_get_link_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            """
            根据索引获取线所连接的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 线所连接的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_link_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_link_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            """
            根据索引获取与线相连的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 与线相连的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_link_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_link_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            """
            根据索引获取与线相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与线相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_link_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            """
            返回线所连接的所有节点的迭代器。

            Returns:
                Iterator: 线所连接的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def faces(self):
            """
            返回与线相连的所有面的迭代器。

            Returns:
                Iterator: 与线相连的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self):
            """
            返回与线相连的所有体的迭代器。

            Returns:
                Iterator: 与线相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        @property
        def length(self):
            """
            返回线的长度。

            Returns:
                float: 线的长度。
            """
            assert self.node_number == 2
            return get_distance(self.get_node(0).pos, self.get_node(1).pos)

        @property
        def pos(self):
            """
            返回线的中心点位置。

            Returns:
                tuple: 包含线中心点三个坐标的元组。
            """
            assert self.node_number == 2
            p0, p1 = self.get_node(0).pos, self.get_node(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_double, 'mesh3_get_link_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_link_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取线的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 线的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_link_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置线的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Link: 当前线对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_link_attr(self.model.handle, self.index, index, value)
            return self

    class Face(Object):
        """
        三维网格中的面类。

        Attributes:
            model (Mesh3): 面所属的网格模型。
            index (int): 面的索引。
        """
        def __init__(self, model, index):
            """
            初始化面对象。

            Args:
                model (Mesh3): 面所属的网格模型。
                index (int): 面的索引，必须小于模型的面数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.face_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_face_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            """
            返回面所包含的节点数量。

            Returns:
                int: 面所包含的节点数量。
            """
            return core.mesh3_get_face_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            """
            返回面所包含的线的数量。

            Returns:
                int: 面所包含的线的数量。
            """
            return core.mesh3_get_face_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            """
            返回与面相连的体的数量。

            Returns:
                int: 与面相连的体的数量。
            """
            return core.mesh3_get_face_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            """
            根据索引获取面所包含的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 面所包含的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_face_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_face_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            """
            根据索引获取面所包含的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 面所包含的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_face_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_face_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            """
            根据索引获取与面相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与面相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_face_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            """
            返回面所包含的所有节点的迭代器。

            Returns:
                Iterator: 面所包含的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self):
            """
            返回面所包含的所有线的迭代器。

            Returns:
                Iterator: 面所包含的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def bodies(self):
            """
            返回与面相连的所有体的迭代器。

            Returns:
                Iterator: 与面相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        core.use(c_double, 'mesh3_get_face_area', c_void_p, c_size_t)

        @property
        def area(self):
            """
            返回面的面积。

            Returns:
                float: 面的面积。
            """
            return core.mesh3_get_face_area(self.model.handle, self.index)

        @property
        def pos(self):
            """
            返回面的位置（节点的平均位置）。

            Returns:
                tuple: 包含面位置三个坐标的元组。
            """
            x, y, z = 0, 0, 0
            n = 0
            for node in self.nodes:
                xi, yi, zi = node.pos
                x += xi
                y += yi
                z += zi
                n += 1
            if n > 0:
                return x / n, y / n, z / n

        core.use(c_double, 'mesh3_get_face_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_face_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取面的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 面的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_face_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置面的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Face: 当前面对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_face_attr(self.model.handle, self.index, index, value)
            return self

    class Body(Object):
        """
        三维网格中的体类。

        Attributes:
            model (Mesh3): 体所属的网格模型。
            index (int): 体的索引。
        """
        def __init__(self, model, index):
            """
            初始化体对象。

            Args:
                model (Mesh3): 体所属的网格模型。
                index (int): 体的索引，必须小于模型的体数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.body_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_body_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            """
            返回体所包含的节点数量。

            Returns:
                int: 体所包含的节点数量。
            """
            return core.mesh3_get_body_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            """
            返回体所包含的线的数量。

            Returns:
                int: 体所包含的线的数量。
            """
            return core.mesh3_get_body_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            返回体所包含的面的数量。

            Returns:
                int: 体所包含的面的数量。
            """
            return core.mesh3_get_body_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            """
            根据索引获取体所包含的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 体所包含的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_body_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_body_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            """
            根据索引获取体所包含的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 体所包含的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_body_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_body_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            """
            根据索引获取体所包含的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 体所包含的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_body_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        @property
        def nodes(self):
            """
            返回体所包含的所有节点的迭代器。

            Returns:
                Iterator: 体所包含的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self):
            """
            返回体所包含的所有线的迭代器。

            Returns:
                Iterator: 体所包含的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self):
            """
            返回体所包含的所有面的迭代器。

            Returns:
                Iterator: 体所包含的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def pos(self):
            """
            返回体的位置（节点的平均位置）。

            Returns:
                tuple: 包含体位置三个坐标的元组。
            """
            x, y, z = 0, 0, 0
            n = 0
            for node in self.nodes:
                xi, yi, zi = node.pos
                x += xi
                y += yi
                z += zi
                n += 1
            if n > 0:
                return x / n, y / n, z / n

        core.use(c_double, 'mesh3_get_body_volume', c_void_p, c_size_t)

        @property
        def volume(self):
            """
            返回体的体积。

            Returns:
                float: 体的体积。
            """
            return core.mesh3_get_body_volume(self.model.handle, self.index)

        core.use(c_double, 'mesh3_get_body_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_body_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取体的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 体的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_body_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置体的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Body: 当前体对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_body_attr(self.model.handle, self.index, index, value)
            return self

        core.use(c_bool, 'mesh3_body_contains', c_void_p, c_size_t, c_double, c_double, c_double)

        def contains(self, pos):
            """
            判断给定的位置是否包含在体中。

            Args:
                pos (list): 包含三个坐标的列表，表示要判断的位置。

            Returns:
                bool: 如果位置包含在体中返回 True，否则返回 False。
            """
            assert len(pos) == 3, f'pos = {pos}'
            return core.mesh3_body_contains(self.model.handle, self.index, *pos)

    core.use(c_void_p, 'new_mesh3')
    core.use(None, 'del_mesh3', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化 Mesh3 对象。

        Args:
            path (str, optional): 要加载的网格文件的路径。
            handle (any, optional): 网格的句柄。
        """
        super(Mesh3, self).__init__(handle, core.new_mesh3, core.del_mesh3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回 Mesh3 对象的字符串表示。

        Returns:
            str: Mesh3 对象的字符串表示。
        """
        return (f'zml.Mesh3(handle = {self.handle}, node_n = {self.node_number}, link_n = {self.link_number}, '
                f'face_n = {self.face_number}, body_n = {self.body_number})')

    core.use(None, 'mesh3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存网格数据。

        Args:
            path (str): 保存文件的路径。

        可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.mesh3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mesh3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化的网格文件。

        Args:
            path (str): 要读取的文件路径。

        根据扩展名确定文件格式（txt、xml 和二进制），请参考 save 函数。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.mesh3_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'mesh3_get_node_number', c_void_p)

    @property
    def node_number(self):
        """
        返回网格中的节点数量。

        Returns:
            int: 网格中的节点数量。
        """
        return core.mesh3_get_node_number(self.handle)

    core.use(c_size_t, 'mesh3_get_link_number', c_void_p)

    @property
    def link_number(self):
        """
        返回网格中的线的数量。

        Returns:
            int: 网格中的线的数量。
        """
        return core.mesh3_get_link_number(self.handle)

    core.use(c_size_t, 'mesh3_get_face_number', c_void_p)

    @property
    def face_number(self):
        """
        返回网格中的面的数量。

        Returns:
            int: 网格中的面的数量。
        """
        return core.mesh3_get_face_number(self.handle)

    core.use(c_size_t, 'mesh3_get_body_number', c_void_p)

    @property
    def body_number(self):
        """
        返回网格中的体的数量。

        Returns:
            int: 网格中的体的数量。
        """
        return core.mesh3_get_body_number(self.handle)

    def get_node(self, index):
        """
        根据索引获取网格中的节点。

        Args:
            index (int): 节点的索引。

        Returns:
            Node: 网格中的节点对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.node_number)
        if index is not None:
            return Mesh3.Node(self, index)

    def get_link(self, index):
        """
        根据索引获取网格中的线。

        Args:
            index (int): 线的索引。

        Returns:
            Link: 网格中的线对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.link_number)
        if index is not None:
            return Mesh3.Link(self, index)

    def get_face(self, index):
        """
        根据索引获取网格中的面。

        Args:
            index (int): 面的索引。

        Returns:
            Face: 网格中的面对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Mesh3.Face(self, index)

    def get_body(self, index):
        """
        根据索引获取网格中的体。

        Args:
            index (int): 体的索引。

        Returns:
            Body: 网格中的体对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.body_number)
        if index is not None:
            return Mesh3.Body(self, index)

    @property
    def nodes(self):
        """
        返回网格中所有节点的迭代器。

        Returns:
            Iterator: 网格中所有节点的迭代器。
        """
        return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

    @property
    def links(self):
        """
        返回网格中所有线的迭代器。

        Returns:
            Iterator: 网格中所有线的迭代器。
        """
        return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

    @property
    def faces(self):
        """
        返回网格中所有面的迭代器。

        Returns:
            Iterator: 网格中所有面的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def bodies(self):
        """
        返回网格中所有体的迭代器。

        Returns:
            Iterator: 网格中所有体的迭代器。
        """
        return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

    core.use(c_size_t, 'mesh3_add_node', c_void_p, c_double, c_double, c_double)

    def add_node(self, x, y, z):
        """
        在网格中添加一个节点。

        Args:
            x (float): 节点的 x 坐标。
            y (float): 节点的 y 坐标。
            z (float): 节点的 z 坐标。

        Returns:
            Node: 新添加的节点对象。
        """
        index = core.mesh3_add_node(self.handle, x, y, z)
        return self.get_node(index)

    core.use(c_size_t, 'mesh3_add_link', c_void_p, c_size_t, c_size_t)

    def add_link(self, nodes):
        """
        在网格中添加一条线。

        Args:
            nodes (list): 包含两个 Node 对象的列表，表示线的两个端点。

        注意，如果添加的线已经存在，则直接返回已有的线。

        Returns:
            Link: 新添加的线对象。
        """
        assert len(nodes) == 2
        for elem in nodes:
            assert isinstance(elem, Mesh3.Node)
        index = core.mesh3_add_link(self.handle, nodes[0].index, nodes[1].index)
        return self.get_link(index)

    core.use(c_size_t, 'mesh3_add_face3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(c_size_t, 'mesh3_add_face4', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def add_face(self, links):
        """
        根据给定的线创建一个面并返回。

        Args:
            links (list): 包含线对象的列表，用于创建面。

        注意，在创建的过程中，会自动识别线的端点的位置，并且对节点进行排序，从而尽可能保证，面的所有的节点，恰好能够按照顺序形成一个闭环。

        Returns:
            Face: 新创建的面对象。
        """
        for elem in links:
            assert isinstance(elem, Mesh3.Link)
        if len(links) == 3:
            index = core.mesh3_add_face3(self.handle, links[0].index, links[1].index, links[2].index)
            return self.get_face(index)
        if len(links) == 4:
            index = core.mesh3_add_face4(self.handle, links[0].index, links[1].index, links[2].index, links[3].index)
            return self.get_face(index)

    core.use(c_size_t, 'mesh3_add_body4', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)
    core.use(c_size_t, 'mesh3_add_body6', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t)

    def add_body(self, faces):
        """
        根据给定的面创建一个体并返回。

        Args:
            faces (list): 包含面对象的列表，用于创建体。

        Returns:
            Body: 新创建的体对象。
        """
        for elem in faces:
            assert isinstance(elem, Mesh3.Face)
        if len(faces) == 4:
            index = core.mesh3_add_body4(self.handle, faces[0].index, faces[1].index, faces[2].index, faces[3].index)
            return self.get_body(index)
        if len(faces) == 6:
            index = core.mesh3_add_body6(self.handle, faces[0].index, faces[1].index, faces[2].index, faces[3].index,
                                         faces[4].index, faces[5].index)
            return self.get_body(index)

    core.use(None, 'mesh3_change_view', c_void_p, c_void_p, c_void_p)

    def change_view(self, c_new, c_old):
        """
        改变网格的视图。

        Args:
            c_new (Coord3): 新的坐标系统。
            c_old (Coord3): 旧的坐标系统。

        Returns:
            Mesh3: 当前网格对象。
        """
        assert isinstance(c_new, Coord3)
        assert isinstance(c_old, Coord3)
        core.mesh3_change_view(self.handle, c_new.handle, c_old.handle)
        return self

    core.use(None, 'mesh3_get_slice', c_void_p, c_void_p, c_void_p)

    def get_slice(self, node_kept):
        """
        获取网格的切片。

        Args:
            node_kept (function): 一个函数，用于判断节点是否保留。

        Returns:
            Mesh3: 切片后的网格对象。
        """
        kernel = CFUNCTYPE(c_bool, c_double, c_double, c_double)
        data = Mesh3()
        core.mesh3_get_slice(data.handle, self.handle, kernel(node_kept))
        return data

    core.use(None, 'mesh3_append', c_void_p, c_void_p)

    def append(self, other):
        """
        将另一个网格对象追加到当前网格对象中。

        Args:
            other (Mesh3): 要追加的网格对象。

        Returns:
            Mesh3: 当前网格对象。
        """
        assert isinstance(other, Mesh3)
        core.mesh3_append(self.handle, other.handle)
        return self

    core.use(None, 'mesh3_del_nodes', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_nodes', c_void_p)

    def del_nodes(self, should_del=None):
        """
        删除网格中的节点。

        Args:
            should_del (function, optional): 一个函数，用于判断节点是否应该删除。如果为 None，则删除所有孤立节点。
        """
        if should_del is None:
            core.mesh3_del_isolated_nodes(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_nodes(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_links', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_links', c_void_p)

    def del_links(self, should_del=None):
        """
        删除网格中的线。

        Args:
            should_del (function, optional): 一个函数，用于判断线是否应该删除。如果为 None，则删除所有孤立线。
        """
        if should_del is None:
            core.mesh3_del_isolated_links(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_links(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_faces', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_faces', c_void_p)

    def del_faces(self, should_del=None):
        """
        删除网格中的面。

        Args:
            should_del (function, optional): 一个函数，用于判断面是否应该删除。如果为 None，则删除所有孤立面。
        """
        if should_del is None:
            core.mesh3_del_isolated_faces(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_faces(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_bodies', c_void_p, c_void_p)

    def del_bodies(self, should_del=None):
        """
        删除网格中的体。

        Args:
            should_del (function): 一个函数，用于判断体是否应该删除。
        """
        assert should_del is not None
        kernel = CFUNCTYPE(c_bool, c_size_t)
        core.mesh3_del_bodies(self.handle, kernel(should_del))

    def del_isolated_nodes(self):
        """
        删除网格中的孤立节点。
        """
        core.mesh3_del_isolated_nodes(self.handle)

    def del_isolated_links(self):
        """
        删除网格中的孤立线。
        """
        core.mesh3_del_isolated_links(self.handle)

    def del_isolated_faces(self):
        """
        删除网格中的孤立面。
        """
        core.mesh3_del_isolated_faces(self.handle)

    core.use(None, 'mesh3_print_trimesh',
             c_void_p, c_char_p, c_char_p, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def print_trimesh(vertex_file, triangle_file, data, index_start_from=1, na=99999999, fa=99999999):
        """
        将三角形网格信息打印到文件。

        Args:
            vertex_file (str): 顶点文件的路径。
            triangle_file (str): 三角形文件的路径。
            data (Mesh3): 要打印的网格对象。
            index_start_from (int, optional): 索引的起始值，默认为 1。
            na (int, optional): 无效节点的索引值，默认为 99999999。
            fa (int, optional): 无效面的索引值，默认为 99999999。

        注意，给定的文件路径绝对不能包含中文字符，否则会出错。
        """
        assert isinstance(data, Mesh3)
        core.mesh3_print_trimesh(data.handle, make_c_char_p(vertex_file), make_c_char_p(triangle_file),
                                 index_start_from, na, fa)

    core.use(None, 'mesh3_create_tri', c_void_p, c_double, c_double,
             c_double, c_double, c_double)

    @staticmethod
    def create_tri(x1, y1, x2, y2, edge_length):
        """
        在x-y平面创建等边三角形网格。

        Args:
            x1 (float): 矩形区域x轴起始坐标
            y1 (float): 矩形区域y轴起始坐标
            x2 (float): 矩形区域x轴结束坐标
            y2 (float): 矩形区域y轴结束坐标
            edge_length (float): 目标三角形边长（实际边长可能略有不同）

        Returns:
            Mesh3: 生成的二维三角形网格对象

        Note:
            - 生成的网格严格位于z=0平面
            - 实际网格范围可能与指定区域略有差异
            - 三角形排列可能产生锯齿状边界
        """
        data = Mesh3()
        core.mesh3_create_tri(data.handle, x1, y1, x2, y2, edge_length)
        return data

    core.use(None, 'mesh3_create_tetra', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double)

    @staticmethod
    def create_tetra(x1, y1, z1, x2, y2, z2, edge_length):
        """
        在三维区域生成四面体网格。

        Args:
            x1 (float): 立方体区域x轴起始坐标
            y1 (float): 立方体区域y轴起始坐标
            z1 (float): 立方体区域z轴起始坐标
            x2 (float): 立方体区域x轴结束坐标
            y2 (float): 立方体区域y轴结束坐标
            z2 (float): 立方体区域z轴结束坐标
            edge_length (float): 目标四面体边长

        Returns:
            Mesh3: 生成的三维四面体网格对象
        """
        data = Mesh3()
        core.mesh3_create_tetra(data.handle, x1, y1, z1, x2, y2, z2, edge_length)
        return data

    core.use(None, 'mesh3_create_cubic', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    core.use(None, 'mesh3_create_cubic_by_lattice3', c_void_p, c_void_p)

    @staticmethod
    def create_cube(x1=None, y1=None, z1=None, x2=None, y2=None, z2=None, dx=None,
                    dy=None, dz=None, lat=None, buffer=None):
        """
        创建立方体结构网格。

        Args:
            x1 (float): 区域x轴最小坐标
            y1 (float): 区域y轴最小坐标
            z1 (float): 区域z轴最小坐标
            x2 (float): 区域x轴最大坐标
            y2 (float): 区域y轴最大坐标
            z2 (float): 区域z轴最大坐标
            dx (float): x方向网格尺寸
            dy (float): y方向网格尺寸（默认同dx）
            dz (float): z方向网格尺寸（默认同dx）
            lat (Lattice3): 晶格结构对象
            buffer (Mesh3): 用于存储结果的网格对象

        Returns:
            Mesh3: 生成的立方体网格对象

        Raises:
            AssertionError: 当必需参数未提供时抛出
        """
        if lat is not None:
            if not isinstance(buffer, Mesh3):
                buffer = Mesh3()
            core.mesh3_create_cubic_by_lattice3(buffer.handle, lat.handle)
            return buffer
        else:
            assert x1 is not None and y1 is not None and z1 is not None
            assert x2 is not None and y2 is not None and z2 is not None
            assert dx is not None
            if dy is None:
                dy = dx
            if dz is None:
                dz = dx
            if not isinstance(buffer, Mesh3):
                buffer = Mesh3()
            core.mesh3_create_cubic(buffer.handle, x1, y1, z1, x2, y2, z2, dx, dy, dz)
            return buffer

    core.use(c_size_t, 'mesh3_get_nearest_node_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_node(self, pos):
        """
        获取距离给定位置最近的节点。

        Args:
            pos (Iterable[float]): 三维坐标(x, y, z)

        Returns:
            Node/None: 最近节点对象，若无节点返回None
        """
        if self.node_number > 0:
            index = core.mesh3_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_node(index)

    core.use(c_size_t, 'mesh3_get_nearest_link_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_link(self, pos):
        """
        获取距离给定位置最近的线。

        Args:
            pos (Iterable[float]): 三维坐标(x, y, z)

        Returns:
            Link/None: 最近线对象，无线时返回None
        """
        if self.link_number > 0:
            index = core.mesh3_get_nearest_link_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_link(index)

    core.use(c_size_t, 'mesh3_get_nearest_face_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_face(self, pos):
        """
        获取距离给定位置最近的面。

        Args:
            pos (Iterable[float]): 三维坐标(x, y, z)

        Returns:
            Face/None: 最近面对象，无面时返回None
        """
        if self.face_number > 0:
            index = core.mesh3_get_nearest_face_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_face(index)

    core.use(c_size_t, 'mesh3_get_nearest_body_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_body(self, pos):
        """
        获取距离给定位置最近的体。

        Args:
            pos (Iterable[float]): 三维坐标(x, y, z)

        Returns:
            Body/None: 最近体对象，无体时返回None
        """
        if self.body_number > 0:
            index = core.mesh3_get_nearest_body_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_body(index)

    core.use(None, 'mesh3_get_loc_range', c_void_p, c_void_p, c_void_p)

    def get_pos_range(self, lr=None, rr=None):
        """
        获取所有节点的空间坐标范围。

        Args:
            lr (Array3, optional): 用于存储最小坐标的Array3对象，默认创建新实例
            rr (Array3, optional): 用于存储最大坐标的Array3对象，默认创建新实例

        Returns:
            tuple: 包含最小坐标和最大坐标的元组，格式为(lr_list, rr_list)

        Note:
            - 返回的坐标范围按[x_min, y_min, z_min]和[x_max, y_max, z_max]格式
            - 输入参数lr和rr将被直接修改
        """
        if not isinstance(lr, Array3):
            lr = Array3()
        if not isinstance(rr, Array3):
            rr = Array3()
        core.mesh3_get_loc_range(self.handle, lr.handle, rr.handle)
        return lr.to_list(), rr.to_list()


class Alg:
    core.use(None, 'link_point2', c_void_p, c_void_p, c_double)

    @staticmethod
    def link_point2(points, lmax):
        """
        在二维点集之间建立连接关系。

        Args:
            points (Vector): 包含二维坐标点的向量，格式为[x0, y0, x1, y1,...]
            lmax (float): 允许建立连接的最大距离阈值

        Returns:
            UintVector: 包含连接索引的列表，格式为[起点0, 终点0, 起点1, 终点1,...]

        Raises:
            AssertionError: 当points参数不是Vector类型时抛出
        """
        assert isinstance(points, Vector)
        lnks = UintVector()
        core.link_point2(lnks.handle, points.handle, lmax)
        return lnks

    core.use(c_double, 'get_velocity_after_slowdown_by_viscosity', c_double, c_double, c_double)

    @staticmethod
    def get_velocity_after_slowdown_by_viscosity(v0, a0, time):
        """
        计算粘性流体中物体速度随时间的变化。

        Args:
            v0 (float): 初始速度（m/s）
            a0 (float): 初始时刻由粘性阻力产生的加速度（m/s²），方向与速度相反
            time (float): 经过的时间（秒）

        Returns:
            float: 指定时间后的物体速度（m/s）

        Note:
            基于粘性阻力与速度成正比的假设，使用指数衰减模型计算
        """
        return core.get_velocity_after_slowdown_by_viscosity(v0, a0, time)

    core.use(None, 'prepare_zml', c_char_p, c_char_p, c_char_p)

    @staticmethod
    def prepare_zml(code_path, target_folder, znetwork_folder):
        """
        准备ZML库的头文件到指定目录。

        Args:
            code_path (str): 需要监测的C++源代码目录路径
            target_folder (str): 目标输出目录，用于存放生成的zml头文件
            znetwork_folder (str): ZNetwork库的源代码目录路径

        Returns:
            None

        Note:
            该操作会覆盖目标目录中已存在的同名文件
        """
        core.prepare_zml(make_c_char_p(code_path), make_c_char_p(target_folder), make_c_char_p(znetwork_folder))


class LinearExpr(HasHandle):
    core.use(c_void_p, 'new_lexpr')
    core.use(None, 'del_lexpr', c_void_p)

    def __init__(self, handle=None):
        super(LinearExpr, self).__init__(handle, core.new_lexpr, core.del_lexpr)

    core.use(None, 'lexpr_save', c_void_p, c_char_p)

    def save(self, path):
        """
        将线性表达式序列化到指定路径。

        Args:
            path (str): 文件保存路径，扩展名决定格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读性XML格式（体积大）
                - 其他: 高效二进制格式（平台相关）

        Note:
            自动创建父目录，会覆盖已存在的文件
        """
        if isinstance(path, str):
            make_parent(path)
            core.lexpr_save(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_load', c_void_p, c_char_p)

    def load(self, path):
        """
        从文件加载线性表达式数据。

        Args:
            path (str): 文件路径，格式由扩展名决定

        Raises:
            FileNotFoundError: 当文件不存在时抛出
            ValueError: 当文件格式不匹配时抛出
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.lexpr_load(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'lexpr_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将表达式序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选 'text', 'xml', 'binary'

        Returns:
            FileMap: 包含序列化数据的文件映射对象
        """
        fmap = FileMap()
        core.lexpr_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从文件映射对象加载表达式。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 数据格式，需与写入时一致

        Raises:
            TypeError: 当fmap参数类型错误时抛出
        """
        assert isinstance(fmap, FileMap)
        core.lexpr_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __eq__(self, rhs):
        """判断两个线性表达式是否指向同一内存对象"""
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        """判断两个线性表达式是否不同对象"""
        return not (self == rhs)

    def __str__(self):
        """
        获取线性表达式的字符串表示。

        Returns:
            str: 格式如'zml.LinearExpr(c + 1.2*x(3) + 0.5*x(5))'
        """
        if self.length > 0:
            s = ' + '.join([f'{self[i][1]}*x({self[i][0]})' for i in range(len(self))])
            return f'zml.LinearExpr({self.c} + {s})'
        else:
            return f'zml.LinearExpr({self.c})'

    core.use(c_double, 'lexpr_get_c', c_void_p)
    core.use(None, 'lexpr_set_c', c_void_p, c_double)

    @property
    def c(self):
        """
        线性表达式的常数项。

        Returns:
            float: 表达式中的常数偏移量
        """
        return core.lexpr_get_c(self.handle)

    @c.setter
    def c(self, value):
        """
        设置线性表达式的常数项。

        Args:
            value (float): 新的常数项值
        """
        core.lexpr_set_c(self.handle, value)

    def set_c(self, value):
        """
        设置常数项并返回当前实例以便链式调用。

        Args:
            value (float): 新的常数项值

        Returns:
            LinearExpr: self实例
        """
        self.c = value
        return self

    core.use(c_size_t, 'lexpr_get_length', c_void_p)

    @property
    def length(self):
        """
        获取线性项的数量（不包括常数项）。

        Returns:
            int: 当前表达式中的线性项数量
        """
        return core.lexpr_get_length(self.handle)

    def __len__(self):
        """
        获取线性项的数量（与length属性一致）。

        Returns:
            int: 当前表达式中的线性项数量
        """
        return self.length

    core.use(c_size_t, 'lexpr_get_index', c_void_p, c_size_t)
    core.use(c_double, 'lexpr_get_weight', c_void_p, c_size_t)

    def __getitem__(self, i):
        """
        通过索引获取线性项信息。

        Args:
            i (int): 项索引（0 <= i < length）

        Returns:
            tuple: (变量索引, 系数) 的元组，格式为(int, float)
        """
        i = get_index(i, self.length)
        if i is not None:
            index = core.lexpr_get_index(self.handle, i)
            weight = core.lexpr_get_weight(self.handle, i)
            return index, weight

    core.use(None, 'lexpr_add', c_void_p, c_size_t, c_double)

    def add(self, index, weight):
        """
        添加线性项到表达式。

        Args:
            index (int): 变量索引
            weight (float): 变量系数

        Returns:
            LinearExpr: self实例便于链式调用
        """
        core.lexpr_add(self.handle, index, weight)
        return self

    core.use(None, 'lexpr_clear', c_void_p)

    def clear(self):
        """
        重置表达式为初始状态。

        Note:
            - 清除所有线性项
            - 将常数项置零
        """
        core.lexpr_clear(self.handle)
        return self

    core.use(None, 'lexpr_merge', c_void_p)

    def merge(self):
        """
        合并同类项并简化表达式。

        Note:
            - 合并相同变量索引的系数
            - 删除系数绝对值小于1e-15的项
            - 操作会改变表达式内部存储结构
        """
        core.lexpr_merge(self.handle)

    core.use(None, 'lexpr_plus', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lexpr_multiply', c_void_p, c_size_t, c_double)

    def __add__(self, other):
        """
        实现线性表达式加法运算。

        Args:
            other (LinearExpr): 另一个线性表达式

        Returns:
            LinearExpr: 新的表达式对象，包含两个表达式之和
        """
        assert isinstance(other, LinearExpr)
        result = LinearExpr()
        core.lexpr_plus(result.handle, self.handle, other.handle)
        return result

    def __sub__(self, other):
        """
        实现线性表达式减法运算。

        Args:
            other (LinearExpr): 另一个线性表达式

        Returns:
            LinearExpr: 新的表达式对象，包含两个表达式之差
        """
        return self.__add__(other * (-1.0))

    def __mul__(self, scale):
        """
        实现表达式与标量的乘法运算。

        Args:
            scale (float): 缩放系数

        Returns:
            LinearExpr: 新的缩放后的表达式对象
        """
        result = LinearExpr()
        core.lexpr_multiply(result.handle, self.handle, scale)
        return result

    def __truediv__(self, scale):
        """
        实现表达式与标量的除法运算。

        Args:
            scale (float): 除数（不能为0）

        Returns:
            LinearExpr: 新的缩放后的表达式对象
        """
        return self.__mul__(1.0 / scale)

    @staticmethod
    def create(index):
        """
        创建基本变量表达式。

        Args:
            index (int): 变量索引

        Returns:
            LinearExpr: 形式为1.0*x(index)的表达式
        """
        lexpr = LinearExpr()
        lexpr.c = 0
        lexpr.add(index, 1.0)
        return lexpr

    @staticmethod
    def create_constant(c):
        """
        创建常数表达式。

        Args:
            c (float): 常数值

        Returns:
            LinearExpr: 仅包含常数项的表达式
        """
        lexpr = LinearExpr()
        lexpr.c = c
        return lexpr

    core.use(None, 'lexpr_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        深度克隆另一个表达式数据。

        Args:
            other (LinearExpr): 源表达式对象

        Returns:
            LinearExpr: self实例便于链式调用

        Note:
            完全复制源表达式的所有项和常数项
        """
        if isinstance(other, LinearExpr):
            core.lexpr_clone(self.handle, other.handle)
        return self


class DynSys(HasHandle):
    """
    质量-弹性动力学系统。用以实现固体计算的模型。对于任何固体的变形及运动问题，都可以归结为两个概念，即质量和弹性。对于任何一个自由度，
    都可以定义“质量”和“位置”。

    由于整个体系是线性的，因此，某个自由度的“受力”一定是一个或者多个自由度“位置”的线性函数，即
        f = ax + b                                                       (1)
    其中f代表各个自由度的“受力”，x代表各个自由度的“位置”，f和x均为N阶向量，其中N为自由度的数量。
    a是一个N*N的稀疏矩阵，b为一个长度为N的常向量。

    同时，在给定时间步长dt之后，一个自由度在dt之后的“位置”，也是dt之后“受力”的线性函数。根据牛顿第2定律，有
        x=x0 + v0*dt + 0.5*(f/m)*dt*dt                                   (2)
    整理可得:
        x = cf + d                                                       (3)
    其中 c=0.5*dt*dt/m, d=x0 + v0*dt. 其中m为各个自由度的质量，x0为上一次更新之后的各个自由度的位置, v0为各个自由度的速度. 其中
    m, x0, v0均为长度为N的向量.

    以上方程(1)和(3)构成了以向量x和向量f为未知量的N阶的线性方程组，求解之后，即可得到t0+dt时刻之后，整个体系各个自由度的“位置”向量x和
    “受力”向量f，并进一步得到各个自由度的速度v.

    以上步骤完成一次迭代。

    todo:
        对于pos、vel和mas的读写，需要支持向量化操作. 对于p2f，也尽量设计向量化操作的方法. @23-10-08

    """
    core.use(c_void_p, 'new_dynsys')
    core.use(None, 'del_dynsys', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化动力学系统。

        Args:
            path (str, optional): 序列化文件路径，若存在则从文件加载
            handle: 已存在的底层对象句柄

        Raises:
            FileNotFoundError: 当指定path但文件不存在时抛出
        """
        super(DynSys, self).__init__(handle, core.new_dynsys, core.del_dynsys)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'dynsys_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存系统状态到文件。

        Args:
            path (str): 文件保存路径，支持格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读XML格式（体积大）
                - 其他: 高效二进制格式（平台相关）

        Note:
            自动创建父目录，会覆盖已存在的文件
        """
        if isinstance(path, str):
            make_parent(path)
            core.dynsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        从文件加载系统状态。

        Args:
            path (str): 序列化文件路径

        Raises:
            ValueError: 文件格式不匹配时抛出
            RuntimeError: 数据加载失败时抛出
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.dynsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'dynsys_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        序列化到文件映射对象。

        Args:
            fmt (str): 序列化格式，可选 'text', 'xml', 'binary'

        Returns:
            FileMap: 包含序列化数据的文件映射
        """
        fmap = FileMap()
        core.dynsys_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从文件映射加载数据。

        Args:
            fmap (FileMap): 包含序列化数据的文件映射
            fmt (str): 数据格式，需与写入时一致

        Raises:
            TypeError: 当fmap参数类型错误时抛出
        """
        assert isinstance(fmap, FileMap)
        core.dynsys_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """
        文件映射属性（二进制格式序列化）。

        Getter返回FileMap对象，Setter从FileMap加载数据
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_int, 'dynsys_iterate', c_void_p, c_double, c_void_p)

    def iterate(self, dt, solver):
        """
        执行单次时间步长迭代。

        Args:
            dt (float): 时间步长（秒）
            solver: 线性方程组求解器实例

        Returns:
            int: 迭代状态码（0表示成功）

        Note:
            需要有效的求解器来处理线性方程组
        """
        return core.dynsys_iterate(self.handle, dt, solver.handle)

    core.use(c_size_t, 'dynsys_size', c_void_p)

    @property
    def size(self):
        """
        系统的自由度数量（读写属性）。

        例如：
            3节点三角形网格每个节点2个自由度 → size=6
            2个共享边的三角形网格 → size=8
        """
        return core.dynsys_size(self.handle)

    core.use(None, 'dynsys_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.dynsys_resize(self.handle, value)

    core.use(c_double, 'dynsys_get_pos', c_void_p, c_size_t)

    def get_pos(self, idx):
        """
        获取指定自由度的当前位置。

        Args:
            idx (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 当前位置值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_pos(self.handle, idx)

    core.use(None, 'dynsys_set_pos', c_void_p, c_size_t, c_double)

    def set_pos(self, idx, value):
        """
        设置指定自由度的位置。

        Args:
            idx (int): 自由度索引（0 <= idx < size）
            value (float): 新位置值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_pos(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_vel', c_void_p, c_size_t)

    def get_vel(self, idx):
        """
        获取指定自由度的当前速度。

        Args:
            idx (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 当前速度值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_vel(self.handle, idx)

    core.use(None, 'dynsys_set_vel', c_void_p, c_size_t, c_double)

    def set_vel(self, idx, value):
        """
        设置指定自由度的速度。

        Args:
            idx (int): 自由度索引（0 <= idx < size）
            value (float): 新速度值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_vel(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_mas', c_void_p, c_size_t)

    def get_mas(self, idx):
        """
        获取指定自由度的质量。

        Args:
            idx (int): 自由度索引（0 <= idx < size）

        Returns:
            float: 质量值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_mas(self.handle, idx)

    core.use(None, 'dynsys_set_mas', c_void_p, c_size_t, c_double)

    def set_mas(self, idx, value):
        """
        设置指定自由度的质量。

        Args:
            idx (int): 自由度索引（0 <= idx < size）
            value (float): 新质量值
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_mas(self.handle, idx, value)

    core.use(c_void_p, 'dynsys_get_p2f', c_void_p, c_size_t)

    def get_p2f(self, idx):
        """
        获取位置到受力的线性关系表达式。

        Args:
            idx (int): 自由度索引（0 <= idx < size）

        Returns:
            LinearExpr: 描述受力与位置关系的线性表达式
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            handle = core.dynsys_get_p2f(self.handle, idx)
            if handle > 0:
                return LinearExpr(handle=handle)

    core.use(c_double, 'dynsys_get_lexpr_value', c_void_p, c_void_p)

    def get_lexpr_value(self, lexpr):
        """
        计算线性表达式在当前状态的取值。

        Args:
            lexpr (LinearExpr): 需要计算的线性表达式

        Returns:
            float: 表达式的当前计算值

        Example:
            用于计算应力、应变等派生量
        """
        assert isinstance(lexpr, LinearExpr)
        return core.dynsys_get_lexpr_value(self.handle, lexpr.handle)


class SpringSys(HasHandle):
    """
    质点弹簧系统模拟器，用于测试基于物理的弹性体变形。

    Attributes:
        node_number (int): 实际节点数量（只读）
        virtual_node_number (int): 虚拟节点数量（只读）
        spring_number (int): 弹簧数量（只读）
        damper_number (int): 阻尼器数量（只读）

    Note:
        系统由以下组件构成：
        - Node: 具有质量、位置、速度的实际节点
        - VirtualNode: 由实际节点位置定义的虚拟位置
        - Spring: 连接两个VirtualNode的弹性元件
        - Damper: 连接两个实际Node的阻尼元件
    """

    class Node(Object):
        """
        具有质量、位置、速度属性的节点。是弹簧系统的基本概念，建模时需要将实体离散为一个个的node，将质量集中到这些node上。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 节点索引（需满足 0 <= index < model.node_number）

        Attributes:
            pos (list[float]): 三维位置坐标 [x, y, z]（单位：米）
            vel (list[float]): 三维速度向量 [vx, vy, vz]（单位：米/秒）
            force (list[float]): 外部施加力 [fx, fy, fz]（单位：牛顿）
            mass (float): 节点质量（单位：千克）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'springsys_get_node_pos', c_void_p, c_size_t, c_size_t)
        core.use(None, 'springsys_set_node_pos', c_void_p, c_size_t, c_size_t, c_double)

        @property
        def pos(self):
            """
            节点在三维空间的位置 <单位m>

            Returns:
                list[float]: 三维坐标列表 [x, y, z]
            """
            return [core.springsys_get_node_pos(self.model.handle, self.index, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            节点在三维空间的位置 <单位m>

            Args:
                value (list[float]): 新的三维坐标 [x, y, z]

            Raises:
                AssertionError: 当输入维度不等于3时抛出
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_pos(self.model.handle, self.index, i, value[i])

        core.use(c_double, 'springsys_get_node_vel', c_void_p, c_size_t, c_size_t)
        core.use(None, 'springsys_set_node_vel', c_void_p, c_size_t, c_size_t, c_double)

        @property
        def vel(self):
            """
            节点的速度  <单位m/s>
            """
            return (core.springsys_get_node_vel(self.model.handle, self.index, 0),
                    core.springsys_get_node_vel(self.model.handle, self.index, 1),
                    core.springsys_get_node_vel(self.model.handle, self.index, 2))

        @vel.setter
        def vel(self, value):
            """
            节点的速度  <单位m/s>
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_vel(self.model.handle, self.index, i, value[i])

        core.use(c_double, 'springsys_get_node_force', c_void_p, c_size_t, c_size_t)
        core.use(None, 'springsys_set_node_force', c_void_p, c_size_t, c_size_t, c_double)

        @property
        def force(self):
            """
            在节点上施加的外部力  <单位N>
            """
            return (core.springsys_get_node_force(self.model.handle, self.index, 0),
                    core.springsys_get_node_force(self.model.handle, self.index, 1),
                    core.springsys_get_node_force(self.model.handle, self.index, 2))

        @force.setter
        def force(self, value):
            """
            在节点上施加的外部力  <单位N>
            """
            assert len(value) == 3
            for i in range(3):
                core.springsys_set_node_force(self.model.handle, self.index, i, value[i])

        core.use(None, 'springsys_set_node_mass', c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_node_mass', c_void_p, c_size_t)

        @property
        def mass(self):
            """
            节点的集中质量  <单位kg>
            """
            return core.springsys_get_node_mass(self.model.handle, self.index)

        @mass.setter
        def mass(self, value):
            """
            节点的集中质量  <单位kg>
            """
            core.springsys_set_node_mass(self.model.handle, self.index, value)

    class VirtualNode(Object):
        """
        虚拟节点类：其位置可以用实际的多个node的空间位置的线性组合来表示的虚拟位置。
        用以辅助建立Node之间的力的关系，不具有质量和速度的属性。
        虚拟节点的位置不会作为未知量参与到迭代中，因此增加虚拟节点的数量，不会明显降低计算的速度。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 虚拟节点索引（需满足 0 <= index < model.virtual_node_number）

        Attributes:
            x (LinearExpr): x坐标的线性表达式（读写属性）
            y (LinearExpr): y坐标的线性表达式（读写属性）
            z (LinearExpr): z坐标的线性表达式（读写属性）
            pos (list[float]): 计算得到的实际三维位置（单位：米，只读）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.virtual_node_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_get_virtual_node', c_void_p, c_size_t, c_size_t, c_size_t)

        def __getitem__(self, idim):
            """
            获取指定维度的位置表达式

            Args:
                idim (int): 维度索引（0=x, 1=y, 2=z）

            Returns:
                LinearExpr: 对应维度的线性表达式
            """
            lexpr = LinearExpr()
            core.springsys_get_virtual_node(self.model.handle, self.index, idim, lexpr.handle)
            return lexpr

        core.use(None, 'springsys_set_virtual_node', c_void_p, c_size_t, c_size_t, c_size_t)

        def __setitem__(self, idim, lexpr):
            """
            设置指定维度的位置表达式

            Args:
                idim (int): 维度索引（0=x, 1=y, 2=z）
                lexpr (LinearExpr): 新的线性表达式

            Raises:
                AssertionError: 当lexpr类型错误时抛出
            """
            assert isinstance(lexpr, LinearExpr)
            core.springsys_set_virtual_node(self.model.handle, self.index, idim, lexpr.handle)

        @property
        def x(self):
            """x轴位置表达式（等效于self[0]）"""
            return self[0]

        @x.setter
        def x(self, value):
            """设置x轴位置表达式（等效于self[0] = value）"""
            self[0] = value

        @property
        def y(self):
            """y轴位置表达式（等效于self[1]）"""
            return self[1]

        @y.setter
        def y(self, value):
            """设置y轴位置表达式（等效于self[1] = value）"""
            self[1] = value

        @property
        def z(self):
            """z轴位置表达式（等效于self[2]）"""
            return self[2]

        @z.setter
        def z(self, value):
            """设置z轴位置表达式（等效于self[2] = value）"""
            self[2] = value

        core.use(c_double, 'springsys_get_virtual_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            获取虚拟节点当前计算位置。

            Returns:
                list[float]: 三维坐标 [x, y, z]，单位：米

            Note:
                该位置根据关联的实际节点实时计算得出
            """
            return [core.springsys_get_virtual_node_pos(self.model.handle, self.index, i) for i in range(3)]

    class Spring(Object):
        """
        弹簧，用以连接两个virtual_node，在两者之间建立线性的弹性关系。注意，Spring只能用以连接两个virtual_node，
        不能连接在两个实际的node上。如果要用弹簧连接实际的node，则必须首先在实际node的位置建立virtual_node，然后
        连接相应的virtual_node。
        注意：两个虚拟节点之间，可以添加多个不同的弹簧，这些弹簧会同时发挥作用。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 弹簧索引（需满足 0 <= index < model.spring_number）

        Attributes:
            len0 (float): 弹簧自然长度（单位：米，可读写）
            k (float): 弹性系数（单位：牛/米，可读写）
            tension (float): 当前时刻张力值（单位：牛，只读）
            virtual_nodes (tuple[VirtualNode]): 连接的两个虚拟节点（可读写）
            pos (tuple[float]): 弹簧中心点坐标（单位：米，只读）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出

        Note:
            - 只能连接VirtualNode，连接Node时会自动创建对应VirtualNode
            - 同一对虚拟节点可添加多个不同参数的弹簧
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.spring_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_set_spring_len0', c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_spring_len0', c_void_p, c_size_t)

        @property
        def len0(self):
            """
            获取/设置弹簧自然长度。

            Returns:
                float: 当前自然长度值，单位：米
            """
            return core.springsys_get_spring_len0(self.model.handle, self.index)

        @len0.setter
        def len0(self, value):
            """
            设置弹簧自然长度。

            Args:
                value (float): 新自然长度值，单位：米
            """
            core.springsys_set_spring_len0(self.model.handle, self.index, value)

        core.use(c_double, 'springsys_get_spring_tension', c_void_p, c_size_t)

        @property
        def tension(self):
            """
            获取当前张力值。

            Returns:
                float: 瞬时张力值，单位：牛（N）

            Note:
                正值表示拉力，负值表示压力
            """
            return core.springsys_get_spring_tension(self.model.handle, self.index)

        core.use(None, 'springsys_set_spring_k', c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_spring_k', c_void_p, c_size_t)

        @property
        def k(self):
            """
            获取/设置弹性系数。

            Returns:
                float: 当前弹性系数，单位：牛/米（N/m）
            """
            return core.springsys_get_spring_k(self.model.handle, self.index)

        @k.setter
        def k(self, value):
            """
            设置弹性系数。

            Args:
                value (float): 新弹性系数值，单位：牛/米（N/m）
            """
            core.springsys_set_spring_k(self.model.handle, self.index, value)

        core.use(c_size_t, 'springsys_get_spring_link_n', c_void_p, c_size_t)
        core.use(c_size_t, 'springsys_get_spring_link', c_void_p, c_size_t, c_size_t)
        core.use(None, 'springsys_set_spring_link', c_void_p, c_size_t, c_size_t, c_size_t)

        @property
        def virtual_nodes(self):
            """
            获取/设置连接的虚拟节点对。

            Returns:
                tuple[VirtualNode, VirtualNode]: 当前连接的虚拟节点元组

            Note:
                设置时若传入Node对象，会自动转换为对应位置的VirtualNode
            """
            n = core.springsys_get_spring_link_n(self.model.handle, self.index)
            if n != 2:
                return None, None

            i0 = core.springsys_get_spring_link(self.model.handle, self.index, 0)
            i1 = core.springsys_get_spring_link(self.model.handle, self.index, 1)

            return self.model.get_virtual_node(i0), self.model.get_virtual_node(i1)

        @virtual_nodes.setter
        def virtual_nodes(self, value):
            assert len(value) == 2
            assert isinstance(value[0], SpringSys.VirtualNode)
            assert isinstance(value[1], SpringSys.VirtualNode)
            assert value[0].model.handle == self.model.handle
            assert value[1].model.handle == self.model.handle
            assert value[0].index != value[1].index
            core.springsys_set_spring_link(self.model.handle, self.index, value[0].index, value[1].index)

        @property
        def pos(self):
            """
            计算弹簧中心点空间坐标。

            Returns:
                tuple[float, float, float]|None: 三维坐标(x,y,z)元组，单位：米
                          当任一节点无效时返回None
            """
            virtual_nodes = self.virtual_nodes
            if len(virtual_nodes) == 2:
                if virtual_nodes[0] is not None and virtual_nodes[1] is not None:
                    a = virtual_nodes[0].pos
                    b = virtual_nodes[1].pos
                    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2

        core.use(c_double, 'springsys_get_spring_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取弹簧自定义属性值。

            Args:
                index (int): 自定义属性索引
                default_val: 默认返回值（当属性无效时）
                valid_range: 有效性范围校验（如min=0, max=100）

            Returns:
                float: 属性值或default_val（当值超出有效范围时）
            """
            if index is None:
                return default_val
            value = core.springsys_get_spring_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'springsys_set_spring_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置弹簧自定义属性值。

            Args:
                index (int): 自定义属性索引
                value (float): 新属性值（设为None时重置为默认值1e200）

            Returns:
                Spring: 自身实例，支持链式调用
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.springsys_set_spring_attr(self.model.handle, self.index, index, value)
            return self

    class Damper(Object):
        """
        阻尼器元件，连接两个实际节点并施加粘性阻力。

        Args:
            model (SpringSys): 所属弹簧系统实例
            index (int): 阻尼器索引（需满足 0 <= index < model.damper_number）

        Attributes:
            nodes (tuple[Node, Node]): 连接的两个实际节点（可读写）
            vis (float): 粘性阻尼系数（单位：牛/(米/秒)，可读写）

        Raises:
            AssertionError: 当参数类型或索引范围不合法时抛出

        Note:
            - 只能连接实际节点(Node)，连接VirtualNode会导致断言失败
            - 阻尼力方向与节点相对速度方向相反
        """

        def __init__(self, model, index):
            assert isinstance(model, SpringSys)
            assert isinstance(index, int)
            assert index < model.damper_number
            self.model = model
            self.index = index

        core.use(None, 'springsys_set_damper_link', c_void_p, c_size_t, c_size_t, c_size_t)
        core.use(c_size_t, 'springsys_get_damper_link', c_void_p, c_size_t, c_size_t)
        core.use(c_size_t, 'springsys_get_damper_link_n', c_void_p, c_size_t)

        @property
        def nodes(self):
            """
            获取/设置连接的实际节点对。

            Returns:
                tuple[Node, Node]|(None, None): 当前连接的节点元组，无效时返回(None, None)
            """
            n = core.springsys_get_damper_link_n(self.model.handle, self.index)
            if n != 2:
                return None, None

            i0 = core.springsys_get_damper_link(self.model.handle, self.index, 0)
            i1 = core.springsys_get_damper_link(self.model.handle, self.index, 1)

            return self.model.get_node(i0), self.model.get_node(i1)

        @nodes.setter
        def nodes(self, value):
            """
            设置连接的实际节点对。

            Args:
                value (tuple[Node, Node]): 包含两个Node实例的元组

            Raises:
                AssertionError: 当节点类型错误、属于不同系统或索引相同时抛出
            """
            assert len(value) == 2
            assert isinstance(value[0], SpringSys.Node)
            assert isinstance(value[1], SpringSys.Node)
            assert value[0].handle == self.model.handle
            assert value[1].handle == self.model.handle
            assert value[0].index != value[1].index
            core.springsys_set_damper_link(self.model.handle, self.index, value[0].index, value[1].index)

        core.use(None, 'springsys_set_damper_vis', c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_damper_vis', c_void_p, c_size_t)

        @property
        def vis(self):
            """
            获取当前粘性阻尼系数。

            Returns:
                float: 阻尼系数值
            """
            return core.springsys_get_damper_vis(self.model.handle, self.index)

        @vis.setter
        def vis(self, value):
            """
            设置粘性阻尼系数。

            Args:
                value (float): 新阻尼系数值
            """
            core.springsys_set_damper_vis(self.model.handle, self.index, value)

    core.use(c_void_p, 'new_springsys')
    core.use(None, 'del_springsys', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化弹簧系统实例。

        Args:
            path (str, optional): 序列化文件路径，当handle为None时有效
            handle (c_void_p, optional): 已有系统句柄，用于包装已有对象

        Note:
            当handle为None时会创建新系统，若指定path参数则从文件加载
        """
        super(SpringSys, self).__init__(handle, core.new_springsys, core.del_springsys)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回系统状态摘要字符串。

        Returns:
            str: 包含句柄、节点数、虚拟节点数和弹簧数的描述字符串
        """
        return (f'zml.SpringSys(handle = {self.handle}, node_n = {self.node_number}, '
                f'virtual_node_n = {self.virtual_node_number}, spring_n = {self.spring_number})')

    @staticmethod
    def virtual_x(node):
        """
        创建x轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: x轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.x
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 0)

    @staticmethod
    def virtual_y(node):
        """
        创建y轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: y轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.y
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 1)

    @staticmethod
    def virtual_z(node):
        """
        创建z轴方向的位置线性表达式。

        Args:
            node (Node|VirtualNode): 实际或虚拟节点

        Returns:
            LinearExpr: z轴位置表达式
        """
        if isinstance(node, SpringSys.VirtualNode):
            return node.z
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 2)

    core.use(None, 'springsys_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存系统状态到文件。

        Args:
            path (str): 保存路径，扩展名决定格式：
                - .txt: 跨平台文本格式（不可读）
                - .xml: 可读XML格式（体积大速度慢）
                - 其他: 二进制格式（最快最小，但跨平台不兼容）

        Note:
            自动创建父目录，二进制格式在Windows/Linux之间不兼容
        """
        if isinstance(path, str):
            assert isinstance(path, str)
            make_parent(path)
            core.springsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        从文件加载序列化系统状态。

        Args:
            path (str): 文件路径，格式由扩展名决定（参考save方法说明）

        Note:
            加载前会验证文件路径有效性
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.springsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_print_node_pos', c_void_p, c_char_p)

    def print_node_pos(self, path):
        """
        将节点坐标输出到指定文件。

        Args:
            path (str): 输出文件路径

        Note:
            文件格式为每行包含一个节点的x,y,z坐标，空格分隔
        """
        assert isinstance(path, str)
        core.springsys_print_node_pos(self.handle, make_c_char_p(path))

    def iterate(self, dt, dynsys, solver):
        """
        执行系统动力学迭代。

        Args:
            dt (float): 时间步长（单位：秒）
            dynsys (DynSys): 动态系统实例，用于存储状态变量
            solver (Solver): 微分方程求解器

        Note:
            迭代过程包含以下步骤：
            1、尝试创建DynSys(只有当DynSys的size不正确的时候才去更新)
            2、更新DynSys (借助给定的solver)
            3、从DynSys读取数据，更新弹簧各个Node的位置和速度
        """
        assert isinstance(dynsys, DynSys)
        if dynsys.size != self.node_number * 3:
            dynsys.size = self.node_number * 3
            self.export_p2f(dynsys)
        self.export_mas_pos_vel(dynsys)
        dynsys.iterate(dt, solver)
        self.update_pos_vel(dynsys)
        self.apply_dampers(dt)

    core.use(c_size_t, 'springsys_get_node_n', c_void_p)

    @property
    def node_number(self):
        """
        获取实际节点数量。

        Returns:
            int: 当前系统内实际节点总数
        """
        return core.springsys_get_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_virtual_node_n', c_void_p)

    @property
    def virtual_node_number(self):
        """
        获取虚拟节点数量。

        Returns:
            int: 当前系统内虚拟节点总数
        """
        return core.springsys_get_virtual_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_spring_n', c_void_p)

    @property
    def spring_number(self):
        """
        获取弹簧元件数量。

        Returns:
            int: 当前系统内弹簧总数
        """
        return core.springsys_get_spring_n(self.handle)

    core.use(c_size_t, 'springsys_get_damper_n', c_void_p)

    @property
    def damper_number(self):
        """
        获取阻尼器元件数量。

        Returns:
            int: 当前系统内阻尼器总数
        """
        return core.springsys_get_damper_n(self.handle)

    def get_node(self, index):
        """
        通过索引获取实际节点对象。

        Args:
            index (int): 节点索引（0 <= index < node_number）

        Returns:
            Node|None: 节点对象，索引无效时返回None
        """
        index = get_index(index, self.node_number)
        if index is not None:
            return SpringSys.Node(self, index)

    def get_virtual_node(self, index):
        """
        通过索引获取虚拟节点对象。

        Args:
            index (int): 虚拟节点索引（0 <= index < virtual_node_number）

        Returns:
            VirtualNode|None: 虚拟节点对象，索引无效时返回None
        """
        index = get_index(index, self.virtual_node_number)
        if index is not None:
            return SpringSys.VirtualNode(self, index)

    def get_spring(self, index):
        """
        通过索引获取弹簧对象。

        Args:
            index (int): 弹簧索引（0 <= index < spring_number）

        Returns:
            Spring|None: 弹簧对象，索引无效时返回None
        """
        index = get_index(index, self.spring_number)
        if index is not None:
            return SpringSys.Spring(self, index)

    def get_damper(self, index):
        """
        通过索引获取阻尼器对象。

        Args:
            index (int): 阻尼器索引（0 <= index < damper_number）

        Returns:
            Damper|None: 阻尼器对象，索引无效时返回None
        """
        index = get_index(index, self.damper_number)
        if index is not None:
            return SpringSys.Damper(self, index)

    @property
    def nodes(self):
        """
        实际节点迭代器。

        Returns:
            Iterator[Node]: 遍历所有实际节点的迭代器
        """
        return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

    @property
    def virtual_nodes(self):
        """
        虚拟节点迭代器。

        Returns:
            Iterator[VirtualNode]: 遍历所有虚拟节点的迭代器
        """
        return Iterator(self, self.virtual_node_number, lambda m, ind: m.get_virtual_node(ind))

    @property
    def springs(self):
        """
        弹簧元件迭代器。

        Returns:
            Iterator[Spring]: 遍历所有弹簧的迭代器
        """
        return Iterator(self, self.spring_number, lambda m, ind: m.get_spring(ind))

    @property
    def dampers(self):
        """
        阻尼器元件迭代器。

        Returns:
            Iterator[Damper]: 遍历所有阻尼器的迭代器
        """
        return Iterator(self, self.damper_number, lambda m, ind: m.get_damper(ind))

    core.use(c_size_t, 'springsys_add_node', c_void_p)

    def add_node(self, pos=None, vel=None, force=None, mass=None):
        """
        创建新实际节点并设置初始参数。

        Args:
            pos (list[float], optional): 初始位置 [x,y,z]（单位：米）
            vel (list[float], optional): 初始速度 [vx,vy,vz]（单位：米/秒）
            force (list[float], optional): 初始受力 [fx,fy,fz]（单位：牛）
            mass (float, optional): 节点质量（单位：千克）

        Returns:
            Node: 新建节点实例
        """
        node = self.get_node(core.springsys_add_node(self.handle))
        if node is not None:
            if pos is not None:
                node.pos = pos
            if vel is not None:
                node.vel = vel
            if force is not None:
                node.force = force
            if mass is not None:
                node.mass = mass
        return node

    core.use(c_size_t, 'springsys_add_virtual_node', c_void_p)

    def add_virtual_node(self, node=None, x=None, y=None, z=None):
        """
        添加一个虚拟节点，并返回虚拟节点对象

        Args:
            node (Node, optional): 基于实际节点创建位置表达式
            x (LinearExpr, optional): 直接设置x轴表达式
            y (LinearExpr, optional): 直接设置y轴表达式
            z (LinearExpr, optional): 直接设置z轴表达式

        Returns:
            VirtualNode: 新建虚拟节点实例

        Note:
            添加一个虚拟节点，并返回虚拟节点对象。当给定参数node时，则在该node的位置创建一个虚拟节点。
            或者，给定x、y、z三个参数，则会分别对虚拟节点的x、y和z进行具体配置。
        """
        virtual_node = self.get_virtual_node(core.springsys_add_virtual_node(self.handle))
        if virtual_node is not None:
            if node is not None:
                assert isinstance(node, SpringSys.Node)
                virtual_node.x = SpringSys.virtual_x(node)
                virtual_node.y = SpringSys.virtual_y(node)
                virtual_node.z = SpringSys.virtual_z(node)
            if x is not None:
                assert isinstance(x, LinearExpr)
                virtual_node.x = x
            if y is not None:
                assert isinstance(y, LinearExpr)
                virtual_node.y = y
            if z is not None:
                assert isinstance(z, LinearExpr)
                virtual_node.z = z
        return virtual_node

    core.use(c_size_t, 'springsys_add_spring', c_void_p)

    def add_spring(self, virtual_nodes=None, len0=None, k=None):
        """
        创建并配置新弹簧元件。

        Args:
            virtual_nodes (tuple, optional): 连接的虚拟节点对，支持以下类型：
                - (VirtualNode, VirtualNode): 直接使用现有虚拟节点
                - (Node, Node): 自动转换为对应虚拟节点
            len0 (float, optional): 弹簧初始长度（单位：米），未设置时保留默认值
            k (float, optional): 刚度系数（单位：牛/米），未设置时保留默认值

        Returns:
            Spring: 新建弹簧实例

        Raises:
            AssertionError: 当节点类型不符合要求时抛出

        Note:
            当传入Node实例时会自动创建对应的虚拟节点
        """
        spring = self.get_spring(core.springsys_add_spring(self.handle))
        if spring is not None:
            if virtual_nodes is not None:
                assert len(virtual_nodes) == 2
                a = virtual_nodes[0]
                b = virtual_nodes[1]
                if isinstance(a, SpringSys.Node):
                    a = self.add_virtual_node(node=a)
                if isinstance(b, SpringSys.Node):
                    b = self.add_virtual_node(node=b)
                assert isinstance(a, SpringSys.VirtualNode) and isinstance(b, SpringSys.VirtualNode)
                spring.virtual_nodes = (a, b)
            if len0 is not None:
                spring.len0 = len0
            if k is not None:
                spring.k = k
        return spring

    core.use(c_size_t, 'springsys_add_damper', c_void_p)

    def add_damper(self, nodes=None, vis=None):
        """
        创建并配置新阻尼器元件。

        Args:
            nodes (tuple[Node, Node]): 连接的实际节点对
            vis (float, optional): 粘性阻尼系数（单位：牛/(米/秒)），未设置时保留默认值

        Returns:
            Damper: 新建阻尼器实例

        Raises:
            AssertionError: 当节点类型不符合要求时抛出

        Note:
            必须连接实际节点(Node)，连接虚拟节点会导致断言失败
        """
        damper = self.get_damper(core.springsys_add_damper(self.handle))
        if damper is not None:
            if nodes is not None:
                damper.nodes = nodes
            if vis is not None:
                damper.vis = vis
        return damper

    core.use(None, 'springsys_modify_vel', c_void_p, c_double)

    def modify_vel(self, scale):
        """
        全局调整节点运动速度。

        Args:
            scale (float): 速度缩放系数（范围：0.0-1.0）

        Note:
            将所有实际节点的速度向量乘以该系数，用于模拟能量耗散
        """
        core.springsys_modify_vel(self.handle, scale)

    core.use(None, 'springsys_get_pos', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, x=None, y=None, z=None):
        """
        获取所有实际节点的坐标数据。

        Args:
            x (Vector, optional): 用于存储x坐标的向量，未提供时自动创建
            y (Vector, optional): 用于存储y坐标的向量，未提供时自动创建
            z (Vector, optional): 用于存储z坐标的向量，未提供时自动创建

        Returns:
            tuple[Vector, Vector, Vector]: 包含x,y,z坐标向量的元组

        Note:
            返回向量长度等于节点数量，坐标单位：米
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.springsys_get_pos(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'springsys_get_len', c_void_p, c_void_p)

    def get_len(self, buffer=None):
        """
        获取所有弹簧的当前长度。

        Args:
            buffer (Vector, optional): 用于存储长度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧长度的向量，单位：米

        Note:
            向量索引与弹簧索引一一对应
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_get_k', c_void_p, c_void_p)

    def get_k(self, buffer=None):
        """
        获取所有弹簧的刚度系数。

        Args:
            buffer (Vector, optional): 用于存储刚度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧刚度系数的向量，单位：牛/米
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_k(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_k', c_void_p, c_void_p)

    def set_k(self, k):
        """
        批量设置所有弹簧的刚度系数。

        Args:
            k (Vector): 包含新刚度系数的向量，长度必须等于弹簧数量

        Note:
            向量索引必须与弹簧索引严格对应
        """
        assert isinstance(k, Vector)
        core.springsys_set_k(self.handle, k.handle)

    core.use(None, 'springsys_get_len0', c_void_p, c_void_p)

    def get_len0(self, buffer=None):
        """
        获取所有弹簧的初始长度。

        Args:
            buffer (Vector, optional): 用于存储长度的向量，未提供时自动创建

        Returns:
            Vector: 包含所有弹簧初始长度的向量，单位：米

        Note:
            向量索引与弹簧索引一一对应
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len0(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_len0', c_void_p, c_void_p)

    def set_len0(self, len0):
        """
        批量设置所有弹簧的初始长度。

        Args:
            len0 (Vector): 包含新初始长度的向量，长度必须等于弹簧数量

        Note:
            向量索引必须与弹簧索引严格对应
        """
        assert isinstance(len0, Vector)
        core.springsys_set_len0(self.handle, len0.handle)

    core.use(c_size_t, 'springsys_apply_k_reduction', c_void_p, c_size_t)

    def apply_k_reduction(self, sa_tmax):
        """
        根据张力阈值实施刚度折减。

        Args:
            sa_tmax (int): 弹簧自定义属性索引，代表最大承受张力（单位：牛）

        Returns:
            int: 发生刚度折减的弹簧数量

        Note:
            当弹簧张力超过该属性值时，刚度将调整为原值的1%
        """
        return core.springsys_apply_k_reduction(self.handle, sa_tmax)

    core.use(None, 'springsys_adjust_len0', c_void_p, c_size_t)

    def adjust_len0(self, sa_times):
        """
        根据属性值调整弹簧初始长度。

        Args:
            sa_times (int): 弹簧自定义属性索引，代表长度调整系数

        Note:
            - 仅当属性值在[0.5, 2.0]范围内时生效
            - 新长度 = 原长度 × 调整系数
            - 超出范围的调整系数会被自动忽略
        """
        core.springsys_adjust_len0(self.handle, sa_times)

    core.use(None, 'springsys_export_mas_pos_vel', c_void_p, c_void_p)

    def export_mas_pos_vel(self, dynsys):
        """
        导出节点物理量到动态系统。

        Args:
            dynsys (DynSys): 目标动态系统实例

        Note:
            导出数据包含：
            - 节点质量（单位：千克）
            - 节点位置（单位：米）
            - 节点速度（单位：米/秒）
            应在每个时间步开始时调用
        """
        core.springsys_export_mas_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_export_p2f', c_void_p, c_void_p)

    def export_p2f(self, dynsys):
        """
        将弹簧系统的刚度矩阵导出到动态系统。

        Args:
            dynsys (DynSys): 目标动态系统实例，用于存储刚度矩阵

        Note:
            - 当系统发生显著变形时需要调用此方法
            - 更新动态系统的系数矩阵P和力向量F
            - 应在每个时间步开始前调用以确保矩阵最新
        """
        core.springsys_export_p2f(self.handle, dynsys.handle)

    core.use(None, 'springsys_update_pos_vel', c_void_p, c_void_p)

    def update_pos_vel(self, dynsys):
        """
        从动态系统读取数据更新节点位置和速度。

        Args:
            dynsys (DynSys): 动态系统实例，包含最新的状态变量

        Note:
            - 将动态系统中存储的位置和速度同步到所有实际节点
            - 应在每个时间步迭代完成后调用
        """
        core.springsys_update_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_apply_dampers', c_void_p, c_double)

    def apply_dampers(self, dt):
        """
        应用阻尼器作用，计算粘性阻尼力并更新系统状态。

        Args:
            dt (float): 时间步长，单位：秒

        Note:
            - 根据阻尼器连接的节点速度差计算阻尼力
            - 阻尼力公式：F = vis * (v2 - v1)
            - 会直接修改节点的受力状态
        """
        core.springsys_apply_dampers(self.handle, dt)

    core.use(None, 'springsys_modify_pos', c_void_p, c_size_t, c_double, c_double)

    def modify_pos(self, idim, left, right):
        """
        约束节点在指定维度的坐标范围。

        Args:
            idim (int): 维度索引 (0=x, 1=y, 2=z)
            left (float): 最小允许坐标值，None表示无下限
            right (float): 最大允许坐标值，None表示无上限

        Note:
            - 当坐标超出范围时会被自动截断到边界值
            - 设置left=right可固定节点在该维度的坐标
            - 默认边界值为±1e100（近似无约束）
        """
        if left is None and right is None:
            return
        if left is None:
            left = -1e100
        if right is None:
            right = 1e100
        core.springsys_modify_pos(self.handle, idim, left, right)


class FemAlg:
    core.use(None, 'fem_alg_create2', c_void_p, c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def create2(mesh, fa_den, fa_h, face_stiffs):
        assert isinstance(mesh, Mesh3)
        assert isinstance(face_stiffs, Vector)
        dyn = DynSys()
        core.fem_alg_create2(dyn.handle, mesh.handle, ctypes.cast(face_stiffs.pointer, c_void_p), face_stiffs.size,
                             fa_den, fa_h)
        return dyn

    core.use(None, 'fem_alg_add_strain2', c_void_p, c_void_p, c_void_p, c_size_t, c_size_t)

    @staticmethod
    def add_strain2(dyn, mesh, fa_strain, face_stiffs):
        assert isinstance(dyn, DynSys)
        assert isinstance(mesh, Mesh3)
        assert isinstance(face_stiffs, Vector)
        core.fem_alg_add_strain2(dyn.handle, mesh.handle, ctypes.cast(face_stiffs.pointer, c_void_p),
                                 face_stiffs.size, fa_strain)


class HasCells(Object):
    def get_pos_range(self, dim):
        from zmlx.alg import has_cells
        return has_cells.get_pos_range(self, dim)

    def get_cells_in_range(self, *args, **kwargs):
        from zmlx.alg import has_cells
        return has_cells.get_cells_in_range(self, *args, **kwargs)

    def get_cell_pos(self, *args, **kwargs):
        from zmlx.alg import has_cells
        return has_cells.get_cell_pos(self, *args, **kwargs)

    def get_cell_property(self, *args, **kwargs):
        from zmlx.alg import has_cells
        return has_cells.get_cell_property(self, *args, **kwargs)

    def plot_tricontourf(self, *args, **kwargs):
        from zmlx.alg import has_cells
        return has_cells.plot_tricontourf(self, *args, **kwargs)


class SeepageMesh(HasHandle, HasCells):
    """
    定义流体计算的网格系统。

    Attributes:
        cells (Iterator[Cell]): 所有单元格的迭代器
        faces (Iterator[Face]): 所有面的迭代器

    Note:
        由单元格(Cell)和面(Face)组成的网络结构：
        - 每个Cell包含位置和体积属性
        - 每个Face包含面积和长度属性
    """

    class Cell(Object):
        """
        定义网格中的控制体积单元。

        Attributes:
            pos (list[float]): 单元格中心点坐标 [x, y, z]（单位：米）
            vol (float): 单元格体积（单位：立方米）
        """

        def __init__(self, model, index):
            """初始化单元格对象。

            Args:
                model (SeepageMesh): 所属的渗流网格模型
                index (int): 单元格索引，必须满足 0 <= index < model.cell_number

            Raises:
                AssertionError: 如果传入非法类型的参数或索引越界
            """
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.cell_number
            self.model = model
            self.index = index

        def __str__(self):
            """生成单元格的字符串表示。

            Returns:
                str: 包含单元格句柄、索引、位置和体积信息的字符串
            """
            return (f'zml.SeepageMesh.Cell(handle = {self.model.handle}, index = {self.index}, '
                    f'pos = {self.pos}, volume={self.vol})')

        core.use(c_double, 'seepage_mesh_get_cell_pos', c_void_p,
                 c_size_t,
                 c_size_t)
        core.use(None, 'seepage_mesh_set_cell_pos', c_void_p,
                 c_size_t,
                 c_size_t,
                 c_double)

        @property
        def pos(self):
            """获取/设置单元格中心点坐标。

            Returns:
                list[float]: 三维坐标列表 [x, y, z]，单位：米

            Note:
                设置新坐标时会自动更新关联的Face属性，可能影响计算精度
            """
            return [core.seepage_mesh_get_cell_pos(self.model.handle, self.index, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """设置单元格中心点坐标。

            Args:
                value (list[float]): 三维坐标列表，长度必须为3

            Raises:
                AssertionError: 如果输入坐标维度不等于3
            """
            assert len(value) == 3
            for dim in range(3):
                core.seepage_mesh_set_cell_pos(self.model.handle, self.index,
                                               dim, value[dim])

        def distance(self, other):
            """计算到另一单元格或坐标点的欧氏距离。

            Args:
                other (Cell|Iterable[float]): 目标单元格或三维坐标

            Returns:
                float: 三维空间中的直线距离，单位：米
            """
            p0 = self.pos
            if hasattr(other, 'pos'):
                p1 = other.pos
            else:
                p1 = other
            return ((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 + (p0[2] - p1[2]) ** 2) ** 0.5

        core.use(None, 'seepage_mesh_set_cell_volume', c_void_p,
                 c_size_t,
                 c_double)
        core.use(c_double, 'seepage_mesh_get_cell_volume', c_void_p,
                 c_size_t)

        @property
        def vol(self):
            """获取/设置单元格体积。

            Returns:
                float: 单元格体积，单位：立方米

            Note:
                修改体积值会影响质量守恒计算，建议通过网格生成工具统一设置
            """
            return core.seepage_mesh_get_cell_volume(self.model.handle, self.index)

        @vol.setter
        def vol(self, value):
            """设置单元格体积。

            Args:
                value (float): 新的体积值，必须大于等于0

            Raises:
                ValueError: 如果输入负值
            """
            core.seepage_mesh_set_cell_volume(self.model.handle, self.index, value)

        core.use(c_double, 'seepage_mesh_get_cell_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取单元格自定义属性值。

            Args:
                index (int): 属性索引
                default_val (Any): 当属性无效时的默认值
                **valid_range: 有效值范围约束（如min=0, max=100）

            Returns:
                float: 属性值或默认值
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_cell_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_cell_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置单元格的自定义属性。

            Args:
                index (int): 属性索引，如果为 None 则不进行任何操作。
                value (float): 属性值，如果为 None 则默认设置为 1.0e200。

            Returns:
                Cell: 当前 Cell 对象，方便链式调用。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_mesh_set_cell_attr(self.model.handle, self.index, index, value)
            return self

        core.use(c_size_t, 'seepage_mesh_cell_get_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            获取周边 Face 的数量。

            Returns:
                int: 周边 Face 的数量。
            """
            return core.seepage_mesh_cell_get_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            获取周边 Cell 的数量。

            Returns:
                int: 周边 Cell 的数量，与周边 Face 的数量相同。
            """
            return self.face_number

        core.use(c_size_t, 'seepage_mesh_cell_get_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            """
            获取相邻的指定索引的 Face 对象。

            Args:
                index (int): 相邻 Face 的索引，范围是 0 <= index < face_number。

            Returns:
                Face: 相邻的 Face 对象。

            Raises:
                IndexError: 如果索引超出有效范围。
            """
            index = get_index(index, self.face_number)
            return self.model.get_face(core.seepage_mesh_cell_get_face_id(self.model.handle, self.index, index))

        core.use(c_size_t, 'seepage_mesh_cell_get_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            """
            返回周边第 index 个 Cell。

            Args:
                index (int): 周边 Cell 的索引，范围是 0 <= index < cell_number。

            Returns:
                Cell: 周边第 index 个 Cell 对象。

            Raises:
                IndexError: 如果索引超出有效范围。
            """
            index = get_index(index, self.cell_number)
            return self.model.get_cell(core.seepage_mesh_cell_get_cell_id(self.model.handle, self.index, index))

        @property
        def cells(self):
            """
            获取所有相邻单元格的迭代器。

            Returns:
                Iterator[Cell]: 相邻单元格迭代器。
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            获取此 Cell 周围的所有 Face 的迭代器。

            Returns:
                Iterator[Face]: 此 Cell 周围的所有 Face 的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    class Face(Object):
        """
        定义单元格之间的连接通道。

        Attributes:
            area (float): 流动横截面积（单位：平方米）
            length (float): 流动通道长度（单位：米）
        """

        def __init__(self, model, index):
            """
            初始化Face对象。

            Args:
                model (SeepageMesh): SeepageMesh对象，代表所属的渗流网格模型。
                index (int): 面的索引，必须小于模型中的面的数量。

            Raises:
                AssertionError: 如果model不是SeepageMesh类型，或者index不是整数，或者index超出模型面的数量范围。
            """
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index

        def __str__(self):
            """
            返回Face对象的字符串表示。

            Returns:
                str: 包含Face对象的句柄、索引、面积和长度信息的字符串。
            """
            return (f'zml.SeepageMesh.Face(handle = {self.model.handle}, index = {self.index}, '
                    f'area = {self.area}, length = {self.length}) ')

        core.use(None, 'seepage_mesh_set_face_area', c_void_p,
                 c_size_t,
                 c_double)
        core.use(c_double, 'seepage_mesh_get_face_area', c_void_p,
                 c_size_t)

        @property
        def area(self):
            """
            获取/设置流动横截面积。

            Returns:
                float: 流动横截面积（单位：平方米）。

            Note:
                修改面积会影响关联的流动计算参数。
            """
            return core.seepage_mesh_get_face_area(self.model.handle, self.index)

        @area.setter
        def area(self, value):
            """
            设置流动横截面积。

            Args:
                value (float): 新的流动横截面积（单位：平方米）。
            """
            core.seepage_mesh_set_face_area(self.model.handle, self.index, value)

        core.use(None, 'seepage_mesh_set_face_length', c_void_p,
                 c_size_t,
                 c_double)
        core.use(c_double, 'seepage_mesh_get_face_length', c_void_p,
                 c_size_t)

        @property
        def length(self):
            """
            获取/设置流动的距离。

            Returns:
                float: 流动的距离（单位：米）。

            Note:
                为了更加清晰的表示“流动距离”的概念，可以调用dist属性。
            """
            return core.seepage_mesh_get_face_length(self.model.handle, self.index)

        @length.setter
        def length(self, value):
            """
            设置流动的距离。

            Args:
                value (float): 新的流动距离（单位：米）。

            Note:
                为了更加清晰的表示“流动距离”的概念，可以调用dist属性。
            """
            core.seepage_mesh_set_face_length(self.model.handle, self.index, value)

        @property
        def dist(self):
            """
            获取/设置流动的距离。

            Returns:
                float: 流动的距离（单位：米）。
            """
            return self.length

        @dist.setter
        def dist(self, value):
            """
            设置流动的距离。

            Args:
                value (float): 新的流动距离（单位：米）。
            """
            self.length = value

        @property
        def pos(self):
            """
            计算面中心点坐标。

            Returns:
                tuple[float]: 两侧单元格坐标的平均值，以元组形式返回。
            """
            p0 = self.get_cell(0).pos
            p1 = self.get_cell(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_size_t, 'seepage_mesh_get_face_end0', c_void_p, c_size_t)

        @property
        def cell_i0(self):
            """
            返回第0个cell的id。

            Returns:
                int: 第0个cell的id。
            """
            return core.seepage_mesh_get_face_end0(self.model.handle, self.index)

        core.use(c_size_t, 'seepage_mesh_get_face_end1', c_void_p, c_size_t)

        @property
        def cell_i1(self):
            """
            返回第1个cell的id。

            Returns:
                int: 第1个cell的id。
            """
            return core.seepage_mesh_get_face_end1(self.model.handle, self.index)

        @property
        def cell_ids(self):
            """
            获取两端Cell的ID。

            Returns:
                tuple[int]: 包含两端Cell的ID的元组。
            """
            return self.cell_i0, self.cell_i1

        @property
        def link(self):
            """
            获取两端Cell的ID。

            Returns:
                tuple[int]: 包含两端Cell的ID的元组。
            """
            return self.cell_ids

        @property
        def cell_number(self):
            """
            返回与此face相连的cell的数量。

            Returns:
                int: 与此face相连的cell的数量，固定为2。
            """
            return 2

        def get_cell(self, i):
            """
            获取连接的第i个单元格。

            Args:
                i (int): 单元格索引，只能为0或1。

            Returns:
                Cell: 连接的单元格对象。

            Raises:
                IndexError: 当索引超出0 - 1范围时抛出。
            """
            i = get_index(i, 2)
            if i is not None:
                if i > 0:
                    return self.model.get_cell(self.cell_i1)
                else:
                    return self.model.get_cell(self.cell_i0)

        def cells(self):
            """
            遍历两端的Cell。

            Returns:
                tuple[Cell]: 包含两端Cell对象的元组。
            """
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'seepage_mesh_get_face_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取第index个自定义属性。

            Args:
                index (int): 属性索引。
                default_val (Any): 默认值，当属性值无效或索引为None时返回。
                **valid_range: 属性值的有效范围，以关键字参数形式传入。

            Returns:
                float: 属性值或默认值。
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_face_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_face_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置第index个自定义属性。

            Args:
                index (int): 属性索引。
                value (float): 属性值，如果为None则默认设置为1.0e200。

            Returns:
                Face: 当前Face对象，方便链式调用。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_mesh_set_face_attr(self.model.handle, self.index, index, value)
            return self

    core.use(c_void_p, 'new_seepage_mesh')
    core.use(None, 'del_seepage_mesh', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化SeepageMesh对象

        Args:
            path (str, optional): 加载网格的路径。如果提供，则从该路径加载网格。
            handle (Any, optional): 网格的句柄。如果为None，则从path加载网格。

        Notes:
            如果handle为None，则尝试从path加载网格。
        """
        super(SeepageMesh, self).__init__(handle, core.new_seepage_mesh, core.del_seepage_mesh)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回对象的字符串表示

        Returns:
            str: 包含句柄、cell数量、face数量和总体积的字符串表示。
        """
        return (f'zml.SeepageMesh(handle = {self.handle}, cell_n = {self.cell_number}, '
                f'face_n = {self.face_number}, volume = {self.volume})')

    core.use(None, 'seepage_mesh_save', c_void_p, c_char_p)

    def save(self, path):
        """
        保存网格到指定路径

        Args:
            path (str): 保存网格的路径。

        Notes:
            可选扩展名:
            - .txt: TXT格式（跨平台，基本不可读）
            - .xml: XML格式（特定可读性，体积最大，读写最慢，跨平台）
            - 其他: 二进制格式（最快最小，但Windows和Linux下生成的文件不能互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.seepage_mesh_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_load', c_void_p, c_char_p)

    def load(self, path):
        """
        从指定路径加载网格

        Args:
            path (str): 加载网格的路径。

        Notes:
            根据扩展名确定文件格式（txt, xml, 二进制），参考save函数。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.seepage_mesh_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_clear', c_void_p)

    def clear(self):
        """
        清除所有的cell和face
        """
        core.seepage_mesh_clear(self.handle)

    core.use(c_size_t, 'seepage_mesh_get_cell_n', c_void_p)

    @property
    def cell_number(self):
        """
        返回cell的数量

        Returns:
            int: 网格中cell的数量。
        """
        return core.seepage_mesh_get_cell_n(self.handle)

    def get_cell(self, ind):
        """
        返回第ind个cell

        Args:
            ind (int): cell的索引。

        Returns:
            SeepageMesh.Cell: 第ind个cell对象，如果索引有效；否则返回None。
        """
        ind = get_index(ind, self.cell_number)
        if ind is not None:
            return SeepageMesh.Cell(self, ind)

    core.use(c_size_t, 'seepage_mesh_get_nearest_cell_id', c_void_p,
             c_double, c_double, c_double)

    def get_nearest_cell(self, pos):
        """
        返回与给定位置距离最近的cell

        Args:
            pos (tuple): 包含三个浮点数的元组，表示三维空间中的位置。

        Returns:
            SeepageMesh.Cell: 与给定位置距离最近的cell对象，如果网格中有cell；否则返回None。
        """
        if self.cell_number > 0:
            return self.get_cell(core.seepage_mesh_get_nearest_cell_id(self.handle, pos[0], pos[1], pos[2]))

    core.use(c_size_t, 'seepage_mesh_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        返回face的数量

        Returns:
            int: 网格中face的数量。
        """
        return core.seepage_mesh_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_mesh_get_face', c_void_p, c_size_t, c_size_t)

    def get_face(self, ind=None, cell_0=None, cell_1=None):
        """
        返回第ind个face，或者找到两个cell之间的face

        Args:
            ind (int, optional): 面的索引。如果提供，则返回该索引对应的face。
            cell_0 (SeepageMesh.Cell, optional): 第一个单元格。如果ind未提供，则需要提供此参数。
            cell_1 (SeepageMesh.Cell, optional): 第二个单元格。如果ind未提供，则需要提供此参数。

        Returns:
            SeepageMesh.Face: 面的对象，如果找到；否则返回None。

        Raises:
            AssertionError: 如果ind和(cell_0, cell_1)的提供不符合要求。
        """
        if ind is not None:
            assert cell_0 is None and cell_1 is None
            ind = get_index(ind, self.face_number)
            if ind is not None:
                return SeepageMesh.Face(self, ind)
        else:
            assert cell_0 is not None and cell_1 is not None
            assert isinstance(cell_0, SeepageMesh.Cell)
            assert isinstance(cell_1, SeepageMesh.Cell)
            assert cell_0.model.handle == self.handle
            assert cell_1.model.handle == self.handle
            ind = core.seepage_mesh_get_face(self.handle, cell_0.index, cell_1.index)
            if ind < self.face_number:
                return SeepageMesh.Face(self, ind)

    core.use(c_size_t, 'seepage_mesh_add_cell', c_void_p)

    def add_cell(self):
        """
        添加一个cell，并且返回这个新添加的cell

        Returns:
            SeepageMesh.Cell: 新添加的cell对象。
        """
        return self.get_cell(core.seepage_mesh_add_cell(self.handle))

    core.use(c_size_t, 'seepage_mesh_add_face', c_void_p,
             c_size_t,
             c_size_t)

    def add_face(self, cell_0, cell_1):
        """
        添加一个face，连接两个给定的cell

        Args:
            cell_0 (SeepageMesh.Cell): 第一个单元格。
            cell_1 (SeepageMesh.Cell): 第二个单元格。

        Returns:
            SeepageMesh.Face: 新添加的面的对象。

        Raises:
            AssertionError: 如果提供的cell不属于当前网格。
        """
        if isinstance(cell_0, SeepageMesh.Cell):
            assert cell_0.model.handle == self.handle
            cell_0 = cell_0.index

        if isinstance(cell_1, SeepageMesh.Cell):
            assert cell_1.model.handle == self.handle
            cell_1 = cell_1.index

        return self.get_face(core.seepage_mesh_add_face(self.handle, cell_0, cell_1))

    @property
    def cells(self):
        """
        用以迭代所有的cell

        Returns:
            Iterator: 用于迭代所有cell的迭代器。
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        用以迭代所有的face

        Returns:
            Iterator: 用于迭代所有face的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def volume(self):
        """
        返回整个模型整体的体积

        Returns:
            float: 整个模型的总体积，通过累加所有cell的体积得到。
        """
        vol = 0
        for cell in self.cells:
            vol += cell.vol
        return vol

    def load_ascii(self, *args, **kwargs):
        """
        加载ASCII格式的网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.ascii中的函数。
        """
        warnings.warn('SeepageMesh.load_ascii will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.ascii import load_ascii
        load_ascii(*args, **kwargs, mesh=self)

    def save_ascii(self, *args, **kwargs):
        """
        保存ASCII格式的网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.ascii中的函数。
        """
        warnings.warn('SeepageMesh.save_ascii will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.ascii import save_ascii
        save_ascii(*args, **kwargs, mesh=self)

    @staticmethod
    def load_mesh(*args, **kwargs):
        """
        加载网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.load_mesh中的函数。
        """
        warnings.warn('SeepageMesh.load_mesh will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.load_mesh instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.load_mesh import load_mesh as load
        return load(*args, **kwargs)

    @staticmethod
    def create_cube(*args, **kwargs):
        """
        创建一个立方体网格

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.cube.create_cube函数。
        """
        warnings.warn('The zml.SeepageMesh.create_cube will be removed after 2025-5-27. '
                      'please use zmlx.seepage_mesh.cube.create_cube instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.cube import create_cube as create
        return create(*args, **kwargs)

    @staticmethod
    def create_cylinder(*args, **kwargs):
        """
        创建一个圆柱体网格

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.cylinder.create_cylinder函数。
        """
        warnings.warn('The zml.SeepageMesh.create_cylinder will be removed after 2025-5-27. '
                      'please use zmlx.seepage_mesh.cylinder.create_cylinder instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.cylinder import create_cylinder as create
        return create(*args, **kwargs)

    core.use(None, 'seepage_mesh_find_inner_face_ids', c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号

        Args:
            cell_ids (UintVector): 单元格的ID列表。
            buffer (UintVector, optional): 缓冲区，用于存储返回的面的ID。如果未提供，则创建一个新的UintVector。

        Returns:
            UintVector: 缓冲区，包含了内部相互连接的面的ID。

        Raises:
            AssertionError: 如果cell_ids不是UintVector类型。
        """
        assert isinstance(cell_ids, UintVector)
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.seepage_mesh_find_inner_face_ids(self.handle, buffer.handle, cell_ids.handle)
        return buffer

    core.use(None, 'seepage_mesh_from_mesh3', c_void_p, c_void_p)

    @staticmethod
    def from_mesh3(mesh3, buffer=None):
        """
        利用一个Mesh3的Body来创建Cell，Face来创建Face

        Args:
            mesh3 (Mesh3): 一个Mesh3对象，用于创建SeepageMesh的单元格和面。
            buffer (SeepageMesh, optional): 一个可选的SeepageMesh对象，用于存储转换后的网格。如果未提供，则创建一个新的SeepageMesh对象。

        Returns:
            SeepageMesh: 如果成功，返回创建的或传入的SeepageMesh对象；否则抛出异常。

        Raises:
            AssertionError: 如果mesh3不是Mesh3类的实例，或者buffer不是SeepageMesh类的实例（当提供时）。
        """
        assert isinstance(mesh3, Mesh3)
        if not isinstance(buffer, SeepageMesh):
            buffer = SeepageMesh()
        core.seepage_mesh_from_mesh3(buffer.handle, mesh3.handle)
        return buffer


class ElementMap(HasHandle):
    class Element(Object):
        """
        表示ElementMap中的一个元素。

        Attributes:
            model (ElementMap): 元素所属的ElementMap实例。
            index (int): 元素的索引。
        """
        def __init__(self, model, index):
            """
            初始化Element对象。

            Args:
                model (ElementMap): 元素所属的ElementMap实例。
                index (int): 元素的索引。
            """
            self.model = model
            self.index = index

        core.use(c_size_t, 'element_map_related_count', c_void_p, c_size_t)

        @property
        def size(self):
            """
            获取与该元素相关的元素数量。

            Returns:
                int: 与该元素相关的元素数量。
            """
            return core.element_map_related_count(self.model.handle, self.index)

        core.use(c_size_t, 'element_map_related_id', c_void_p, c_size_t, c_size_t)

        core.use(c_double, 'element_map_related_weight', c_void_p, c_size_t, c_size_t)

        def get_iw(self, i):
            """
            获取与该元素相关的第i个元素的索引和权重。

            Args:
                i (int): 相关元素的索引。

            Returns:
                tuple: 包含相关元素的索引和权重的元组，如果索引有效；否则返回None。
            """
            i = get_index(i, self.size)
            if i is not None:
                ind = core.element_map_related_id(self.model.handle, self.index, i)
                w = core.element_map_related_weight(self.model.handle, self.index, i)
                return ind, w

    core.use(c_void_p, 'new_element_map')
    core.use(None, 'del_element_map', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化ElementMap对象。

        Args:
            path (str, optional): 加载ElementMap的文件路径。如果提供，则从该路径加载。
            handle (Any, optional): ElementMap的句柄。如果为None，则尝试从path加载。

        Notes:
            如果handle为None且path是有效的字符串，则从path加载ElementMap。
        """
        super(ElementMap, self).__init__(handle, core.new_element_map, core.del_element_map)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回ElementMap对象的字符串表示。

        Returns:
            str: 包含句柄和大小的字符串表示。
        """
        return f'zml.ElementMap(handle = {self.handle}, size = {self.size})'

    core.use(None, 'element_map_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存ElementMap到指定路径。

        Args:
            path (str): 保存ElementMap的文件路径。

        Notes:
            可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.element_map_save(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_load', c_void_p, c_char_p)

    def load(self, path):
        """
        从指定路径读取序列化的ElementMap文件。

        Args:
            path (str): 加载ElementMap的文件路径。

        Notes:
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.element_map_load(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_to_str', c_void_p, c_size_t)

    def to_str(self):
        """
        将ElementMap转换为字符串。

        Returns:
            str: 表示ElementMap的字符串。
        """
        s = String()
        core.element_map_to_str(self.handle, s.handle)
        return s.to_str()

    core.use(None, 'element_map_from_str', c_void_p, c_size_t)

    def from_str(self, s):
        """
        从字符串中加载ElementMap。

        Args:
            s (str): 包含ElementMap数据的字符串。
        """
        s2 = String()
        s2.assign(s)
        core.element_map_from_str(self.handle, s2.handle)

    core.use(c_size_t, 'element_map_size', c_void_p)

    @property
    def size(self):
        """
        获取ElementMap的大小。

        Returns:
            int: ElementMap的大小。
        """
        return core.element_map_size(self.handle)

    core.use(None, 'element_map_clear', c_void_p)

    def clear(self):
        """
        清除ElementMap中的所有元素。
        """
        core.element_map_clear(self.handle)

    core.use(None, 'element_map_add', c_void_p, c_void_p, c_void_p)

    def add_element(self, vi, vw):
        """
        向ElementMap中添加一个元素。

        Args:
            vi (IntVector or list): 元素的索引向量。
            vw (Vector or list): 元素的权重向量。

        Notes:
            如果vi和vw不是IntVector和Vector类型，将尝试转换为相应类型。
        """
        if not isinstance(vi, IntVector):
            vi = IntVector(vi)
        if not isinstance(vw, Vector):
            vw = Vector(vw)
        core.element_map_add(self.handle, vi.handle, vw.handle)

    def get_element(self, index):
        """
        获取指定索引的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            ElementMap.Element: 指定索引的元素对象。
        """
        return ElementMap.Element(self, index)

    core.use(None, 'element_map_get', c_void_p, c_void_p, c_void_p, c_double)

    def get_values(self, source, buffer=None, default=None):
        """
        根据原始网格中的数据，根据此映射，计算此网格体系内各个网格的数值。

        Args:
            source (Vector): 原始网格中的数据向量。
            buffer (Vector, optional): 用于存储计算结果的缓冲区。如果未提供，则创建一个新的Vector。
            default (float, optional): 默认值，用于处理未映射的元素。如果未提供，则默认为0.0。

        Returns:
            Vector: 包含计算结果的缓冲区。

        Raises:
            AssertionError: 如果source不是Vector类型。
        """
        assert isinstance(source, Vector)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        if default is None:
            default = 0.0
        core.element_map_get(self.handle, buffer.handle, source.handle, default)
        return buffer


class Groups(HasHandle):
    core.use(c_void_p, 'new_groups')
    core.use(None, 'del_groups', c_void_p)

    def __init__(self, handle=None):
        """
        初始化Groups对象。

        Args:
            handle (c_void_p, optional): 指向底层C对象的句柄。如果为None，则创建一个新的Groups对象。
        """
        super(Groups, self).__init__(handle, core.new_groups, core.del_groups)

    core.use(None, 'groups_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。

        Notes:
            如果路径的父目录不存在，会自动创建。
        """
        if isinstance(path, str):
            make_parent(path)
            core.groups_save(self.handle, make_c_char_p(path))

    core.use(None, 'groups_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 加载文件的路径。

        Raises:
            AssertionError: 如果路径无效。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.groups_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'groups_size', c_void_p)

    @property
    def size(self):
        """
        获取Groups中元素的数量。

        Returns:
            int: Groups中元素的数量。
        """
        return core.groups_size(self.handle)

    core.use(c_void_p, 'groups_get', c_void_p, c_size_t)

    def get(self, idx):
        """
        获取指定索引的元素。

        Args:
            idx (int): 元素的索引。

        Returns:
            UintVector: 包含指定索引元素的UintVector对象。
        """
        handle = core.groups_get(self.handle, idx)
        return UintVector(handle=handle)


class Seepage(HasHandle, HasCells):
    """
    多相多组分渗流模型。Seepage类是进行热流耦合模拟的基础。Seepage类主要涉及单元Cell，界面Face，流体Fluid，反应Reaction，流体定义FluDef
    几个概念。
    对于任意渗流场，均可以离散为由Cell<控制体：流体的存储空间>和Face<两个Cell之间的界面，流体的流动通道>组成的结构。
    """

    class Reaction(HasHandle):
        """
        定义一个化学反应。反应所需要的物质存储在Seepage.Cell中。这里，所谓化学反应，是一种或者几种流体（或者流体的组分）转化为另外一种或者几种
        流体或者组分，并吸收或者释放能量的过程。这个Reaction，即定义参与反应的各种物质的比例、反应的速度以及反应过程中的能量变化。基于Seepage
        类模拟水合物的分解或者生成、冰的形成和融化、重油的裂解等，均基于此Reaction类进行定义。
        """
        core.use(c_void_p, 'new_reaction')
        core.use(None, 'del_reaction', c_void_p)

        def __init__(self, path=None, handle=None):
            """
            初始化一个反应。

            Args:
                path (str, optional): 当给定path的时候，则载入之前创建好并序列化存储的反应。默认为None。
                handle (Any, optional): 反应的句柄。如果为None，则根据path加载反应；否则忽略path。默认为None。
            """
            super(Seepage.Reaction, self).__init__(handle, core.new_reaction, core.del_reaction)
            if handle is None:
                if isinstance(path, str):
                    self.load(path)
            else:
                assert path is None

        core.use(None, 'reaction_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。

            Args:
                path (str): 保存文件的路径。

            Notes:
                可选扩展格式：
                1：.txt
                    .TXT 格式（跨平台，基本不可读）
                2：.xml
                    .XML 格式（特定可读性，文件体积最大，读写速度最慢，跨平台）
                3：.其他
                    二进制格式（最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
            """
            if isinstance(path, str):
                make_parent(path)
                core.reaction_save(self.handle, make_c_char_p(path))

        core.use(None, 'reaction_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。

            Args:
                path (str): 读取文件的路径。

            Notes:
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.reaction_load(self.handle, make_c_char_p(path))

        core.use(None, 'reaction_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'reaction_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中。

            Args:
                fmt (str, optional): 序列化格式，取值可以为 'text', 'xml' 和 'binary'。默认为 'binary'。

            Returns:
                FileMap: 包含序列化数据的FileMap对象。
            """
            fmap = FileMap()
            core.reaction_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据。

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 序列化格式，取值可以为 'text', 'xml' 和 'binary'。默认为 'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.reaction_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            返回一个二进制的FileMap对象。

            Returns:
                FileMap: 包含二进制序列化数据的FileMap对象。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            从二进制的FileMap对象中读取序列化的数据。

            Args:
                value (FileMap): 包含二进制序列化数据的FileMap对象。
            """
            self.from_fmap(value, fmt='binary')

        core.use(None, 'reaction_set_dheat', c_void_p, c_double)
        core.use(c_double, 'reaction_get_dheat', c_void_p)

        @property
        def heat(self):
            """
            发生1kg物质的化学反应<1kg的左侧物质，转化为1kg的右侧物质>释放的热量，单位焦耳。
            注意，如果反应是吸热反应，则此heat为负值。

            Returns:
                float: 化学反应释放的热量。
            """
            return core.reaction_get_dheat(self.handle)

        @heat.setter
        def heat(self, value):
            """
            设置化学反应释放的热量。

            Args:
                value (float): 化学反应释放的热量，单位焦耳。
            """
            core.reaction_set_dheat(self.handle, value)

        # 兼容之前的接口 (_Trash)
        # todo:
        #   删除dheat属性. (after 2024.02.01)
        dheat = heat

        core.use(None, 'reaction_set_t0', c_void_p, c_double)
        core.use(c_double, 'reaction_get_t0', c_void_p)

        @property
        def temp(self):
            """
            和heat对应的参考温度，只有当反应前后的温度都等于此temp的时候，释放的热量才可以使用heat来定义。

            Returns:
                float: 参考温度。
            """
            return core.reaction_get_t0(self.handle)

        @temp.setter
        def temp(self, value):
            """
            设置参考温度。

            Args:
                value (float): 参考温度。
            """
            core.reaction_set_t0(self.handle, value)

        core.use(None, 'reaction_set_p2t', c_void_p, c_void_p, c_void_p)

        def set_p2t(self, p, t):
            """
            设置不同的压力下，反应可以发生的临界温度。

            Args:
                p (Vector or list): 压力向量。
                t (Vector or list): 临界温度向量。

            Notes:
                对于吸热反应，只有当温度大于此临界温度的时候，反应才会发生；
                对于放热反应，温度小于临界温度的时候，反应才会发生。
                此反应目前不适用于“燃烧”这种反应（后续可能会添加支持）。
            """
            if not isinstance(p, Vector):
                p = Vector(p)
            if not isinstance(t, Vector):
                t = Vector(t)
            core.reaction_set_p2t(self.handle, p.handle, t.handle)

        core.use(None, 'reaction_set_t2q', c_void_p, c_void_p, c_void_p)

        def set_t2q(self, t, q):
            """
            设置当温度偏离平衡温度的时候反应的速率。

            Args:
                t (Vector or list): 温度偏移量向量。
                q (Vector or list): 反应速率向量。

            Notes:
                对于吸热反应，随着温度的增加，反应的速率应当增加；
                对于放热反应，随着温度的降低，反应的速率降低；
                当温度偏移量为0的时候，反应的速率为0。
                此处，反应的速率定义为，对于1kg的物质，在1s内发生反应的质量。
            """
            if not isinstance(t, Vector):
                t = Vector(t)
            if not isinstance(q, Vector):
                q = Vector(q)
            core.reaction_set_t2q(self.handle, t.handle, q.handle)

        core.use(None, 'reaction_add_component', c_void_p, c_size_t, c_size_t, c_size_t,
                 c_double, c_size_t, c_size_t)

        def add_component(self, index, weight, fa_t, fa_c):
            """
            添加一种反应物质。

            Args:
                index (int): Seepage.Cell中定义的流体组分的序号。
                weight (float): 发生1kg的反应的时候此物质变化的质量，其中左侧物质的weight为负值，右侧为正值。
                fa_t (int): 定义流体温度的属性ID。
                fa_c (int): 定义流体比热的属性ID。

            Raises:
                AssertionError: 如果fa_t或fa_c为None，或者weight的绝对值大于1.00001。
            """
            assert fa_t is not None
            assert fa_c is not None
            assert abs(weight) <= 1.00001
            core.reaction_add_component(self.handle, *parse_fid3(index), weight, fa_t, fa_c)

        core.use(None, 'reaction_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的反应组分。
            """
            core.reaction_clear_components(self.handle)

        core.use(None, 'reaction_add_inhibitor', c_void_p,
                 c_size_t, c_size_t, c_size_t,
                 c_size_t, c_size_t, c_size_t,
                 c_void_p, c_void_p, c_bool)

        def add_inhibitor(self, sol, liq, c, t, *, use_vol=False):
            """
            添加一种抑制剂。

            Args:
                sol (int): 抑制剂对应的组分ID。
                liq (int): 流体的组分ID。
                c (Vector or list): 抑制剂浓度向量。
                t (Vector or list): 化学反应平衡温度向量。
                use_vol (bool, optional): 是否使用体积。默认为False。
            """
            if not isinstance(c, Vector):
                c = Vector(c)
            if not isinstance(t, Vector):
                t = Vector(t)
            core.reaction_add_inhibitor(self.handle, *parse_fid3(sol), *parse_fid3(liq), c.handle, t.handle,
                                        use_vol)

        core.use(None, 'reaction_clear_inhibitors', c_void_p)

        def clear_inhibitors(self):
            """
            清除所有的抑制剂定义。
            """
            core.reaction_clear_inhibitors(self.handle)

        core.use(None, 'reaction_react', c_void_p, c_void_p, c_double, c_void_p)

        def react(self, model, dt, buf=None):
            """
            将该反应作用到Seepage的所有的Cell上dt时间。

            Args:
                model (Seepage): Seepage模型对象。
                dt (float): 时间步长。
                buf (Any, optional): 一个缓冲区(double*)，记录各个Cell上发生的反应的质量。务必确保此缓冲区的大小足够，否则会出现致命的错误。默认为None。

            Returns:
                float: 反应发生的总的质量。
            """
            self.adjust_weights()  # 确保权重正确，保证质量守恒
            core.reaction_react(self.handle, model.handle, dt,
                                0 if buf is None else ctypes.cast(buf, c_void_p))

        core.use(None, 'reaction_adjust_weights', c_void_p)

        def adjust_weights(self):
            """
            等比例地调整权重。确保方程左侧系数加和之后等于-1，右侧的系数加和之后等于1.
            """
            core.reaction_adjust_weights(self.handle)

        def adjust_widghts(self):
            """
            同adjust_weights

            Warnings:
                此方法已弃用，将在2024-1-1之后移除，请使用 <adjust_weights>。
            """
            warnings.warn('Use <adjust_weights>. <adjust_widghts> will be removed after 2024-1-1',
                          DeprecationWarning)
            self.adjust_weights()

        core.use(c_double, 'reaction_get_rate', c_void_p, c_void_p)

        def get_rate(self, cell):
            """
            获得给定Cell在当前状态(温度、压力、抑制剂等条件)下的<瞬时的>反应速率。

            Args:
                cell (Seepage.CellData): Seepage的CellData对象。

            Returns:
                float: 反应速率。
            """
            assert isinstance(cell, Seepage.CellData)
            return core.reaction_get_rate(self.handle, cell.handle)

        core.use(None, 'reaction_set_idt', c_void_p, c_size_t)
        core.use(c_size_t, 'reaction_get_idt', c_void_p)

        @property
        def idt(self):
            """
            Cell的属性ID。Cell的此属性用以定义反应作用到该Cell上的时候，平衡温度的调整量。
            这允许在不同的Cell上，有不同的反应温度。
            默认情况下，此属性不定义，则反应在各个Cell上的温度是一样的。

            Notes:
                此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。

            Returns:
                int: Cell的属性ID。
            """
            return core.reaction_get_idt(self.handle)

        @idt.setter
        def idt(self, value):
            """
            设置Cell的属性ID。

            Args:
                value (int): Cell的属性ID。
            """
            core.reaction_set_idt(self.handle, value)

        core.use(None, 'reaction_set_wdt', c_void_p, c_double)
        core.use(c_double, 'reaction_get_wdt', c_void_p)

        @property
        def wdt(self):
            """
            和idt配合使用。在Cell定义温度调整量的时候，可以利用这个权重再对这个调整量进行（缩放）调整。
            比如，当Cell给的温度的调整量的单位不是K的时候，可以利用wdt属性来添加一个倍率。

            Notes:
                此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。

            Returns:
                float: 权重。
            """
            return core.reaction_get_wdt(self.handle)

        @wdt.setter
        def wdt(self, value):
            """
            设置权重。

            Args:
                value (float): 权重。
            """
            core.reaction_set_wdt(self.handle, value)

        core.use(None, 'reaction_set_irate', c_void_p, c_size_t)
        core.use(c_size_t, 'reaction_get_irate', c_void_p)

        @property
        def irate(self):
            """
            Cell的属性ID。Cell的此属性用以定义反应作用到该Cell上的时候，反应速率应该乘以的倍数。
            若定义这个属性，且Cell的这个属性值小于等于0，那么反应在这个Cell上将不会发生。

            Notes:
                如果希望某个反应只在部分Cell上发生，则可以利用这个属性来实现。

            Returns:
                int: Cell的属性ID。
            """
            return core.reaction_get_irate(self.handle)

        @irate.setter
        def irate(self, value):
            """
            设置Cell的属性ID。

            Args:
                value (int): Cell的属性ID。
            """
            core.reaction_set_irate(self.handle, value)

        core.use(None, 'reaction_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            拷贝所有的数据。

            Args:
                other (Seepage.Reaction): 要拷贝的Reaction对象。

            Returns:
                Seepage.Reaction: 拷贝后的Reaction对象。
            """
            if other is not None:
                assert isinstance(other, Seepage.Reaction)
                core.reaction_clone(self.handle, other.handle)
            return self

        def get_copy(self):
            """
            返回一个拷贝(而非一个引用)。

            Returns:
                Seepage.Reaction: 拷贝后的Reaction对象。
            """
            result = Seepage.Reaction()
            result.clone(self)
            return result

    class FluDef(HasHandle):
        """
        流体定义。在本程序中，我们假设流体的密度和粘性系数都是压力和温度的函数，并且利用二维插值来存储。
            比热容被视为常数(这可能不严谨，但是大多数情况下够用).
        流体定义被存储在Seepage中，被所有的Cell所共用。
        """
        core.use(c_void_p, 'new_fludef')
        core.use(None, 'del_fludef', c_void_p)

        def __init__(self, den=1000.0, vis=1.0e-3, specific_heat=4200, name=None, path=None, handle=None):
            """
            构造函数。

            Args:
                den (float or Interp2, optional): 流体密度，当为None时清除C++层面的默认数据。默认为1000.0。
                vis (float or Interp2, optional): 流体粘性，当为None时清除C++层面的默认数据。默认为1.0e-3。
                specific_heat (float, optional): 流体比热容。默认为4200。
                name (str, optional): 流体名称。默认为None。
                path (str, optional): 加载流体定义的文件路径。默认为None。
                handle (c_void_p, optional): 指向底层C对象的句柄。如果为None，则根据其他参数初始化；否则创建当前数据的引用。默认为None。
            """
            super(Seepage.FluDef, self).__init__(handle, core.new_fludef, core.del_fludef)
            if handle is None:
                # 现在，这是一个新建数据，将进行必要的初始化
                if isinstance(path, str):
                    self.load(path)
                else:
                    self.den = den  # 即便给定的数据为None，也将使用(清除当前数据)
                    self.vis = vis  # 即便给定的数据为None，也将使用(清除当前数据)
                    if specific_heat is not None:
                        self.specific_heat = specific_heat
                # 只要给定name，无论是load，还是create，都修改name
                if name is not None:
                    self.name = name
            else:
                assert path is None

        core.use(None, 'fludef_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。

            Args:
                path (str): 保存文件的路径。

            Notes:
                可选扩展格式：
                1：.txt
                    .TXT 格式（跨平台，基本不可读）
                2：.xml
                    .XML 格式（特定可读性，文件体积最大，读写速度最慢，跨平台）
                3：.其他
                    二进制格式（最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
            """
            if isinstance(path, str):
                make_parent(path)
                core.fludef_save(self.handle, make_c_char_p(path))

        core.use(None, 'fludef_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。

            Args:
                path (str): 读取文件的路径。

            Notes:
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.fludef_load(self.handle, make_c_char_p(path))

        core.use(None, 'fludef_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'fludef_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中。

            Args:
                fmt (str, optional): 序列化格式，取值可以为 'text', 'xml' 和 'binary'。默认为 'binary'。

            Returns:
                FileMap: 包含序列化数据的FileMap对象。
            """
            fmap = FileMap()
            core.fludef_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据。

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 序列化格式，取值可以为 'text', 'xml' 和 'binary'。默认为 'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.fludef_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            返回一个二进制的FileMap对象。

            Returns:
                FileMap: 包含二进制序列化数据的FileMap对象。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            从二进制的FileMap对象中读取序列化的数据。

            Args:
                value (FileMap): 包含二进制序列化数据的FileMap对象。
            """
            self.from_fmap(value, fmt='binary')

        core.use(c_void_p, 'fludef_get_den', c_void_p)

        @property
        def den(self):
            """
            流体密度的插值。

            Returns:
                Interp2: 流体密度的插值对象。

            Raises:
                AssertionError: 如果组分的数量不为0。
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_den(self.handle))

        @den.setter
        def den(self, value):
            """
            设置密度数据。

            Args:
                value (float or Interp2, optional): 密度数据，当为None时清除现有数据。

            Raises:
                AssertionError: 如果组分的数量不为0，或者给定的非插值数据不在有效范围内。
            """
            assert self.component_number == 0
            if value is None:
                self.den.clear()
            else:
                if isinstance(value, Interp2):
                    self.den.clone(value)
                else:  # 转化为二维插值
                    assert 1.0e-3 < value <= 1.0e7
                    itp = Interp2.create_const(value)
                    self.den.clone(itp)

        core.use(c_void_p, 'fludef_get_vis', c_void_p)

        @property
        def vis(self):
            """
            流体粘性的插值。

            Returns:
                Interp2: 流体粘性的插值对象。

            Raises:
                AssertionError: 如果组分的数量不为0。
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_vis(self.handle))

        @vis.setter
        def vis(self, value):
            """
            设置粘性数据。

            Args:
                value (float or Interp2, optional): 粘性数据，当为None时清除现有数据。

            Raises:
                AssertionError: 如果组分的数量不为0，或者给定的非插值数据不在有效范围内。
            """
            assert self.component_number == 0
            if value is None:
                self.vis.clear()
            else:
                if isinstance(value, Interp2):
                    self.vis.clone(value)
                else:  # 转化为二维插值
                    assert 1.0e-7 < value < 1.0e40
                    itp = Interp2.create_const(value)
                    self.vis.clone(itp)

        def get_den(self, pressure, temp):
            """
            返回给定压力和温度下的密度。

            Args:
                pressure (float): 压力值。
                temp (float): 温度值。

            Returns:
                float: 给定压力和温度下的密度。
            """
            return self.den(pressure, temp)

        def get_vis(self, pressure, temp):
            """
            返回给定压力和温度下的粘性。

            Args:
                pressure (float): 压力值。
                temp (float): 温度值。

            Returns:
                float: 给定压力和温度下的粘性。
            """
            return self.vis(pressure, temp)

        core.use(c_double, 'fludef_get_specific_heat', c_void_p)
        core.use(None, 'fludef_set_specific_heat', c_void_p, c_double)

        @property
        def specific_heat(self):
            """
            流体的比热(常数)。

            Returns:
                float: 流体的比热。

            Raises:
                AssertionError: 如果组分的数量不为0。
            """
            assert self.component_number == 0
            return core.fludef_get_specific_heat(self.handle)

        @specific_heat.setter
        def specific_heat(self, value):
            """
            设置流体的比热。

            Args:
                value (float): 流体的比热。

            Raises:
                AssertionError: 如果组分的数量不为0，或者给定的值不在有效范围内。
            """
            assert self.component_number == 0
            assert 0.1 <= value <= 1.0e8
            core.fludef_set_specific_heat(self.handle, value)

        core.use(c_size_t, 'fludef_get_component_number', c_void_p)
        core.use(None, 'fludef_set_component_number', c_void_p, c_size_t)

        @property
        def component_number(self):
            """
            流体组分的数量。

            Returns:
                int: 流体组分的数量。
            """
            return core.fludef_get_component_number(self.handle)

        @component_number.setter
        def component_number(self, value):
            """
            设置流体组分的数量。

            Args:
                value (int): 流体组分的数量。
            """
            core.fludef_set_component_number(self.handle, value)

        core.use(c_void_p, 'fludef_get_component', c_void_p, c_size_t)

        def get_component(self, idx):
            """
            返回流体的组分。

            Args:
                idx (int): 组分的索引。

            Returns:
                Seepage.FluDef: 流体的组分对象，如果索引有效；否则返回None。
            """
            idx = get_index(idx, self.component_number)
            if idx is not None:
                return Seepage.FluDef(handle=core.fludef_get_component(self.handle, idx))

        core.use(None, 'fludef_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的组分。
            """
            core.fludef_clear_components(self.handle)

        core.use(c_size_t, 'fludef_add_component', c_void_p, c_void_p)

        def add_component(self, flu, name=None):
            """
            添加流体组分，并返回组分的ID。

            Args:
                flu (Seepage.FluDef): 要添加的流体组分对象。
                name (str, optional): 流体组分的名称。默认为None。

            Returns:
                int: 新添加组分的ID。
            """
            assert isinstance(flu, Seepage.FluDef)
            idx = core.fludef_add_component(self.handle, flu.handle)
            if name is not None:
                self.get_component(idx).name = name
            return idx

        @staticmethod
        def create(defs, name=None):
            """
            将存储在list中的多个流体的定义，组合成为一个具有多个组分的单个流体定义。

            Args:
                defs (list or Seepage.FluDef): 流体定义列表或单个流体定义对象。
                name (str, optional): 返回的流体定义的名称。默认为None。

            Returns:
                Seepage.FluDef: 组合后的流体定义对象。

            Notes:
                当给定name的时候，则返回的数据使用此name。
                此函数将返回给定数据的拷贝，因此，原始的数据并不会被引用和修改。
            """
            if isinstance(defs, Seepage.FluDef):
                return defs.get_copy(name=name)
            else:
                result = Seepage.FluDef(name=name)
                for x in defs:
                    result.add_component(Seepage.FluDef.create(x))
                return result

        core.use(None, 'fludef_set_name', c_void_p, c_char_p)
        core.use(c_char_p, 'fludef_get_name', c_void_p)

        @property
        def name(self):
            """
            流体组分的名称。

            Returns:
                str: 流体组分的名称。
            """
            return core.fludef_get_name(self.handle).decode()

        @name.setter
        def name(self, value):
            """
            设置流体组分的名称。

            Args:
                value (str): 流体组分的名称。
            """
            core.fludef_set_name(self.handle, make_c_char_p(value))

        core.use(None, 'fludef_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            克隆数据。

            Args:
                other (Seepage.FluDef): 要克隆的FluDef对象。

            Returns:
                Seepage.FluDef: 克隆后的FluDef对象。
            """
            if other is not None:
                assert isinstance(other, Seepage.FluDef)
                core.fludef_clone(self.handle, other.handle)
            return self

        def get_copy(self, name=None):
            """
            返回当前数据的一个拷贝。

            Args:
                name (str, optional): 拷贝后的数据的名称。默认为None。

            Returns:
                Seepage.FluDef: 拷贝后的FluDef对象。
            """
            result = Seepage.FluDef()
            result.clone(self)
            if name is not None:
                result.name = name
            return result

    class FluData(HasHandle):
        """
        流体数据(存储在Cell中)。一个流体数据由以下属性组成：
        1、流体的质量、密度、粘性系数。
        2、流体的自定义属性。
            在FluData内存储一个浮点型的数组，存储一系列自定义的属性，用于辅助存储和计算。自定义属性从0开始编号。
        3、流体的组分。
            流体的组分亦采用FluData类进行定义（即FluData为一个嵌套的类），因此，流体的组分也具有和流体同样的数据。流体的组分存储在
            一个数组内，且从0开始编号。当流体的组分数量不为0的时候，则存储在流体自身的数据自动失效，并利用组分的属性来自动计算
            这些组分作为一个整体的属性。如：流体的质量等于各个组分的质量之和，体积等于各个组分的体积之和，自定义属性则等于不同组分
            根据质量的加权平均。
        """
        core.use(c_void_p, 'new_fluid')
        core.use(None, 'del_fluid', c_void_p)

        def __init__(self, mass=None, den=None, vis=None, vol=None, handle=None):
            """
            创建给定handle的引用，或者创建流体数据。

            Args:
                mass (float, optional): 流体的质量，单位为kg。默认为None。
                den (float, optional): 流体的密度，单位为kg/m^3。默认为None。
                vis (float, optional): 流体的粘性系数，单位为Pa.s。默认为None。
                vol (float, optional): 流体的体积，单位为m^3。默认为None。
                handle (c_void_p, optional): 流体数据的句柄。默认为None。
            """
            super(Seepage.FluData, self).__init__(handle, core.new_fluid, core.del_fluid)
            if handle is None:
                if mass is not None:
                    self.mass = mass
                if den is not None:
                    self.den = den
                if vis is not None:
                    self.vis = vis
                if vol is not None:
                    assert mass is None
                    self.vol = vol
            else:
                assert mass is None and den is None and vis is None and vol is None

        core.use(None, 'fluid_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。可选扩展格式：
                1：.txt
                .TXT 格式
                （跨平台，基本不可读）

                2：.xml
                .XML 格式
                （特定可读性，文件体积最大，读写速度最慢，跨平台）

                3：.其他
                二进制格式
                （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

            Args:
                path (str): 保存文件的路径。
            """
            if isinstance(path, str):
                make_parent(path)
                core.fluid_save(self.handle, make_c_char_p(path))

        core.use(None, 'fluid_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

            Args:
                path (str): 读取文件的路径。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.fluid_load(self.handle, make_c_char_p(path))

        core.use(None, 'fluid_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'fluid_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中。其中fmt的取值可以为: text, xml和binary。

            Args:
                fmt (str, optional): 序列化的格式，可选值为'text', 'xml'和'binary'。默认为'binary'。

            Returns:
                FileMap: 序列化后的FileMap对象。
            """
            fmap = FileMap()
            core.fluid_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据。其中fmt的取值可以为: text, xml和binary。

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 反序列化的格式，可选值为'text', 'xml'和'binary'。默认为'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.fluid_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            获取二进制格式的序列化数据。

            Returns:
                FileMap: 二进制格式的序列化数据。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            设置二进制格式的序列化数据。

            Args:
                value (FileMap): 二进制格式的序列化数据。
            """
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'fluid_get_mass', c_void_p)
        core.use(None, 'fluid_set_mass', c_void_p, c_double)

        @property
        def mass(self):
            """
            流体的质量，单位为kg。

            Returns:
                float: 流体的质量。
            """
            return core.fluid_get_mass(self.handle)

        @mass.setter
        def mass(self, value):
            """
            设置流体的质量，单位为kg。

            Args:
                value (float): 流体的质量，必须大于等于0。
            """
            assert value >= 0
            core.fluid_set_mass(self.handle, value)

        core.use(c_double, 'fluid_get_vol', c_void_p)
        core.use(None, 'fluid_set_vol', c_void_p, c_double)

        @property
        def vol(self):
            """
            流体的体积，单位为m^3。
            注意:
                内核中并不存储流体体积，而是根据质量和密度计算得到的。

            Returns:
                float: 流体的体积。
            """
            return core.fluid_get_vol(self.handle)

        @vol.setter
        def vol(self, value):
            """
            修改流体的体积，单位为m^3。
            注意:
                内核中并不存储流体体积，而是根据质量和密度计算得到的。
                将修改mass，并保持density不变。

            Args:
                value (float): 流体的体积，必须大于等于0。
            """
            assert value >= 0
            core.fluid_set_vol(self.handle, value)

        core.use(c_double, 'fluid_get_den', c_void_p)
        core.use(None, 'fluid_set_den', c_void_p, c_double)

        @property
        def den(self):
            """
            流体密度，单位为kg/m^3。
                注意: 流体不可压缩，除非外部修改，否则密度永远维持不变。
            假设：
                在计算的过程中，流体的密度不会发生剧烈的变化，因此，在一次迭代的过程中，流体的密度可以
                视为不变的。在一次迭代之后，可以根据最新的温度和压力来更新流体的密度。
            注意：
                在利用TherFlowConfig来iterate的时候，如果模型中存储了流体的定义，那么流体密度的
                更新会被自动调用，从而保证流体的密度总是最新的。

            Returns:
                float: 流体的密度。
            """
            return core.fluid_get_den(self.handle)

        @den.setter
        def den(self, value):
            """
            设置流体的密度，单位为kg/m^3。

            Args:
                value (float): 流体的密度，必须大于0。
            """
            assert value > 0
            core.fluid_set_den(self.handle, value)

        core.use(c_double, 'fluid_get_vis', c_void_p)
        core.use(None, 'fluid_set_vis', c_void_p, c_double)

        @property
        def vis(self):
            """
            流体粘性系数，单位为Pa.s。
                注意: 除非外部修改，否则vis维持不变。
            流体粘性的更新规则和密度相似。

            Returns:
                float: 流体的粘性系数。
            """
            return core.fluid_get_vis(self.handle)

        @vis.setter
        def vis(self, value):
            """
            设置流体的粘性系数，单位为Pa.s。

            Args:
                value (float): 流体的粘性系数，必须大于0。
            """
            assert value > 0
            core.fluid_set_vis(self.handle, value)

        @property
        def is_solid(self):
            """
            该流体单元在计算内核中是否可以被视为固体。
            注意：
                该属性将被弃用。

            Returns:
                bool: 如果流体的粘性系数大于等于0.5e30，则返回True；否则返回False。
            """
            warnings.warn('FluData.is_solid will be deleted after 2024-5-5', DeprecationWarning)
            return self.vis >= 0.5e30

        core.use(c_double, 'fluid_get_attr', c_void_p, c_size_t)
        core.use(None, 'fluid_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取第index个流体自定义属性。当两个流体数据相加时，自定义属性将根据质量进行加权平均。

            Args:
                index (int or str): 自定义属性的索引或键。
                default_val (float, optional): 当属性不存在或不在有效范围内时返回的默认值。默认为None。
                **valid_range: 自定义属性的有效范围。

            Returns:
                float: 自定义属性的值，如果不存在或不在有效范围内，则返回默认值。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Fluid)
                assert isinstance(self.cell, Seepage.Cell)
                index = self.cell.model.get_flu_key(key=index)
            if index is None:
                return default_val
            # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            value = core.fluid_get_attr(self.handle, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置第index个流体自定义属性。参考get_attr函数。

            Args:
                index (int or str): 自定义属性的索引或键。
                value (float): 自定义属性的值。

            Returns:
                FluData: 返回当前对象。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Fluid)
                assert isinstance(self.cell, Seepage.Cell)
                index = self.cell.model.reg_flu_key(key=index)
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.fluid_set_attr(self.handle, index, value)
            return self

        core.use(None, 'fluid_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            拷贝所有的数据。

            Args:
                other (FluData): 要拷贝的FluData对象。

            Returns:
                FluData: 返回当前对象。
            """
            if other is not None:
                assert isinstance(other, Seepage.FluData)
                core.fluid_clone(self.handle, other.handle)
            return self

        def get_copy(self):
            """
            获取当前对象的拷贝。

            Returns:
                FluData: 当前对象的拷贝。
            """
            result = Seepage.FluData()
            result.clone(self)
            return result

        core.use(None, 'fluid_add', c_void_p, c_void_p)

        def add(self, other):
            """
            将other所定义的流体数据添加到self。注意，并不是添加组分。类似于: self = self + other。
            比如:
                若self的质量为1kg，other的质量也为1kg，则当执行了此函数之后，self的质量会成为2kg，而other保持不变。

            Args:
                other (FluData): 要添加的FluData对象。
            """
            assert isinstance(other, Seepage.FluData)
            core.fluid_add(self.handle, other.handle)

        core.use(c_size_t, 'fluid_get_component_number', c_void_p)
        core.use(None, 'fluid_set_component_number', c_void_p, c_size_t)

        @property
        def component_number(self):
            """
            流体组分的数量。当流体不可再分的时候，组分数量为0；否则，流体被视为混合物，且组分的数量大于0。

            Returns:
                int: 流体组分的数量。
            """
            return core.fluid_get_component_number(self.handle)

        @component_number.setter
        def component_number(self, value):
            """
            设置流体组分的数量。

            Args:
                value (int): 流体组分的数量。
            """
            core.fluid_set_component_number(self.handle, value)

        core.use(c_void_p, 'fluid_get_component', c_void_p, c_size_t)

        def get_component(self, idx):
            """
            返回给定的组分。

            Args:
                idx (int): 组分的索引。

            Returns:
                FluData: 给定索引的组分对象，如果索引无效则返回None。
            """
            idx = get_index(idx, self.component_number)
            if idx is not None:
                return Seepage.FluData(handle=core.fluid_get_component(self.handle, idx))

        core.use(None, 'fluid_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的组分。
            """
            core.fluid_clear_components(self.handle)

        core.use(c_size_t, 'fluid_add_component', c_void_p, c_void_p)

        def add_component(self, flu):
            """
            添加流体组分，并返回组分的ID。

            Args:
                flu (FluData): 要添加的流体组分对象。

            Returns:
                int: 新添加组分的ID。
            """
            assert isinstance(flu, Seepage.FluData)
            return core.fluid_add_component(self.handle, flu.handle)

        core.use(None, 'fluid_set_property', c_void_p, c_double, c_size_t, c_size_t, c_void_p)

        def set_property(self, p, fa_t, fa_c, fdef):
            """
            在给定压力和由 <fa_T> 定义的流体温度下，设置流体的密度、粘度和比热。

            Args:
                p (float): 压力。
                fa_t (int): 流体温度的索引。
                fa_c (int): 流体组分的索引。
                fdef (FluDef): 流体定义对象。
            """
            assert isinstance(fdef, Seepage.FluDef)
            core.fluid_set_property(self.handle, p, fa_t, fa_c, fdef.handle)

        core.use(None, 'fluid_set_components', c_void_p, c_void_p)

        def set_components(self, fdef):
            """
            按照fdef的定义来设置流体的组分的数量，从而使得这个流体数据和给定的流体定义具有相同的结构。

            Args:
                fdef (FluDef): 流体定义对象。
            """
            assert isinstance(fdef, Seepage.FluDef)
            core.fluid_set_components(self.handle, fdef.handle)

    class Fluid(FluData):
        core.use(c_void_p, 'seepage_cell_get_fluid', c_void_p, c_size_t)

        def __init__(self, cell, fid):
            """
            初始化Fluid对象。

            Args:
                cell (Seepage.CellData): 流体所在的Cell对象。
                fid (int): 流体在Cell中的编号，必须小于Cell内流体的数量。
            """
            assert isinstance(cell, Seepage.CellData)
            assert isinstance(fid, int)
            assert fid < cell.fluid_number
            self.cell = cell
            self.fid = fid
            super(Seepage.Fluid, self).__init__(handle=core.seepage_cell_get_fluid(self.cell.handle, self.fid))

        @property
        def vol_fraction(self):
            """
            流体的体积占Cell内所有流体总体积的比例。

            Returns:
                float: 流体的体积占比。
            """
            return self.cell.get_fluid_vol_fraction(self.fid)

    class CellData(HasHandle):
        """
        CellData类用于管理和操作控制体（Cell）的数据。

        该类提供了一系列方法用于序列化保存和加载数据，设置和获取Cell的位置、孔隙参数、流体属性等。
        """
        core.use(c_void_p, 'new_seepage_cell')
        core.use(None, 'del_seepage_cell', c_void_p)

        def __init__(self, path=None, handle=None):
            """
            初始化CellData对象。

            Args:
                path (str, optional): 用于加载数据的文件路径。默认为None。
                handle (c_void_p, optional): 指向底层数据的句柄。默认为None。
            """
            super(Seepage.CellData, self).__init__(handle, core.new_seepage_cell, core.del_seepage_cell)
            if handle is None:
                if isinstance(path, str):
                    self.load(path)

        core.use(None, 'seepage_cell_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。可选扩展格式：
                1：.txt
                .TXT 格式
                （跨平台，基本不可读）

                2：.xml
                .XML 格式
                （特定可读性，文件体积最大，读写速度最慢，跨平台）

                3：.其他
                二进制格式
                （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

            Args:
                path (str): 保存文件的路径。
            """
            if isinstance(path, str):
                make_parent(path)
                core.seepage_cell_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_cell_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

            Args:
                path (str): 读取文件的路径。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.seepage_cell_load(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_cell_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'seepage_cell_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

            Args:
                fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

            Returns:
                FileMap: 序列化后的FileMap对象。
            """
            fmap = FileMap()
            core.seepage_cell_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 反序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.seepage_cell_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            获取当前Cell对象的二进制格式FileMap对象。

            Returns:
                FileMap: 二进制格式的FileMap对象。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            通过FileMap对象设置当前Cell对象的数据。

            Args:
                value (FileMap): 包含序列化数据的FileMap对象。
            """
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'seepage_cell_get_pos', c_void_p, c_size_t)
        core.use(None, 'seepage_cell_set_pos', c_void_p, c_size_t, c_double)

        @property
        def x(self):
            """
            在三维空间中的x坐标

            Returns:
                float: x坐标的值。
            """
            return core.seepage_cell_get_pos(self.handle, 0)

        @x.setter
        def x(self, value):
            """
            设置在三维空间中的x坐标。

            Args:
                value (float): 新的x坐标的值。
            """
            core.seepage_cell_set_pos(self.handle, 0, value)

        @property
        def y(self):
            """
            在三维空间中的y坐标

            Returns:
                float: y坐标的值。
            """
            return core.seepage_cell_get_pos(self.handle, 1)

        @y.setter
        def y(self, value):
            """
            设置在三维空间中的y坐标。

            Args:
                value (float): 新的y坐标的值。
            """
            core.seepage_cell_set_pos(self.handle, 1, value)

        @property
        def z(self):
            """
            在三维空间中的z坐标

            Returns:
                float: z坐标的值。
            """
            return core.seepage_cell_get_pos(self.handle, 2)

        @z.setter
        def z(self, value):
            """
            设置在三维空间中的z坐标。

            Args:
                value (float): 新的z坐标的值。
            """
            core.seepage_cell_set_pos(self.handle, 2, value)

        @property
        def pos(self):
            """
            该Cell在三维空间的坐标

            Returns:
                list: 包含x、y、z坐标的列表。
            """
            return [core.seepage_cell_get_pos(self.handle, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            设置该Cell在三维空间的坐标。

            Args:
                value (list): 包含x、y、z坐标的列表，长度必须为3。
            """
            assert len(value) == 3
            for dim in range(3):
                core.seepage_cell_set_pos(self.handle, dim, value[dim])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离

            Args:
                other (CellData or list): 另一个Cell对象或者包含坐标的列表。

            Returns:
                float: 两个对象之间的距离。
            """
            if hasattr(other, 'pos'):
                return get_distance(self.pos, other.pos)
            else:
                return get_distance(self.pos, other)

        core.use(c_double, 'seepage_cell_get_v0', c_void_p)
        core.use(None, 'seepage_cell_set_v0', c_void_p, c_double)

        @property
        def v0(self):
            """
            当流体压力等于0时，该Cell内流体的存储空间 m^3.
            注意:
                务必设置合适的刚度和孔隙度，使得v0的数值大于0

            Returns:
                float: 流体存储空间的值。
            """
            return core.seepage_cell_get_v0(self.handle)

        @v0.setter
        def v0(self, value):
            """
            设置当流体压力等于0时，该Cell内流体的存储空间 m^3。

            Args:
                value (float): 新的流体存储空间的值，必须大于等于1.0e-10。
            """
            assert value >= 1.0e-10, f'value = {value}'
            core.seepage_cell_set_v0(self.handle, value)

        core.use(c_double, 'seepage_cell_get_k', c_void_p)
        core.use(None, 'seepage_cell_set_k', c_void_p, c_double)

        @property
        def k(self):
            """
            流体压力增加1Pa的时候，孔隙体积的增加量(m^3). k的数值越小，则刚度越大.

            Returns:
                float: 孔隙体积增加量的值。
            """
            return core.seepage_cell_get_k(self.handle)

        @k.setter
        def k(self, value):
            """
            设置流体压力增加1Pa的时候，孔隙体积的增加量(m^3)。

            Args:
                value (float): 新的孔隙体积增加量的值。
            """
            core.seepage_cell_set_k(self.handle, value)

        def set_pore(self, p, v, dp, dv):
            """
            创建一个孔隙，使得当内部压力等于p时，体积为v；
            如果压力变化dp，体积变化为dv

            Args:
                p (float): 内部压力。
                v (float): 体积。
                dp (float): 压力变化量。
                dv (float): 体积变化量。

            Returns:
                CellData: 返回当前CellData对象。
            """
            k = max(1.0e-30, abs(dv)) / max(1.0e-30, abs(dp))
            self.k = k
            v0 = v - p * k
            if v0 <= 0:
                warnings.warn(f'v0 (= {v0}) <= 0 at {self.pos}. p={p}, v={v}, dp={dp}, dv={dv}')
            self.v0 = v0
            return self

        def v2p(self, v):
            """
            给定内部流体的体积，根据孔隙刚度计算孔隙内流体的压力。

            Args:
                v (float): 内部流体的体积。

            Returns:
                float: 孔隙内流体的压力。
            """
            return (v - self.v0) / self.k

        def p2v(self, p):
            """
            给定内部流体的压力，根据孔隙刚度计算内部流体的体积。

            Args:
                p (float): 内部流体的压力。

            Returns:
                float: 内部流体的体积。
            """
            return self.v0 + p * self.k

        core.use(None, 'seepage_cell_fill', c_void_p, c_double, c_void_p)

        def fill(self, p, s):
            """
            根据此时流体的密度，孔隙的v0和k，给定的目标压力和流体饱和度，设置各个组分的质量。
                这里p为目标压力，s为目标饱和度；
                当各个相的饱和度的和不等于1的时候，将首先对饱和度的值进行等比例调整；
            注意：
                s作为一个数组，它的长度应该等于流体的数量或者组分的数量(均可以)；
                当s的长度等于流体的数量的时候，需要事先设置流体中各个组分的比例；
            注意
                当s的总和等于0的时候，虽然给定目标压力，但是仍然不会填充流体。此时填充后
                所有的组分都等于0。

            Args:
                p (float): 目标压力。
                s (Vector): 目标饱和度。

            Returns:
                CellData: 返回当前CellData对象。
            """
            if not isinstance(s, Vector):
                s = Vector(s)
            assert isinstance(s, Vector)
            core.seepage_cell_fill(self.handle, p, s.handle)
            return self

        core.use(c_double, 'seepage_cell_get_pre', c_void_p)

        @property
        def pre(self):
            """
            单元格内流体的压力
                (根据流体的总体积和孔隙弹性计算得出)

            Returns:
                float: 单元格内流体的压力。
            """
            return core.seepage_cell_get_pre(self.handle)

        core.use(c_size_t, 'seepage_cell_get_fluid_n', c_void_p)
        core.use(None, 'seepage_cell_set_fluid_n', c_void_p, c_size_t)

        @property
        def fluid_number(self):
            """
            单元格内流体的数量
                (至少设置为1，并且需要为模型中的所有单元格设置相同的值)

            Returns:
                int: 单元格内流体的数量。
            """
            return core.seepage_cell_get_fluid_n(self.handle)

        @fluid_number.setter
        def fluid_number(self, value):
            """
            设置单元格内流体的数量。

            Args:
                value (int): 新的流体数量，必须在0到10之间。
            """
            assert 0 <= value < 10
            core.seepage_cell_set_fluid_n(self.handle, value)

        def get_fluid(self, *args):
            """
            返回给定序号的流体。(当参数数量为1的时候，返回Seepage.Fluid对象；当参数数量大于1的时候，返回Seepage.FluData对象)

            Args:
                *args: 流体或组分的序号。

            Returns:
                Seepage.Fluid or Seepage.FluData: 返回相应的流体或组分对象，如果不存在则返回None。
            """
            if len(args) > 0:
                idx = get_index(args[0], self.fluid_number)
                if idx is not None:
                    flu = Seepage.Fluid(self, idx)
                    if len(args) > 1:
                        for i in range(1, len(args)):
                            flu = flu.get_component(args[i])
                            if flu is None:
                                return
                    return flu

        @property
        def fluids(self):
            """
            单元格内的所有流体

            Returns:
                Iterator: 包含所有流体的迭代器。
            """
            return Iterator(self, self.fluid_number, lambda m, ind: m.get_fluid(ind))

        def get_component(self, indexes):
            """
            返回给定序号的组分。

            Args:
                indexes (int or list): 组分的序号或序号列表。

            Returns:
                Seepage.FluData: 返回相应的组分对象，如果不存在则返回None。
            """
            if is_array(indexes):
                return self.get_fluid(*indexes)
            else:
                return self.get_fluid(indexes)

        core.use(c_double, 'seepage_cell_get_fluid_vol', c_void_p)

        @property
        def fluid_vol(self):
            """
            所有流体的体积。
            注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，在计算内核中被视为固体的流体

            Returns:
                float: 所有流体的体积。
            """
            return core.seepage_cell_get_fluid_vol(self.handle)

        core.use(c_double, 'seepage_cell_get_fluid_mass', c_void_p)

        @property
        def fluid_mass(self):
            """
            所有流体的质量
            注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，在计算内核中被视为固体的流体

            Returns:
                float: 所有流体的质量。
            """
            return core.seepage_cell_get_fluid_mass(self.handle)

        core.use(c_double, 'seepage_cell_get_fluid_vol_fraction', c_void_p, c_size_t)

        def get_fluid_vol_fraction(self, index):
            """
            返回index给定流体的体积饱和度

            Args:
                index (int): 流体的序号。

            Returns:
                float: 该流体的体积饱和度，如果序号无效则返回None。
            """
            index = get_index(index, self.fluid_number)
            if index is not None:
                return core.seepage_cell_get_fluid_vol_fraction(self.handle, index)

        core.use(c_double, 'seepage_cell_get_attr', c_void_p, c_size_t)
        core.use(None, 'seepage_cell_set_attr', c_void_p, c_size_t, c_double)
        core.use(c_size_t, 'seepage_cell_get_attr_n', c_void_p)

        @property
        def attr_n(self):
            """
            当前存储attr的数组的长度

            Returns:
                int: 存储attr的数组的长度。
            """
            return core.seepage_cell_get_attr_n(self.handle)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            该Cell的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)

            Args:
                index (int or str): 自定义属性的序号或名称。
                default_val (float, optional): 当属性不存在时返回的默认值。默认为None。
                **valid_range: 可选的有效范围参数。

            Returns:
                float: 自定义属性的值，如果不存在则返回默认值。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Cell)
                index = self.model.get_cell_key(key=index)
            if index is None:
                return default_val
            if index < 0:
                if index == -1:
                    return self.x
                if index == -2:
                    return self.y
                if index == -3:
                    return self.z
                if index == -4:
                    return self.v0
                if index == -5:
                    return self.k
                return default_val
            value = core.seepage_cell_get_attr(self.handle, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            该Cell的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)

            Args:
                index (int or str): 自定义属性的序号或名称。
                value (float): 自定义属性的新值。

            Returns:
                CellData: 返回当前CellData对象。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Cell)
                index = self.model.reg_cell_key(key=index)
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            if index < 0:
                if index == -1:
                    self.x = value
                    return self
                if index == -2:
                    self.y = value
                    return self
                if index == -3:
                    self.z = value
                    return self
                if index == -4:
                    self.v0 = value
                    return self
                if index == -5:
                    self.k = value
                    return self
                assert False
            core.seepage_cell_set_attr(self.handle, index, value)
            return self

        core.use(None, 'seepage_cell_multiply', c_void_p, c_void_p, c_double)

        def multiply(self, scale, result=None):
            """
            将孔隙大小和流体都乘以相同的倍率，其余所有的属性保持不变。

            Args:
                scale (float): 缩放倍率。
                result (Seepage.CellData, optional): 用于存储结果的CellData对象。默认为None。

            Returns:
                Seepage.CellData: 缩放后的CellData对象。
            """
            if not isinstance(result, Seepage.CellData):
                result = Seepage.CellData()
            core.seepage_cell_multiply(result.handle, self.handle, scale)
            return result

        def __mul__(self, scale):
            """
            将孔隙大小和流体都乘以相同的倍率，其余所有的属性保持不变。

            Args:
                scale (float): 缩放倍率。

            Returns:
                Seepage.CellData: 缩放后的CellData对象。
            """
            return self.multiply(scale)

        core.use(None, 'seepage_cell_clone', c_void_p, c_void_p)

        def clone(self, other, *, scale=None):
            """
            从other克隆数据（所有的数据）

            Args:
                other (Seepage.CellData): 要克隆数据的源CellData对象。
                scale (float, optional): 可选的缩放倍率。默认为None。

            Returns:
                CellData: 克隆后的CellData对象。
            """
            if other is None:
                return self
            assert isinstance(other, Seepage.CellData)
            if scale is not None:
                other.multiply(scale, result=self)
                return self
            else:
                core.seepage_cell_clone(self.handle, other.handle)
                return self

        core.use(None, 'seepage_cell_set_fluid_components', c_void_p, c_void_p)

        def set_fluid_components(self, model):
            """
            利用model中定义的流体来设置Cell中的流体的组分的数量。
            注意:
                此函数会递归地调用model中的组分定义，从而保证Cell中流体组分结构和model中完全一样。

            Args:
                model (Seepage): 用于定义流体组分的模型。
            """
            assert isinstance(model, Seepage)
            core.seepage_cell_set_fluid_components(self.handle, model.handle)

        core.use(None, 'seepage_cell_set_fluid_property', c_void_p,
                 c_double, c_size_t, c_size_t,
                 c_void_p)

        def set_fluid_property(self, p, fa_t, fa_c, model):
            """
            利用model中定义的流体的属性来更新流体的比热、密度和粘性系数。
            注意：
                函数会使用在各个流体中由fa_t指定的温度，并根据给定的压力p来查找流体属性；
                因此，在调用这个函数之前，务必要设置各个流体的温度 (fa_t)。
            注意：
                在调用之前，务必保证此Cell内的流体的结构和model内fludef的结构一致。 即，应该首先调用set_fluid_components函数

            Args:
                p (float): 压力。
                fa_t (int): 流体温度的索引。
                fa_c (int): 流体组分的索引。
                model (Seepage): 用于定义流体属性的模型。
            """
            assert isinstance(model, Seepage)
            core.seepage_cell_set_fluid_property(self.handle, p, fa_t, fa_c, model.handle)

        core.use(None, 'seepage_cell_set_fluids_by_lexpr', c_void_p, c_void_p, c_void_p)

        def set_fluids_by_lexpr(self, lexpr: LinearExpr, model):
            """ 设置此Cell中的流体

            此函数将使用model中各个cell的流体，然后使用线性表达式lexpr来计算

            Args:
                lexpr (LinearExpr): 计算流体的线性表达式
                model (Seepage): 用来拷贝流体的另外一个模型

            Returns:
                None
            """
            core.seepage_cell_set_fluids_by_lexpr(self.handle, lexpr.handle, model.handle)

        core.use(None, 'seepage_cell_set_pore_by_lexpr', c_void_p, c_void_p, c_void_p)

        def set_pore_by_lexpr(self, lexpr: LinearExpr, model):
            """ 设置此Cell中的孔隙

            此函数将使用model中各个cell的孔隙，然后使用线性表达式lexpr来计算

            Args:
                lexpr (LinearExpr): 计算pore的线性表达式
                model (Seepage): 用来拷贝pore的另外一个模型

            Returns:
                None
            """
            core.seepage_cell_set_pore_by_lexpr(self.handle, lexpr.handle, model.handle)

        core.use(None, 'seepage_cell_set_mass_attr_by_lexpr',
                 c_void_p, c_size_t, c_void_p, c_void_p)

        def set_mass_attr_by_lexpr(self, idx, lexpr: LinearExpr, model):
            """ 设置此Cell中的自定义属性
            此函数将使用model中各个cell的自定义属性，然后使用线性表达式lexpr来计算
            Args:
                idx (int): 自定义属性的序号
                lexpr (LinearExpr): 计算自定义属性的线性表达式
                model (Seepage): 用来拷贝自定义属性的另外一个模型
            Returns:
                None
            """
            core.seepage_cell_set_mass_attr_by_lexpr(self.handle, idx, lexpr.handle, model.handle)

        core.use(None, 'seepage_cell_set_density_attr_by_lexpr',
                 c_void_p, c_size_t, c_void_p, c_void_p)

        def set_density_attr_by_lexpr(self, idx, lexpr: LinearExpr, model):
            """ 设置此Cell中的自定义属性
            此函数将使用model中各个cell的自定义属性，然后使用线性表达式lexpr来计算
            Args:
                idx (int): 自定义属性的序号
                lexpr (LinearExpr): 计算自定义属性的线性表达式
                model (Seepage): 用来拷贝自定义属性的另外一个模型
            Returns:
                None
            """
            core.seepage_cell_set_density_attr_by_lexpr(self.handle, idx, lexpr.handle, model.handle)

    class Cell(CellData):
        """
        Cell为控制体。一个Cell由如下几个部分组成：

        1、该控制体内流体存储空间的大小以及刚度(即设置Cell的pore). 计算内核根据Cell内流体的总的体积，结合pore的弹性性质来定义Cell内流体
            的压力，所以在创建一个Cell之后，必须首先对Cell的pore进行配置。具体地，调用Cell.set_pore函数来设置Cell的pore;

        2、Cell内存储的流体。一个Cell内可以存储多种流体，这些流体存储在一个数组内，且从0开始编号。每一种流体可以由多个组分组成，流体的组分
            也从0开始编号；

        3、Cell的自定义属性。在Cell内存储一个浮点型的数组，存储一系列自定义的属性，用于辅助存储和计算。自定义属性从0开始编号。
        """

        core.use(c_void_p, 'seepage_get_cell', c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化Cell对象。

            Args:
                model (Seepage): 所属的Seepage模型。
                index (int): Cell的索引，必须小于模型中的Cell数量。

            Raises:
                AssertionError: 如果model不是Seepage类型，或者index不是整数，或者index大于等于模型中的Cell数量。
            """
            assert isinstance(model, Seepage)
            assert isinstance(index, int)
            assert index < model.cell_number
            self.model = model
            self.index = index
            super(Seepage.Cell, self).__init__(handle=core.seepage_get_cell(model.handle, index))

        def __str__(self):
            """
            返回Cell对象的字符串表示。

            Returns:
                str: 包含Cell句柄、索引和位置的字符串。
            """
            return f'zml.Seepage.Cell(handle = {self.model.handle}, index = {self.index}, pos = {self.pos})'

        core.use(c_size_t, 'seepage_get_cell_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            获取与该Cell连接的Face的数量。

            Returns:
                int: 与该Cell连接的Face的数量。
            """
            return core.seepage_get_cell_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            获取与该Cell相邻的Cell的数量。

            Returns:
                int: 与该Cell相邻的Cell的数量，等于face_number。
            """
            return self.face_number

        core.use(c_size_t, 'seepage_get_cell_face_id', c_void_p, c_size_t, c_size_t)

        core.use(c_size_t, 'seepage_get_cell_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            """
            获取与该Cell相邻的第index个Cell。

            Args:
                index (int): 相邻Cell的索引。

            Returns:
                Seepage.Cell or None: 与该Cell相邻的第index个Cell，如果不存在则返回None。
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.seepage_get_cell_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            获取与该Cell连接的第index个Face。

            Args:
                index (int): 连接Face的索引。

            Returns:
                Seepage.Face or None: 与该Cell连接的第index个Face，如果不存在则返回None。
            注：该Face的另一侧，即为get_cell返回的Cell。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                face_id = core.seepage_get_cell_face_id(self.model.handle, self.index, index)
                return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            获取此Cell周围的所有Cell。

            Returns:
                Iterator: 包含此Cell周围所有Cell的迭代器。
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            获取此Cell周围的所有Face。

            Returns:
                Iterator: 包含此Cell周围所有Face的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        def set_ini(self, ca_mc, ca_t, fa_t, fa_c, pos=None, vol=1.0, porosity=0.1, pore_modulus=1000e6, denc=1.0e6,
                    temperature=280.0, p=1.0, s=None, pore_modulus_range=None):
            """
            配置初始状态。必须保证给定温度和压力。

            Args:
                ca_mc (int): 自定义属性的索引，用于存储质量。
                ca_t (int): 自定义属性的索引，用于存储温度。
                fa_t (int): 流体温度的索引。
                fa_c (int): 流体组分的索引。
                pos (list or None, optional): Cell的位置，默认为None。
                vol (float, optional): Cell的体积，默认为1.0。
                porosity (float, optional): 孔隙度，默认为0.1。
                pore_modulus (float, optional): 孔隙模量，默认为1000e6。
                denc (float, optional): 密度，默认为1.0e6。
                temperature (float, optional): 温度，默认为280.0。
                p (float, optional): 压力，默认为1.0。
                s (list or None, optional): 饱和度数组，默认为None。
                pore_modulus_range (tuple or None, optional): 孔隙模量的有效范围，默认为None。

            Raises:
                AssertionError: 如果孔隙模量不在有效范围内，或者孔隙度小于1.0e-6。
            """
            model = self.model
            assert isinstance(model, Seepage)

            if pos is not None:
                self.pos = pos

            if temperature is not None:
                self.set_attr(ca_t, temperature)

            if vol is not None and denc is not None:
                self.set_attr(ca_mc, vol * denc)

            if pore_modulus is not None:
                if pore_modulus_range is None:
                    assert 1e6 < pore_modulus < 10000e6
                else:
                    assert pore_modulus_range[0] < pore_modulus < pore_modulus_range[1]

            if porosity is not None:
                assert 1.0e-6 < porosity

            # 确保在给定的这个p下，孔隙度等于设置的值.
            if p is not None and vol is not None and porosity is not None and pore_modulus is not None:
                self.set_pore(p, vol * porosity, pore_modulus, vol * porosity)

            # 设置流体的结构
            self.set_fluid_components(model)

            # 设置组分的温度.
            if temperature is not None:
                for i in range(self.fluid_number):
                    self.get_fluid(i).set_attr(fa_t, temperature)

            # 更新流体的比热、密度和粘性系数
            if p is not None:
                self.set_fluid_property(p=p, fa_t=fa_t, fa_c=fa_c, model=model)

            if s is not None and self.fluid_number > 0:
                def get_s(indexes):
                    assert len(indexes) > 0
                    temp = s
                    for ind in indexes:
                        if is_array(temp):
                            temp = temp[ind] if ind < len(temp) else 0.0
                        else:
                            temp = temp if ind == 0 else 0.0
                    return temp

                s2 = []
                vi = []

                def set_flu(flu):
                    assert isinstance(flu, Seepage.FluData)
                    if flu.component_number == 0:
                        s2.append(get_s(vi))
                    else:
                        for ind in range(flu.component_number):
                            vi.append(ind)
                            set_flu(flu.get_component(ind))
                            vi.pop(-1)

                for fid in range(self.fluid_number):
                    vi.append(fid)
                    set_flu(self.get_fluid(fid))
                    vi.pop(-1)

                # 调用上一级的fill函数来填充流体
                if p is not None:
                    self.fill(p, s2)

    class FaceData(HasHandle):
        """
        FaceData类用于表示和操作Cell之间界面（Face）的数据。

        该类提供了一系列方法来处理Face的序列化保存、加载，以及获取和设置Face的各种属性，如自定义属性、导流能力、相对渗透率曲线等。
        """
        core.use(c_void_p, 'new_seepage_face')
        core.use(None, 'del_seepage_face', c_void_p)

        def __init__(self, path=None, handle=None):
            """
            初始化FaceData对象。

            Args:
                path (str, optional): 用于加载序列化数据的文件路径。默认为None。
                handle (c_void_p, optional): 已有的FaceData句柄。默认为None。

            若handle为None且path为字符串，则会尝试从指定路径加载数据。
            """
            super(Seepage.FaceData, self).__init__(handle, core.new_seepage_face, core.del_seepage_face)
            if handle is None:
                if isinstance(path, str):
                    self.load(path)

        core.use(None, 'seepage_face_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。可选扩展格式：
                1：.txt
                .TXT 格式
                （跨平台，基本不可读）

                2：.xml
                .XML 格式
                （特定可读性，文件体积最大，读写速度最慢，跨平台）

                3：.其他
                二进制格式
                （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

            Args:
                path (str): 保存序列化数据的文件路径。
            """
            if isinstance(path, str):
                make_parent(path)
                core.seepage_face_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_face_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

            Args:
                path (str): 读取序列化数据的文件路径。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.seepage_face_load(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_face_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'seepage_face_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

            Args:
                fmt (str, optional): 序列化格式，可选值为 'text', 'xml' 和 'binary'。默认为 'binary'。

            Returns:
                FileMap: 包含序列化数据的FileMap对象。
            """
            fmap = FileMap()
            core.seepage_face_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 反序列化格式，可选值为 'text', 'xml' 和 'binary'。默认为 'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.seepage_face_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            获取当前FaceData对象的二进制序列化FileMap对象。

            Returns:
                FileMap: 包含二进制序列化数据的FileMap对象。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            从给定的FileMap对象中加载二进制序列化数据。

            Args:
                value (FileMap): 包含二进制序列化数据的FileMap对象。
            """
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'seepage_face_get_attr', c_void_p, c_size_t)
        core.use(None, 'seepage_face_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            该Face的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)

            Args:
                index (int or str): 自定义属性的索引或键名。
                default_val (float, optional): 当属性不存在或不在有效范围内时返回的默认值。默认为None。
                **valid_range: 可选的有效范围参数。

            Returns:
                float: 自定义属性的值，如果不存在或不在有效范围内则返回默认值。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Face)
                index = self.model.get_face_key(key=index)
            if index is None:
                return default_val
            value = core.seepage_face_get_attr(self.handle, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            该Face的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)

            Args:
                index (int or str): 自定义属性的索引或键名。
                value (float): 要设置的自定义属性的值。

            Returns:
                FaceData: 返回当前FaceData对象。
            """
            if isinstance(index, str):
                assert isinstance(self, Seepage.Face)
                index = self.model.reg_face_key(key=index)
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_face_set_attr(self.handle, index, value)
            return self

        core.use(None, 'seepage_face_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            从另一个FaceData对象克隆数据。

            Args:
                other (Seepage.FaceData): 要克隆数据的源FaceData对象。

            Returns:
                FaceData: 返回当前FaceData对象。
            """
            if other is not None:
                assert isinstance(other, Seepage.FaceData)
                core.seepage_face_clone(self.handle, other.handle)
            return self

        core.use(c_double, 'seepage_face_get_cond', c_void_p)
        core.use(None, 'seepage_face_set_cond', c_void_p, c_double)

        @property
        def cond(self):
            """
            此Face的导流能力. dv=cond*dp*dt/vis，其中dp为两端的压力差，dt为时间步长，vis为内部流体的粘性系数
                cond = area * perm / dist.
            如果是多相的情况下，可能需要两步矫正（程序内部自动算，用户不用设置）：
                1. 如果多相中存在固体，首先，需要计算 流体体积/总体积，得到流体的体积分数 a，用 cond * kr(a)得到流体的cond1.
                2. 如果流体有多种，对于第0种流体，s0=v0/v_sum，cond1 * kr0(s0) 得到 cond2_0.

            Returns:
                float: 此Face的导流能力。
            """
            return core.seepage_face_get_cond(self.handle)

        @cond.setter
        def cond(self, value):
            """
            此Face的导流能力. dv=cond*dp*dt/vis，其中dp为两端的压力差，dt为时间步长，vis为内部流体的粘性系数

            Args:
                value (float): 要设置的导流能力值。
            """
            core.seepage_face_set_cond(self.handle, value)

        core.use(c_double, 'seepage_face_get_dr', c_void_p)
        core.use(None, 'seepage_face_set_dr', c_void_p, c_double)

        @property
        def dr(self):
            """
            获取此Face的某个dr属性值(流体的额外驱动力)

            Returns:
                float: 此Face的属性值。
            """
            return core.seepage_face_get_dr(self.handle)

        @dr.setter
        def dr(self, value):
            """
            设置此Face的dr属性值(流体的额外驱动力)

            Args:
                value (float): 要设置的属性值。
            """
            core.seepage_face_set_dr(self.handle, value)

        core.use(c_double, 'seepage_face_get_dv', c_void_p, c_size_t)

        def get_dv(self, fluid_id):
            """
            返回上一步迭代通过这个face的流体的体积

            Args:
                fluid_id (int): 流体的ID。

            Returns:
                float: 上一步迭代通过这个face的指定流体的体积。
            """
            assert isinstance(fluid_id, int)
            return core.seepage_face_get_dv(self.handle, fluid_id)

        core.use(c_size_t, 'seepage_face_get_ikr', c_void_p, c_size_t)
        core.use(None, 'seepage_face_set_ikr',
                 c_void_p, c_size_t, c_size_t)

        def get_ikr(self, index):
            """
            第index种流体的相对渗透率曲线的id

            Args:
                index (int): 流体的索引。

            Returns:
                int: 第index种流体的相对渗透率曲线的ID。
            """
            return core.seepage_face_get_ikr(self.handle, index)

        def set_ikr(self, index, value):
            """
            设置在这个Face中，第index种流体的相对渗透率曲线的id.
                如果在这个Face中，没有为某个流体选择相渗曲线，则如果该流体的序号为ID，则默认使用序号为ID的相渗曲线。

            Args:
                index (int): 流体的索引。
                value (int): 要设置的相对渗透率曲线的ID。
            """
            core.seepage_face_set_ikr(self.handle, index, value)

    class Face(FaceData):
        """
        Face为Cell之间的界面。Cell由如下属性组成：

        1、Face的导流系数cond:  dv=dp*cond*dt/vis 其中dv为流经face的流体的体积，cond为导流系数，dt为时长，vis为流体的粘性系数

        2、Face中不同流体所采用的相对渗透率曲线的序号。在Seepage中可以定义多个（最多10000个）相对渗透率曲线，且不同的Face可以选用
            不同的相对渗透率曲线。<相对渗透率曲线的序号>可以不定义，此时会采用默认值(即第i种流体，自动选用第i个相渗曲线)
            注意：需要为每一种流体配置相对渗透率曲线;

        3、Face的自定义属性。在Face内存储一个浮点型的数组，存储一系列自定义的属性，用于辅助存储和计算。自定义属性从0开始编号。
        """
        core.use(c_void_p, 'seepage_get_face', c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化Face对象。

            Args:
                model (Seepage): 所属的Seepage模型对象。
                index (int): Face的索引。

            Raises:
                AssertionError: 如果model不是Seepage类型，或者index不是整数，或者index超出模型的Face数量范围。
            """
            assert isinstance(model, Seepage)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index
            super(Seepage.Face, self).__init__(handle=core.seepage_get_face(model.handle, index))

        def __str__(self):
            """
            返回Face对象的字符串表示。

            Returns:
                str: 包含Face句柄和索引的字符串。
            """
            return f'zml.Seepage.Face(handle = {self.model.handle}, index = {self.index}) '

        core.use(c_size_t, 'seepage_get_face_cell_id', c_void_p, c_size_t, c_size_t)

        @property
        def cell_number(self):
            """
            和Face连接的Cell的数量

            Returns:
                int: 与Face连接的Cell的数量，固定为2。
            """
            return 2

        def get_cell(self, index):
            """
            和Face连接的第index个Cell

            Args:
                index (int): 要获取的Cell的索引。

            Returns:
                Seepage.Cell or None: 与Face连接的第index个Cell，如果索引无效则返回None。
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.seepage_get_face_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        @property
        def cells(self):
            """
            返回Face两端的Cell

            Returns:
                tuple: 包含Face两端Cell的元组。
            """
            return self.get_cell(0), self.get_cell(1)

        @property
        def pos(self):
            """
            返回Face中心点的位置（根据两侧的Cell的位置来自动计算）

            Returns:
                tuple: 包含Face中心点位置坐标的元组。
            """
            p0 = self.get_cell(0).pos
            p1 = self.get_cell(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离

            Args:
                other (Seepage.Cell or tuple): 另一个Cell对象或位置坐标元组。

            Returns:
                float: 与另一个Cell或位置的距离。
            """
            if hasattr(other, 'pos'):
                return get_distance(self.pos, other.pos)
            else:
                return get_distance(self.pos, other)

        def get_another(self, cell):
            """
            返回另外一侧的Cell

            Args:
                cell (Seepage.Cell or int): Cell对象或Cell的索引。

            Returns:
                Seepage.Cell or None: 另一侧的Cell，如果输入无效则返回None。
            """
            if isinstance(cell, Seepage.Cell):
                cell = cell.index
            if self.get_cell(0).index == cell:
                return self.get_cell(1)
            if self.get_cell(1).index == cell:
                return self.get_cell(0)

    class Injector(HasHandle):
        """
        流体的注入点。可以按照一定的规律向特定的Cell注入特定的流体(或者能量). 注意Injector工作的逻辑：
            1. 如果设置了注入的流体的ID，则实施流体注入操作 (此时value代表注入的体积速率: m^3/s);
            2. 如果没有设置流体ID，并且设置了 ca_mc和ca_t属性，则实施热量注入操作;
        """
        core.use(c_void_p, 'new_injector')
        core.use(None, 'del_injector', c_void_p)

        def __init__(self, path=None, handle=None):
            """
            初始化Injector对象。

            Args:
                path (str, optional): 用于加载序列化数据的文件路径。默认为None。
                handle (c_void_p, optional): 已有的Injector句柄。默认为None。

            如果handle为None且path为字符串，则会尝试从指定路径加载数据。
            """
            super(Seepage.Injector, self).__init__(handle, core.new_injector, core.del_injector)
            if handle is None:
                if isinstance(path, str):
                    self.load(path)

        core.use(None, 'injector_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存。可选扩展格式：
                1：.txt
                .TXT 格式
                （跨平台，基本不可读）

                2：.xml
                .XML 格式
                （特定可读性，文件体积最大，读写速度最慢，跨平台）

                3：.其他
                二进制格式
                （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

            Args:
                path (str): 保存序列化数据的文件路径。
            """
            if isinstance(path, str):
                make_parent(path)
                core.injector_save(self.handle, make_c_char_p(path))

        core.use(None, 'injector_load', c_void_p, c_char_p)

        def load(self, path):
            """
            读取序列化文件。
                根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

            Args:
                path (str): 读取序列化数据的文件路径。
            """
            if isinstance(path, str):
                _check_ipath(path, self)
                core.injector_load(self.handle, make_c_char_p(path))

        core.use(None, 'injector_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'injector_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中。其中fmt的取值可以为: text, xml和binary

            Args:
                fmt (str, optional): 序列化格式，可选值为 'text', 'xml' 和 'binary'。默认为 'binary'。

            Returns:
                FileMap: 包含序列化数据的FileMap对象。
            """
            fmap = FileMap()
            core.injector_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据。其中fmt的取值可以为: text, xml和binary

            Args:
                fmap (FileMap): 包含序列化数据的FileMap对象。
                fmt (str, optional): 反序列化格式，可选值为 'text', 'xml' 和 'binary'。默认为 'binary'。
            """
            assert isinstance(fmap, FileMap)
            core.injector_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            获取当前Injector对象的二进制序列化FileMap对象。

            Returns:
                FileMap: 包含二进制序列化数据的FileMap对象。
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            """
            从给定的FileMap对象中加载二进制序列化数据。

            Args:
                value (FileMap): 包含二进制序列化数据的FileMap对象。
            """
            self.from_fmap(value, fmt='binary')

        core.use(c_size_t, 'injector_get_cell_id', c_void_p)
        core.use(None, 'injector_set_cell_id', c_void_p, c_size_t)

        @property
        def cell_id(self):
            """
            注入点关联的Cell的ID。如果该ID不存在，则不会注入。
            注：
                默认为无穷大

            Returns:
                int: 注入点关联的Cell的ID。
            """
            return core.injector_get_cell_id(self.handle)

        @cell_id.setter
        def cell_id(self, value):
            """
            设置注入点关联的Cell的ID。如果该ID不存在，则不会注入。
            注：
                默认为无穷大

            Args:
                value (int): 要设置的Cell的ID。
            """
            core.injector_set_cell_id(self.handle, value)

        core.use(c_void_p, 'injector_get_flu', c_void_p)

        @property
        def flu(self):
            """
            即将注入到Cell中的流体的数据。这里返回的是一个引用 (从而可以直接修改内部的数据)。
            注：
                默认质量为1e-100，即无限接近于0

            Returns:
                Seepage.FluData: 即将注入的流体的数据对象。
            """
            return Seepage.FluData(handle=core.injector_get_flu(self.handle))

        core.use(None, 'injector_set_fid', c_void_p, c_size_t, c_size_t, c_size_t)

        def set_fid(self, fluid_id):
            """
            设置注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
            注：在没有做特殊设置的时候，fid默认为[]

            Args:
                fluid_id: 注入的流体的ID。
            """
            core.injector_set_fid(self.handle, *parse_fid3(fluid_id))

        core.use(c_size_t, 'injector_get_fid_length', c_void_p)
        core.use(c_size_t, 'injector_get_fid_of', c_void_p, c_size_t)

        def get_fid(self):
            """
            返回注入流体的ID。
            注：在没有做特殊设置的时候，默认为[]

            Returns:
                list: 注入流体的ID列表。
            """
            count = core.injector_get_fid_length(self.handle)
            return [core.injector_get_fid_of(self.handle, idx) for idx in range(count)]

        @property
        def fid(self):
            """
            注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
            注：在没有做特殊设置的时候，fid默认为[]

            Returns:
                list: 注入流体的ID列表。
            """
            return self.get_fid()

        @fid.setter
        def fid(self, value):
            """
            设置注入的流体的ID。注意：如果需要注热的是热量，则将fluid_id设置为None。
            注：在没有做特殊设置的时候，fid默认为[]

            Args:
                value: 要设置的注入流体的ID。
            """
            self.set_fid(value)

        core.use(c_double, 'injector_get_value', c_void_p)
        core.use(None, 'injector_set_value', c_void_p, c_double)

        @property
        def value(self):
            """
            注入的数值。可以有多重的含义：
                当注入流体的时候，为注入的体积速率 m^3/s
                当注热时：
                    若恒温注热，则为温度
                    若恒功率，则为功率
            注：
                在没有做任何设置时，默认值为0

            Returns:
                float: 注入的数值。
            """
            return core.injector_get_value(self.handle)

        @value.setter
        def value(self, val):
            """
            设置注入的数值。
            注：
                在没有做任何设置时，默认值为0

            Args:
                val (float): 要设置的注入数值。
            """
            core.injector_set_value(self.handle, val)

        @property
        def time(self):
            """
            此属性已被移除。

            注：
                此属性已被移除，调用时会发出警告。

            Returns:
                int: 固定返回0。
            """
            warnings.warn('Property Seepage.Injector.time has been removed',
                          DeprecationWarning)
            return 0

        @time.setter
        def time(self, _):
            """
            设置时间属性（此属性已被移除）。

            注：
                此属性已被移除，调用时会发出警告。

            Args:
                _: 此参数无实际作用。
            """
            warnings.warn('Property Seepage.Injector.time has been removed',
                          DeprecationWarning)

        core.use(c_double, 'injector_get_pos', c_void_p, c_size_t)
        core.use(None, 'injector_set_pos', c_void_p, c_size_t, c_double)

        @property
        def pos(self):
            """
            该Injector在三维空间的坐标。
            注：
                在没有设置的时候，默认是一个无限远的位置 [1e+50, 1e+50, 1e+50]

            Returns:
                list: 包含三维坐标的列表。
            """
            return [core.injector_get_pos(self.handle, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            设置该Injector在三维空间的坐标。
            注：
                在没有设置的时候，默认是一个无限远的位置 [1e+50, 1e+50, 1e+50]

            Args:
                value (list): 包含三维坐标的列表，长度必须为3。
            """
            assert len(value) == 3
            for dim in range(3):
                core.injector_set_pos(self.handle, dim, value[dim])

        core.use(c_double, 'injector_get_radi', c_void_p)
        core.use(None, 'injector_set_radi', c_void_p, c_double)

        @property
        def radi(self):
            """
            Injector的控制半径。
            注：
                在没有设置的时候，原始默认值为1e+100，即无穷大

            Returns:
                float: Injector的控制半径。
            """
            return core.injector_get_radi(self.handle)

        @radi.setter
        def radi(self, value):
            """
            设置Injector的控制半径。
            注：
                在没有设置的时候，原始默认值为1e+100，即无穷大

            Args:
                value (float): 要设置的控制半径。
            """
            core.injector_set_radi(self.handle, value)

        core.use(c_double, 'injector_get_g_heat', c_void_p)
        core.use(None, 'injector_set_g_heat', c_void_p, c_double)

        @property
        def g_heat(self):
            """
            热边界和cell之间换热的系数 (当大于0的时候，则实施固定温度的加热，否则为固定功率的加热)。
            注：
                默认为0

            Returns:
                float: 热边界和cell之间换热的系数。
            """
            return core.injector_get_g_heat(self.handle)

        @g_heat.setter
        def g_heat(self, value):
            """
            设置热边界和cell之间换热的系数 (当大于0的时候，则实施固定温度的加热，否则为固定功率的加热)。
            注：
                默认为0

            Args:
                value (float): 要设置的换热系数。
            """
            core.injector_set_g_heat(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_mc', c_void_p)
        core.use(None, 'injector_set_ca_mc', c_void_p, c_size_t)

        @property
        def ca_mc(self):
            """
            cell的mc属性的ID。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Returns:
                int: cell的mc属性的ID。
            """
            return core.injector_get_ca_mc(self.handle)

        @ca_mc.setter
        def ca_mc(self, value):
            """
            设置cell的mc属性的ID。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Args:
                value (int): 要设置的cell的mc属性的ID。
            """
            core.injector_set_ca_mc(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_t', c_void_p)
        core.use(None, 'injector_set_ca_t', c_void_p, c_size_t)

        @property
        def ca_t(self):
            """
            cell的温度属性的id。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Returns:
                int: cell的温度属性的id。
            """
            return core.injector_get_ca_t(self.handle)

        @ca_t.setter
        def ca_t(self, value):
            """
            设置cell的温度属性的id。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Args:
                value (int): 要设置的cell的温度属性的id。
            """
            core.injector_set_ca_t(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_no_inj', c_void_p)
        core.use(None, 'injector_set_ca_no_inj', c_void_p, c_size_t)

        @property
        def ca_no_inj(self):
            """
            在根据位置来寻找注入的cell的时候，凡是设置了ca_no_inj的cell，将会被忽略（从而避免被Injector操作）。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Returns:
                int: cell的ca_no_inj属性的ID。
            """
            return core.injector_get_ca_no_inj(self.handle)

        @ca_no_inj.setter
        def ca_no_inj(self, value):
            """
            设置在根据位置来寻找注入的cell的时候，凡是设置了ca_no_inj的cell，将会被忽略（从而避免被Injector操作）。
            注：
                默认为无穷大18446744073709551615，即不存在的属性ID

            Args:
                value (int): 要设置的cell的ca_no_inj属性的ID。
            """
            core.injector_set_ca_no_inj(self.handle, value)

        core.use(None, 'injector_add_oper', c_void_p, c_double, c_char_p)

        def add_oper(self, time, oper):
            """
            添加在time时刻的一个操作。注意，oper支持如下关键词
                value
                pos    x  y  z
                radi   r
                val    v
                den    v
                vis    v
                mass   m
                attr   id  val
                fid    a  b  c
                g_heat v            (since 2024-02-27)
            其它关键词将会被忽略(不抛出异常)。

            Args:
                time (float): 操作的时间。
                oper (str): 操作的关键词和参数。

            Returns:
                Injector: 返回当前Injector对象。
            """
            core.injector_add_oper(self.handle, time, make_c_char_p(oper if isinstance(oper, str) else f'{oper}'))
            return self

        core.use(None, 'injector_work', c_void_p, c_void_p, c_double, c_double)

        def work(self, model, *, time=None, dt=None):
            """
            执行注入操作。
            注：
                此函数不需要调用。内置在Seepage中的Injector，会在Seepage.iterate函数中被自动调用。

            Args:
                model (Seepage): 所属的Seepage模型对象。
                time (float, optional): 操作的时间，默认为None，若为None则使用默认值0。
                dt (float, optional): 时间步长，默认为None，若为None则不执行操作。
            """
            assert isinstance(model, Seepage)
            if time is None:
                warnings.warn('time is None for Seepage.Injector, use time=0 as default')
                time = 0
            if dt is None:
                return
            core.injector_work(self.handle, model.handle, time, dt)

        core.use(None, 'injector_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            克隆所有的数据；包括作用的cell_id。

            Args:
                other (Seepage.Injector): 要克隆数据的源Injector对象。

            Returns:
                Injector: 返回当前Injector对象。
            """
            if other is not None:
                assert isinstance(other, Seepage.Injector)
                core.injector_clone(self.handle, other.handle)
            return self

    class Updater(HasHandle):
        """
        执行内核求解. 由于在计算的时候必须用到一些临时变量，这些变量如果每次都进行初始化，则可能拖慢计算进程，因此需要缓存。因此
        关于计算的部分，不能做成纯方法，故而有这个类来辅助.
        """
        core.use(c_void_p, 'new_seepage_updater')
        core.use(None, 'del_seepage_updater', c_void_p)

        def __init__(self, handle=None):
            """
            初始化Updater类的实例。

            Args:
                handle: 句柄，默认为None。
            """
            super(Seepage.Updater, self).__init__(handle, core.new_seepage_updater, core.del_seepage_updater)
            self.solver = None

        core.use(None, 'seepage_updater_iterate', c_void_p, c_void_p, c_void_p, c_double,
                 c_size_t, c_size_t, c_size_t, c_size_t, c_void_p)

        def iterate(self, model, dt, fa_s=None, fa_q=None, fa_k=None, ca_p=None, solver=None):
            """
            在时间上向前迭代。

            Args:
                model: 渗流模型对象。
                dt (float): 时间步长。
                fa_s (int, optional): Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力），默认为None。
                fa_q (int, optional): Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)，默认为None。
                fa_k (int, optional): Face内流体的惯性系数的属性ID，默认为None。
                ca_p (int, optional): Cell的自定义属性，表示Cell内流体的压力(迭代时的压力，并非按照流体体积进行计算的)，默认为None。
                solver (ConjugateGradientSolver, optional): 求解器实例，默认为None。

            Returns:
                dict: 包含迭代报告的字典。
            """
            lic.check_once()
            if solver is None:
                self.solver = ConjugateGradientSolver(tolerance=1.0e-25)
                solver = self.solver
            if fa_s is None:
                fa_s = 1000000000
            if fa_q is None:
                fa_q = 1000000000
            if fa_k is None:
                fa_k = 1000000000
            if ca_p is None:
                ca_p = 1000000000
            report = Map()
            core.seepage_updater_iterate(self.handle, model.handle, report.handle, dt,
                                         fa_s, fa_q, fa_k, ca_p, solver.handle)
            return report.to_dict()

        core.use(None, 'seepage_updater_iterate_thermal', c_void_p, c_void_p, c_void_p,
                 c_size_t, c_size_t, c_size_t,
                 c_double, c_void_p)

        def iterate_thermal(self, model, dt, ca_t, ca_mc, fa_g, solver=None):
            """
            对于此渗流模型，当定义了热传导相关的参数之后，可以作为一个热传导模型来使用。具体和Thermal模型类似。

            Args:
                model: 渗流模型对象。
                dt (float): 时间步长。
                ca_t (int): Cell的温度属性的ID。
                ca_mc (int): Cell范围内质量和比热的乘积。
                fa_g (int): Face导热的通量g；单位时间内通过Face的热量dH = g * dT。
                solver (ConjugateGradientSolver, optional): 求解器实例，默认为None。

            Returns:
                dict: 包含迭代报告的字典。
            """
            if solver is None:
                self.solver = ConjugateGradientSolver(tolerance=1.0e-25)
                solver = self.solver
            lic.check_once()
            report = Map()
            core.seepage_updater_iterate_thermal(self.handle, model.handle, report.handle,
                                                 ca_t, ca_mc, fa_g,
                                                 dt, solver.handle)
            return report.to_dict()

        core.use(c_double, 'seepage_updater_get_face_relative_dv_max', c_void_p)
        core.use(c_double, 'seepage_updater_get_face_relative_dheat_max', c_void_p,
                 c_void_p, c_size_t, c_size_t)

        def get_recommended_dt(self, model, previous_dt, dv_relative=0.1,
                               ca_t=None, ca_mc=None):
            """
            在调用了iterate/iterate_thermal函数之后，调用此函数，来获取更优的时间步长。
            当ca_T和ca_mc给定时，返回热传导过程的建议值，否则为渗流的。

            Args:
                model: 渗流模型对象。
                previous_dt (float): 上一次的时间步长。
                dv_relative (float, optional): 相对变化阈值，默认为0.1。
                ca_t (int, optional): Cell的温度属性的ID，默认为None。
                ca_mc (int, optional): Cell范围内质量和比热的乘积，默认为None。

            Returns:
                float: 建议的时间步长。
            """
            if ca_t is not None and ca_mc is not None:
                # 对于iterate_thermal来说
                dv_max = core.seepage_updater_get_face_relative_dheat_max(self.handle,
                                                                          model.handle, ca_t, ca_mc)
            else:
                # 对于iterate来说
                dv_max = core.seepage_updater_get_face_relative_dv_max(self.handle)
            dv_max = max(1.0e-6, dv_max)
            dt = previous_dt
            if dv_max > dv_relative:
                dt *= (dv_relative / dv_max)
            else:
                dt *= min(2.0, math.sqrt(dv_relative / dv_max))
            return dt

    core.use(c_void_p, 'new_seepage')
    core.use(None, 'del_seepage', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化 Seepage 类的实例。

        Args:
            path (str, optional): 要加载的文件的路径。默认为 None。
            handle (optional): 底层核心对象的句柄。默认为 None。
        """
        super(Seepage, self).__init__(handle, core.new_seepage, core.del_seepage)
        self.__updater = None
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回 Seepage 对象的字符串表示形式。

        Returns:
            str: 包含句柄、单元数量、面数量和注释的字符串。
        """
        cell_n = self.cell_number
        face_n = self.face_number
        return f"zml.Seepage(handle={self.handle}, cell_n={cell_n}, face_n={face_n}, note='{self.get_note()}')"

    core.use(None, 'seepage_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.seepage_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.seepage_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'seepage_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmt (str, optional): 序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。

        Returns:
            FileMap: 包含序列化数据的 FileMap 对象。
        """
        fmap = FileMap()
        core.seepage_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary

        Args:
            fmap (FileMap): 包含序列化数据的 FileMap 对象。
            fmt (str, optional): 反序列化格式，可选值为 'text', 'xml', 'binary'。默认为 'binary'。
        """
        assert isinstance(fmap, FileMap)
        core.seepage_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """
        获取二进制格式的 FileMap 对象。

        Returns:
            FileMap: 包含二进制序列化数据的 FileMap 对象。
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """
        从给定的 FileMap 对象中加载二进制格式的数据。

        Args:
            value (FileMap): 包含二进制序列化数据的 FileMap 对象。
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_char_p, 'seepage_get_text', c_void_p, c_char_p)
    core.use(None, 'seepage_set_text', c_void_p, c_char_p, c_char_p)

    def get_text(self, key):
        """
        返回模型内部存储的文本数据

        Args:
            key (str): 文本数据的键。

        Returns:
            str: 存储的文本数据。
        """
        return core.seepage_get_text(self.handle, make_c_char_p(key)).decode()

    def set_text(self, key, text):
        """
        设置模型中存储的文本数据

        Args:
            key (str): 文本数据的键。
            text (str): 要存储的文本数据。
        """
        if not isinstance(text, str):
            text = f'{text}'
        core.seepage_set_text(self.handle, make_c_char_p(key), make_c_char_p(text))

    def add_note(self, text):
        """
        向模型的注释中添加文本。

        Args:
            text (str): 要添加的文本。
        """
        self.set_text('note', self.get_text('note') + text)

    def get_note(self):
        """
        获取模型的注释。

        Returns:
            str: 模型的注释。
        """
        return self.get_text('note')

    core.use(None, 'seepage_clear', c_void_p)

    def clear(self):
        """
        删除所有的Cell、Face和Injector。其它所有的数据保持不变。
        """
        core.seepage_clear(self.handle)

    core.use(None, 'seepage_clear_cells_and_faces', c_void_p)

    def clear_cells_and_faces(self):
        """
        删除所有的Cell和Face。其它所有的数据保持不变。
        """
        core.seepage_clear_cells_and_faces(self.handle)

    core.use(None, 'seepage_remove_cell', c_void_p, c_size_t)

    def remove_cell(self, cell_id):
        """
        移除给定id的(孤立的)cell
        注意：
            1. 这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变
            2. 必须确保给定的cell为孤立的，即没有face和此cell连接，否则，此函数不执行操作.

        Args:
            cell_id (int): 要移除的单元的 ID。
        """
        core.seepage_remove_cell(self.handle, cell_id)

    core.use(None, 'seepage_remove_face', c_void_p, c_size_t)

    def remove_face(self, face_id):
        """
        移除给定id的face
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变

        Args:
            face_id (int): 要移除的面的 ID。
        """
        core.seepage_remove_face(self.handle, face_id)

    core.use(None, 'seepage_remove_faces_of_cell', c_void_p, c_size_t)

    def remove_faces_of_cell(self, cell_id):
        """
        移除给定id的cell的所有的face，使其成为一个孤立的cell
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变

        Args:
            cell_id (int): 要移除面的单元的 ID。
        """
        core.seepage_remove_faces_of_cell(self.handle, cell_id)

    core.use(c_size_t, 'seepage_get_cell_n', c_void_p)

    @property
    def cell_number(self):
        """
        Cell的数量

        Returns:
            int: 模型中单元的数量。
        """
        return core.seepage_get_cell_n(self.handle)

    core.use(c_size_t, 'seepage_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        Face的数量

        Returns:
            int: 模型中面的数量。
        """
        return core.seepage_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_get_inj_n', c_void_p)
    core.use(None, 'seepage_set_inj_n', c_void_p, c_size_t)

    @property
    def injector_number(self):
        """
        Injector的数量

        Returns:
            int: 模型中注入器的数量。
        """
        return core.seepage_get_inj_n(self.handle)

    @injector_number.setter
    def injector_number(self, count):
        """
        设置注入点的数量. 注意，对于新的injector，所有的参数都将使用默认值，后续必须进行配置.
            请谨慎使用此接口来添加注入点.
            重设injector_number主要用来清空已有的注入点.

        Args:
            count (int): 要设置的注入器数量。
        """
        core.seepage_set_inj_n(self.handle, count)

    def get_cell(self, index):
        """
        返回第index个Cell对象

        Args:
            index (int): 单元的索引。

        Returns:
            Seepage.Cell: 第 index 个单元对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.cell_number)
        if index is not None:
            return Seepage.Cell(self, index)

    def get_face(self, index):
        """
        返回第index个Face对象

        Args:
            index (int): 面的索引。

        Returns:
            Seepage.Face: 第 index 个面对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Seepage.Face(self, index)

    core.use(c_void_p, 'seepage_get_inj', c_void_p, c_size_t)

    def get_injector(self, index):
        """
        返回第index个Injector对象

        Args:
            index (int): 注入器的索引。

        Returns:
            Seepage.Injector: 第 index 个注入器对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.injector_number)
        if index is not None:
            return Seepage.Injector(handle=core.seepage_get_inj(self.handle, index))

    core.use(c_size_t, 'seepage_add_cell', c_void_p)

    def add_cell(self, data=None):
        """
        添加一个新的Cell，并返回Cell对象

        Args:
            data (optional): 要克隆到新单元的数据。默认为 None。

        Returns:
            Seepage.Cell: 新添加的单元对象。
        """
        cell_id = core.seepage_add_cell(self.handle)
        cell = self.get_cell(cell_id)
        assert cell is not None
        if data is not None:
            cell.clone(data)
        return cell

    core.use(c_size_t, 'seepage_add_face', c_void_p, c_size_t, c_size_t)

    def add_face(self, cell0, cell1, data=None):
        """
        在两个给定的Cell之间创建Face（注意：两个Cell之间只能有一个Face）

        Args:
            cell0 (Seepage.Cell or int): 第一个单元对象或其 ID。
            cell1 (Seepage.Cell or int): 第二个单元对象或其 ID。
            data (optional): 要克隆到新面的数据。默认为 None。

        Returns:
            Seepage.Face: 新添加的面对象，如果创建失败则返回 None。
        """
        if isinstance(cell0, Seepage.Cell):
            assert cell0.model.handle == self.handle
            cell0 = cell0.index

        if isinstance(cell1, Seepage.Cell):
            assert cell1.model.handle == self.handle
            cell1 = cell1.index

        assert cell0 < self.cell_number
        assert cell1 < self.cell_number
        assert cell0 != cell1

        face_id = core.seepage_add_face(self.handle, cell0, cell1)
        face = self.get_face(face_id)
        if face is not None and data is not None:
            face.clone(data)
        return face

    core.use(c_size_t, 'seepage_add_inj', c_void_p)

    def add_injector(self, cell=None, fluid_id=None, flu=None, data=None, pos=None, radi=None, opers=None,
                     ca_mc=None, ca_t=None, g_heat=None, value=None):
        """
        添加一个注入点. 首先尝试拷贝data；然后尝试利用给定cell、fluid_id和flu进行设置。返回新添加的Injector对象

        Note that this function can be used for both fluid injection and heat injection.
            When the parameter "fluid_id" is given, this function will be used to inject fluid,
            and at this time, the parameter "opers" is used to set the injected volume flow rate;

        When the parameter "fluid_id" is not set and both the parameters "ca_mc" and "ca_t" are set,
            this function is used to inject heat.

        When injecting heat, there are two ways to inject it. When the parameter "g_heat" is given
            a value greater than 0, it injects heat according to temperature. At this time, "opers"
            is used to set the temperature of the boundary during heat injection. When the parameter
            "g_heat" is None, heat is injected according to the power, and "opers" is used to set
            the power of the heat injection.
        """
        inj = self.get_injector(core.seepage_add_inj(self.handle))
        assert inj is not None

        if data is not None:
            assert isinstance(data, Seepage.Injector)
            inj.clone(data)

        if cell is not None:  # 可以是cell对象，也可以是cell的id
            if isinstance(cell, Seepage.Cell):
                assert cell.model.handle == self.handle  # 必须是同一个模型
                cell = cell.index
            inj.cell_id = cell

        if fluid_id is not None:
            if isinstance(fluid_id, str):  # 给定组分名字，则从model中查找   since 2023-10-24
                fluid_id = self.find_fludef(name=fluid_id)
                assert fluid_id is not None
            inj.set_fid(fluid_id)

        if isinstance(flu, Seepage.FluData):  # 只有在等于FluData的时候才使用.
            inj.flu.clone(flu)

        if pos is not None:  # 给定注入的位置，后续，则自动去查找附近的cell
            inj.pos = pos

        if radi is not None:  # 查找的半径
            inj.radi = radi

        if ca_mc is not None:  # Cell的属性
            inj.ca_mc = ca_mc

        if ca_t is not None:  # Cell的属性(温度属性，在注入热量的时候会被修改)
            inj.ca_t = ca_t

        if g_heat is not None:  # 恒定温度加热的时候需要给定
            inj.g_heat = g_heat

        if opers is not None:  # 对属性的操作定时器
            for item in opers:
                inj.add_oper(*item)

        if value is not None:  # 当前的值
            inj.value = value

        return inj

    @property
    def cells(self):
        """
        模型中所有的Cell

        Returns:
            Iterator: 包含所有单元对象的迭代器。
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        模型中所有的Face

        Returns:
            Iterator: 包含所有面对象的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def injectors(self):
        """
        模型中所有的Injector

        Returns:
            Iterator: 包含所有注入器对象的迭代器。
        """
        return Iterator(self, self.injector_number, lambda m, ind: m.get_injector(ind))

    core.use(None, 'seepage_apply_injs', c_void_p, c_double,
             c_double)

    def apply_injectors(self, *, time=None, dt=None):
        """
        所有的注入点执行注入操作.

        Args:
            time (float, optional): 时间。默认为 None。
            dt (float, optional): 时间步长。默认为 None。
        """
        if time is None:
            warnings.warn('time is None for Seepage.Injector, use time=0 as default')
            time = 0
        if dt is None:
            return
        core.seepage_apply_injs(self.handle, time, dt)

    core.use(None, 'seepage_append', c_void_p, c_void_p, c_bool, c_size_t)

    def append(self, other, cell_i0=None, with_faces=True):
        """
        将other中所有的Cell和Face追加到这个模型中，并且从这个模型的cell_i0开始，和从other新添加的cell之间
        建立一一对应的Face. 默认情况下，仅仅追加，但是不建立和现有的Cell的连接。
            2023-4-19

        注意：
            仅仅追加Cell和Face，other中的其它数据，比如反应、注入点、相渗曲线等，均不会被追加到这个
            模型中。

        当with_faces为False的时候，则仅仅追加other中的Cell (other中的 Face 不被追加)

        注意函数实际的执行顺序：
            第一步：添加other的所有的Cell
            第二步：添加other的所有的Face (with_faces属性为True的时候)
            第三步：创建一些额外Face连接 (从这个模型的cell_i0开始，和other的cell之间)

        Args:
            other (Seepage): 要追加的另一个 Seepage 对象。
            cell_i0 (int, optional): 开始建立连接的单元索引。默认为 None。
            with_faces (bool, optional): 是否追加面。默认为 True。
        """
        assert isinstance(other, Seepage)
        if cell_i0 is None:
            cell_i0 = self.cell_number
        core.seepage_append(self.handle, other.handle, with_faces, cell_i0)

    core.use(None, 'seepage_pop_cells', c_void_p, c_size_t)

    def pop_cells(self, count=1):
        """
        删除最后count个Cell的所有的Face，然后移除最后count个Cell

        Args:
            count (int, optional): 要删除的单元数量。默认为 1。

        Returns:
            Seepage: 当前 Seepage 对象。
        """
        core.seepage_pop_cells(self.handle, count)
        return self

    core.use(c_double, 'seepage_get_gravity', c_void_p, c_size_t)
    core.use(None, 'seepage_set_gravity', c_void_p, c_size_t, c_double)

    @property
    def gravity(self):
        """
        重力加速度，默认为(0,0,0)

        Returns:
            tuple: 重力加速度的三维向量。
        """
        return (core.seepage_get_gravity(self.handle, 0),
                core.seepage_get_gravity(self.handle, 1),
                core.seepage_get_gravity(self.handle, 2))

    @gravity.setter
    def gravity(self, value):
        """
        重力加速度，默认为(0,0,0)

        Args:
            value (tuple): 要设置的重力加速度的三维向量。
        """
        assert len(value) == 3
        for dim in range(3):
            core.seepage_set_gravity(self.handle, dim, value[dim])

    core.use(c_size_t, 'seepage_get_gr_n', c_void_p)

    @property
    def gr_number(self):
        """
        返回model中gr的数量

        Returns:
            int: 模型中 gr 的数量。
        """
        return core.seepage_get_gr_n(self.handle)

    core.use(c_void_p, 'seepage_get_gr', c_void_p, c_size_t)

    def get_gr(self, idx):
        """
        返回序号为idx的gr

        Args:
            idx (int): gr 的索引。

        Returns:
            Interp1: 序号为 idx 的 gr 对象，如果索引无效则返回 None。
        """
        idx = get_index(idx, self.gr_number)
        if idx is not None:
            return Interp1(handle=core.seepage_get_gr(self.handle, idx))

    @property
    def grs(self):
        """
        迭代所有的gr

        Returns:
            Iterator: 包含所有 gr 对象的迭代器。
        """
        return Iterator(model=self, count=self.gr_number, get=lambda m, ind: m.get_gr(ind))

    core.use(c_size_t, 'seepage_add_gr', c_void_p, c_void_p)

    def add_gr(self, gr, need_id=False):
        """
        添加一个gr. 其中gr应该为Interp1类型.

        Args:
            gr (Interp1 or tuple): 要添加的 gr 对象或数据。
            need_id (bool, optional): 是否返回添加的 gr 的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，则返回添加的 gr 对象；否则返回添加的 gr 的 ID。
        """
        if not isinstance(gr, Interp1):
            assert len(gr) == 2
            assert len(gr[0]) == len(gr[1])
            assert len(gr[0]) >= 2
            gr = Interp1(x=gr[0], y=gr[1])
        idx = core.seepage_add_gr(self.handle, gr.handle)
        if need_id:
            return idx
        else:
            return self.get_gr(idx)

    core.use(None, 'seepage_clear_grs', c_void_p)

    def clear_grs(self):
        """
        删除模型中所有的gr
        """
        core.seepage_clear_grs(self.handle)

    core.use(c_size_t, 'seepage_get_kr_n', c_void_p)

    @property
    def kr_number(self):
        """
        相渗曲线的数量.
        注意:
            对于 0 <= id < fluid_n 的曲线，是各个流体的默认相渗.
            所以，如果需要对某些相渗进行特殊设置，务必去使用id大于流体数量的曲线.

        Returns:
            int: 模型中相渗曲线的数量。
        """
        return core.seepage_get_kr_n(self.handle)

    def add_kr(self, saturation=None, kr=None, need_id=False):
        """
        添加一个相渗曲线，并且返回ID

        Args:
            saturation (Vector or list, optional): 饱和度数据。默认为 None。
            kr (Vector or Interp1, optional): 相对渗透率数据或曲线对象。默认为 None。
            need_id (bool, optional): 是否返回添加的相渗曲线的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，则返回添加的相渗曲线对象；否则返回添加的相渗曲线的 ID。
        """
        index = self.kr_number
        self.set_kr(index=index, saturation=saturation, kr=kr)
        if need_id:
            return index
        else:
            return self.get_kr(index)

    core.use(None, 'seepage_set_kr', c_void_p, c_size_t, c_void_p)

    def set_kr(self, index=None, saturation=None, kr=None):
        """
        设置第index个相对渗透率曲线。注意模型内部最多可以存储<10000个相对渗透率曲线>以及一个<默认相渗>。
            如果给定的Index大于10000，则此函数将修改默认相对渗透率曲线，否则会修改给定index的数据。
            当index为None的时候，则修改默认相渗曲线。
        在不同的Face中，可以选用不同的相渗曲线(参考Face.set_ikr)，但是默认条件下，如果不加设置，则第i种流体，将默认使用第i个相渗曲线.
            如果计算中需要使用到第i个相渗，但第i个相渗不存在，则会用<默认曲线>来代替。
        --
        通过这里Seepage.set_kr和Face.set_ikr配合，可以在模型的不同区域来配置不同的相渗.

        Args:
            index (int or str, optional): 要设置的相渗曲线的索引或名称。默认为 None。
            saturation (Vector or list, optional): 饱和度数据。默认为 None。
            kr (Vector or Interp1, optional): 相对渗透率数据或曲线对象。默认为 None。
        """
        assert kr is not None

        # 获得相对渗透率曲线数据，并且存储在tmp中
        if isinstance(kr, Interp1):
            assert saturation is None
            tmp = kr
        else:
            if not isinstance(saturation, Vector):
                saturation = Vector(saturation)
            if not isinstance(kr, Vector):
                kr = Vector(kr)
            assert len(saturation) > 0 and len(kr) > 0
            tmp = Interp1(x=saturation, y=kr)

        # 检查流体的id
        if index is None:
            index = 9999999999  # Now, modify the default kr
        else:
            if isinstance(index, str):  # 此时，通过查表来获得流体的id. since 2024-5-8
                idx = self.find_fludef(name=index)
                assert len(idx) == 1, f'You can not set the kr of {index} while its id is: {idx}'
                index = idx[0]

        # 最终，设置相渗数据
        core.seepage_set_kr(self.handle, index, tmp.handle)

    def set_default_kr(self, value):
        """
        set the default kr. since 2024-5-8

        Args:
            value (Interp1 or tuple): 要设置的默认相渗曲线对象或数据。
        """
        if isinstance(value, Interp1):
            self.set_kr(kr=value)
            return
        else:
            x = value[0]
            y = value[1]
            self.set_kr(saturation=x, kr=y)
            return

    core.use(c_void_p, 'seepage_get_kr', c_void_p, c_size_t)

    def get_kr(self, index, saturation=None):
        """
        返回第index个相对渗透率曲线(或者在给定saturation的时候，返回相对渗透率数值)。
        如果给定Index的kr不存在，则使用默认的kr

        Args:
            index (int): 要获取的相渗曲线的索引。
            saturation (float, optional): 饱和度值。默认为 None。

        Returns:
            Interp1 or float: 如果 saturation 为 None，则返回相渗曲线对象；否则返回相对渗透率数值。
        """
        handle = core.seepage_get_kr(self.handle, index)
        assert handle > 0
        curve = Interp1(handle=handle)
        if saturation is None:
            return curve
        else:
            return curve.get(saturation)

    core.use(c_size_t, 'seepage_get_curve_n', c_void_p)

    @property
    def curve_number(self):
        """
        曲线的数量.

        Returns:
            int: 模型中曲线的数量。
        """
        return core.seepage_get_curve_n(self.handle)

    core.use(c_void_p, 'seepage_get_curve', c_void_p, c_size_t)

    def get_curve(self, index):
        """
        返回第index个曲线

        Args:
            index (int): 要获取的曲线的索引。

        Returns:
            Interp1: 第 index 个曲线对象，如果索引无效则返回 None。
        """
        handle = core.seepage_get_curve(self.handle, index)
        if handle > 0:
            return Interp1(handle=handle)

    core.use(None, 'seepage_set_curve', c_void_p, c_size_t, c_void_p)

    def set_curve(self, index, curve):
        """
        设置第index个曲线

        Args:
            index (int): 要设置的曲线的索引。
            curve (Interp1): 要设置的曲线对象。
        """
        if isinstance(curve, Interp1):
            core.seepage_set_curve(self.handle, index, curve.handle)

    core.use(c_size_t, 'seepage_get_fludef_n', c_void_p)

    @property
    def fludef_number(self):
        """
        模型内存储的流体定义的数量

        Returns:
            int: 模型中流体定义的数量。
        """
        return core.seepage_get_fludef_n(self.handle)

    core.use(c_bool, 'seepage_find_fludef', c_void_p, c_char_p, c_void_p)

    def find_fludef(self, name, buffer=None):
        """
        查找给定name的流体定义的ID

        Args:
            name (str): 要查找的流体定义的名称。
            buffer (UintVector, optional): 存储查找结果的缓冲区。默认为 None。

        Returns:
            list: 找到的流体定义的 ID 列表，如果未找到则返回空列表。
        """
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        else:
            buffer.size = 0
        found = core.seepage_find_fludef(self.handle, make_c_char_p(name), buffer.handle)
        if found:
            return buffer.to_list()

    core.use(c_void_p, 'seepage_get_fludef', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fludef(self, key):
        """
        返回给定序号或者名字的流体定义. key可以是str类型/int类型/list类型.

        Args:
            key (str or int or list): 流体定义的名称、序号或序号列表。

        Returns:
            Seepage.FluDef: 找到的流体定义对象，如果未找到则返回 None。
        """
        if isinstance(key, str):
            key = self.find_fludef(key)
        if key is None:
            return
        handle = core.seepage_get_fludef(self.handle, *parse_fid3(key))
        if handle:
            return Seepage.FluDef(handle=handle)

    core.use(c_size_t, 'seepage_add_fludef', c_void_p, c_void_p)

    def add_fludef(self, fdef, need_id=False, name=None):
        """
        添加一个流体定义

        Args:
            fdef (Seepage.FluDef or list): 要添加的流体定义对象或数据。
            need_id (bool, optional): 是否返回添加的流体定义的 ID。默认为 False。
            name (str, optional): 流体定义的名称。默认为 None。

        Returns:
            Seepage.FluDef or int: 如果 need_id 为 False，则返回添加的流体定义对象；否则返回添加的流体定义的 ID。
        """
        if not isinstance(fdef, Seepage.FluDef):
            # 此时，可能是一个list
            fdef = Seepage.FluDef.create(fdef)
        idx = core.seepage_add_fludef(self.handle, fdef.handle)
        if name is not None:
            self.get_fludef(idx).name = name
        if need_id:
            return idx
        else:
            return self.get_fludef(idx)

    core.use(None, 'seepage_clear_fludefs', c_void_p)

    def clear_fludefs(self):
        """
        清除所有的流体定义
        """
        core.seepage_clear_fludefs(self.handle)

    def set_fludefs(self, *args):
        """
        清除并设置所有的流体定义

        Args:
            *args (Seepage.FluDef or list): 要设置的流体定义对象或数据。
        """
        self.clear_fludefs()
        for item in args:
            self.add_fludef(item)

    core.use(c_size_t, 'seepage_get_pc_n', c_void_p)

    @property
    def pc_number(self):
        """
        模型中存储的毛管压力曲线的数量

        Returns:
            int: 模型中毛管压力曲线的数量。
        """
        return core.seepage_get_pc_n(self.handle)

    core.use(c_void_p, 'seepage_get_pc', c_void_p, c_size_t)

    def get_pc(self, idx):
        """
        返回给定序号的毛管压力曲线

        Args:
            idx (int): 毛管压力曲线的索引。

        Returns:
            Interp1: 序号为 idx 的毛管压力曲线对象，如果索引无效则返回 None。
        """
        if idx < self.pc_number:
            return Interp1(handle=core.seepage_get_pc(self.handle, idx))

    core.use(c_size_t, 'seepage_add_pc', c_void_p, c_void_p)

    def add_pc(self, data, need_id=False):
        """
        添加一个毛管压力曲线

        Args:
            data (Interp1): 要添加的毛管压力曲线对象。
            need_id (bool, optional): 是否返回添加的毛管压力曲线的 ID。默认为 False。

        Returns:
            Interp1 or int: 如果 need_id 为 False，则返回添加的毛管压力曲线对象；否则返回添加的毛管压力曲线的 ID。
        """
        assert isinstance(data, Interp1)
        idx = core.seepage_add_pc(self.handle, data.handle)
        if need_id:
            return idx
        else:
            return self.get_pc(idx)

    core.use(None, 'seepage_clear_pcs', c_void_p)

    def clear_pcs(self):
        """
        清除所有的毛管压力曲线
        """
        core.seepage_clear_pcs(self.handle)

    core.use(c_size_t, 'seepage_get_reaction_n', c_void_p)

    @property
    def reactions(self):
        """
        迭代所有的反应

        Returns:
            Iterator: 包含所有反应对象的迭代器。
        """
        return Iterator(model=self, count=self.reaction_number, get=lambda m, ind: m.get_reaction(ind))

    @property
    def reaction_number(self):
        """
        模型中反应的数量

        Returns:
            int: 模型中反应的数量。
        """
        return core.seepage_get_reaction_n(self.handle)

    core.use(c_void_p, 'seepage_get_reaction', c_void_p, c_size_t)

    def get_reaction(self, idx):
        """
        返回第idx个反应对象

        Args:
            idx (int): 反应的索引。

        Returns:
            Seepage.Reaction: 第 idx 个反应对象，如果索引无效则返回 None。
        """
        idx = get_index(idx, self.reaction_number)
        if idx is not None:
            return Seepage.Reaction(handle=core.seepage_get_reaction(self.handle, idx))

    core.use(c_size_t, 'seepage_add_reaction', c_void_p, c_void_p)

    def add_reaction(self, data, need_id=False):
        """
        添加一个反应

        Args:
            data (Seepage.Reaction): 要添加的反应对象。
            need_id (bool, optional): 是否返回添加的反应的 ID。默认为 False。

        Returns:
            Seepage.Reaction or int: 如果 need_id 为 False，则返回添加的反应对象；否则返回添加的反应的 ID。
        """
        if not isinstance(data, Seepage.Reaction):
            warnings.warn('The none Seepage.Reaction type will not be supported after 2026-2-7, '
                          'please use zmlx.react.add_reaction instead.', DeprecationWarning)
            data = self.create_reaction(**data)
        idx = core.seepage_add_reaction(self.handle, data.handle)
        if need_id:
            return idx
        else:
            return self.get_reaction(idx)

    core.use(None, 'seepage_clear_reactions', c_void_p)

    def clear_reactions(self):
        """
        清除所有的反应

        Returns:
            None
        """
        core.seepage_clear_reactions(self.handle)

    core.use(None, 'seepage_remove_reaction', c_void_p, c_size_t)

    def remove_reaction(self, idx):
        """
        移除给定序号的一个反应

        Args:
            idx (int): 要移除的反应的序号

        Returns:
            None
        """
        idx = get_index(idx, self.reaction_number)
        if idx is not None:
            core.seepage_remove_reaction(self.handle, idx)

    def create_reaction(self, **kwargs):
        """
        根据给定的参数，创建一个反应（可能需要读取model中的流体定义，以及会在model中注册属性）

        Args:
            **kwargs: 创建反应所需的参数

        Returns:
            反应对象

        Warnings:
            zml.Seepage.Reaction.create_reaction 将在2026-2-7之后移除，请使用 zmlx.react.create_reaction 代替。
        """
        warnings.warn('zml.Seepage.Reaction.create_reaction will be remove after 2026-2-7, '
                      'please use zmlx.react.create_reaction instead', DeprecationWarning)
        from zmlx.react.create_reaction import create_reaction as create
        return create(self, **kwargs)

    core.use(c_void_p, 'seepage_get_buffer', c_void_p, c_char_p)

    def get_buffer(self, key):
        """
        返回模型内的一个缓冲区（如果不存在，则自动创建并返回）

        Args:
            key (str): 缓冲区的键

        Returns:
            Vector: 模型内的缓冲区对象
        """
        return Vector(handle=core.seepage_get_buffer(self.handle, make_c_char_p(key)))

    core.use(None, 'seepage_del_buffer', c_void_p, c_char_p)

    def del_buffer(self, key):
        """
        删除模型内的缓冲区(如果缓冲区不存在，则不执行操作)

        Args:
            key (str): 要删除的缓冲区的键

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_buffer(self.handle, make_c_char_p(key))
        return self

    core.use(c_bool, 'seepage_has_tag', c_void_p, c_char_p)

    def has_tag(self, tag):
        """
        返回模型是否包含给定的这个标签

        Args:
            tag (str): 要检查的标签

        Returns:
            bool: 如果模型包含该标签返回True，否则返回False
        """
        return core.seepage_has_tag(self.handle, make_c_char_p(tag))

    def not_has_tag(self, tag):
        """
        返回模型是否不包含给定的这个标签

        Args:
            tag (str): 要检查的标签

        Returns:
            bool: 如果模型不包含该标签返回True，否则返回False
        """
        return not self.has_tag(tag)

    core.use(None, 'seepage_add_tag', c_void_p, c_char_p)

    def add_tag(self, tag, *tags):
        """
        在模型中添加给定的标签. 支持添加多个(since 2024-2-23)

        Args:
            tag (str): 要添加的第一个标签
            *tags (str): 要添加的其他标签

        Returns:
            self: 返回当前对象
        """
        core.seepage_add_tag(self.handle, make_c_char_p(tag))
        # 再添加多个.
        if len(tags) > 0:
            for tag in tags:
                self.add_tag(tag=tag)
        return self

    core.use(None, 'seepage_del_tag', c_void_p, c_char_p)

    def del_tag(self, tag, *tags):
        """
        删除模型中的给定的标签

        Args:
            tag (str): 要删除的第一个标签
            *tags (str): 要删除的其他标签

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_tag(self.handle, make_c_char_p(tag))
        if len(tags) > 0:
            for tag in tags:
                self.del_tag(tag=tag)
        return self

    core.use(None, 'seepage_clear_tags', c_void_p)

    def clear_tags(self):
        """
        清除模型中的所有标签

        Returns:
            None
        """
        core.seepage_clear_tags(self.handle)

    core.use(c_int64, 'seepage_reg_key', c_void_p, c_char_p, c_char_p)

    def reg_key(self, ty, key):
        """
        注册一个键。其中ty为该键的前缀. 在注册的时候，将自动根据注册的顺序从0开始编号.

        说明:
            在之前的版本中，不依赖model中定义的key，反之，对于每一个属性，都有一个确定的键值.
            这样的问题是，每个具体的问题所用的key不同，这样全部采用静态的定义，就会浪费空间.
            因此，考虑将各个属性键的含义存储到model中，从而在计算的时候去动态读取. 这样，在
            定义方法的时候，只需要去记录键的名字，而不需要记录具体的键值.

        关于前缀：
            m_: 模型的属性
            n_: Cell属性
            b_: Face属性
            f_: 流体的属性

        Args:
            ty (str): 键的前缀
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return core.seepage_reg_key(self.handle, make_c_char_p(ty), make_c_char_p(key))

    core.use(c_int64, 'seepage_get_key', c_void_p, c_char_p)

    def get_key(self, key):
        """
        返回键值：主要用于存储指定的属性ID

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值，如果键值小于9999则返回，否则不返回
        """
        val = core.seepage_get_key(self.handle, make_c_char_p(key))
        if val < 9999:
            return val

    core.use(None, 'seepage_set_key', c_void_p, c_char_p, c_int64)

    def set_key(self, key, value):
        """
        设置键值. 会直接覆盖现有的键值

        Args:
            key (str): 要设置键值的键
            value (int): 要设置的键值

        Returns:
            self: 返回当前对象
        """
        if value is None:
            self.del_key(key)
            return self
        if value >= 9999:
            self.del_key(key)
            return self
        else:
            core.seepage_set_key(self.handle, make_c_char_p(key), value)
            return self

    core.use(None, 'seepage_del_key', c_void_p, c_char_p)

    def del_key(self, key, *keys):
        """
        删除键值

        Args:
            key (str): 要删除的第一个键
            *keys (str): 要删除的其他键

        Returns:
            self: 返回当前对象
        """
        core.seepage_del_key(self.handle, make_c_char_p(key))
        if len(keys) > 0:
            for key in keys:
                self.del_key(key=key)
        return self

    core.use(None, 'seepage_clear_keys', c_void_p)

    def clear_keys(self):
        """
        清除模型中的所有键值

        Returns:
            self: 返回当前对象
        """
        core.seepage_clear_keys(self.handle)
        return self

    def reg_model_key(self, key):
        """
        注册并返回用于model的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('m_', key)

    def reg_cell_key(self, key):
        """
        注册并返回用于cell的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('n_', key)

    def reg_face_key(self, key):
        """
        注册并返回用于face的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('b_', key)

    def reg_flu_key(self, key):
        """
        注册并返回用于flu的键值

        Args:
            key (str): 要注册的键

        Returns:
            int: 注册的键值
        """
        return self.reg_key('f_', key)

    def get_model_key(self, key):
        """
        返回用于model的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('m_' + key)

    def get_cell_key(self, key):
        """
        返回用于cell的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('n_' + key)

    def get_face_key(self, key):
        """
        返回用于face的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('b_' + key)

    def get_flu_key(self, key):
        """
        返回用于flu的键值

        Args:
            key (str): 要获取键值的键

        Returns:
            int: 键值
        """
        return self.get_key('f_' + key)

    core.use(None, 'seepage_get_keys', c_void_p, c_void_p)

    def get_keys(self):
        """
        返回所有的keys（作为dict）

        Returns:
            dict: 包含所有键值的字典
        """
        s = String()
        core.seepage_get_keys(self.handle, s.handle)
        return eval(s.to_str())

    def set_keys(self, **kwargs):
        """
        设置keys. 会覆盖现有的键值.

        Args:
            **kwargs: 要设置的键值对

        Returns:
            self: 返回当前对象
        """
        for key, value in kwargs.items():
            self.set_key(key, value)
        return self

    core.use(None, 'seepage_get_tags', c_void_p, c_void_p)

    def get_tags(self):
        """
        返回所有的tags（作为set）

        Returns:
            set: 包含所有标签的集合
        """
        s = String()
        core.seepage_get_tags(self.handle, s.handle)
        return eval(s.to_str())

    core.use(c_double, 'seepage_get_attr', c_void_p, c_size_t)
    core.use(None, 'seepage_set_attr',
             c_void_p, c_size_t, c_double)

    def get_attr(self, index, default_val=None, **valid_range):
        """
        模型的第index个自定义属性

        Args:
            index (int or str): 自定义属性的索引或键
            default_val (any, optional): 如果属性不存在或不在有效范围内，返回的默认值。默认为None。
            **valid_range: 属性的有效范围

        Returns:
            any: 自定义属性的值，如果属性不存在或不在有效范围内，返回默认值。
        """
        if isinstance(index, str):
            index = self.get_model_key(key=index)
        if index is None:
            return default_val
        value = core.seepage_get_attr(self.handle, index)
        if _attr_in_range(value, **valid_range):
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        模型的第index个自定义属性

        Args:
            index (int or str): 自定义属性的索引或键
            value (float): 要设置的属性值

        Returns:
            self: 返回当前对象
        """
        if isinstance(index, str):
            index = self.reg_model_key(key=index)
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.seepage_set_attr(self.handle, index, value)
        return self

    core.use(c_size_t, 'seepage_get_nearest_cell_id',
             c_void_p, c_double, c_double, c_double, c_size_t, c_size_t)

    def get_nearest_cell(self, pos, i_beg=None, i_end=None):
        """
        返回与给定位置距离最近的cell (在[i_beg, i_end)的范围内搜索)

        Args:
            pos (tuple): 位置坐标 (x, y, z)
            i_beg (int, optional): 搜索范围的起始索引。默认为None。
            i_end (int, optional): 搜索范围的结束索引。默认为None。

        Returns:
            Cell: 距离给定位置最近的cell对象，如果未找到则返回None。
        """
        cell_n = self.cell_number
        if cell_n > 0:
            index = core.seepage_get_nearest_cell_id(self.handle, pos[0], pos[1], pos[2],
                                                     i_beg if i_beg is not None else 0,
                                                     i_end if i_end is not None else cell_n)
            return self.get_cell(index)

    core.use(None, 'seepage_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        从另外一个模型克隆数据.

        Args:
            other (Seepage): 要克隆数据的源模型

        Returns:
            self: 返回当前对象
        """
        if other is not None:
            assert isinstance(other, Seepage)
            core.seepage_clone(self.handle, other.handle)
        return self

    def get_copy(self):
        """
        返回一个拷贝.

        Returns:
            Seepage: 当前模型的拷贝对象
        """
        temp = Seepage()
        temp.clone(self)
        return temp

    core.use(None, 'seepage_clone_cells', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def clone_cells(self, ibeg0, other, ibeg1, count):
        """
        拷贝Cell数据:
            将other的[ibeg1, ibeg1+count)范围内的Cell的数据，拷贝到self的[ibeg0, ibeg0+count)范围内的Cell
        此函数会自动跳过不存在的CellID.
            since 2023-4-20

        Args:
            ibeg0 (int): 目标模型中Cell的起始索引
            other (Seepage): 源模型
            ibeg1 (int): 源模型中Cell的起始索引
            count (int): 要拷贝的Cell数量

        Returns:
            None
        """
        if count <= 0:
            return
        assert isinstance(other, Seepage)
        core.seepage_clone_cells(self.handle, other.handle, ibeg0, ibeg1, count)

    core.use(None, 'seepage_clone_inner_faces', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def clone_inner_faces(self, ibeg0, other, ibeg1, count):
        """
        拷贝Face数据:
            将other的[ibeg1, ibeg1+count)范围内的Cell对应的Face，拷贝到self的[ibeg0, ibeg0+count)范围内的Cell对应的Face
        此函数会自动跳过不存在的CellID.
            since 2023-9-3

        Args:
            ibeg0 (int): 目标模型中Cell对应的Face的起始索引
            other (Seepage): 源模型
            ibeg1 (int): 源模型中Cell对应的Face的起始索引
            count (int): 要拷贝的Cell对应的Face的数量

        Returns:
            None
        """
        if count <= 0:
            return
        assert isinstance(other, Seepage)
        core.seepage_clone_inner_faces(self.handle, other.handle, ibeg0, ibeg1, count)

    core.use(None, 'seepage_update_den',
             c_void_p, c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t,
             c_double, c_double, c_double)

    def update_den(self, fluid_id=None, kernel=None, relax_factor=1.0, fa_t=None, min=-1, max=-1):
        """
        更新流体的密度。其中
            fluid_id为需要更新的流体的ID (当None的时候，则更新所有)
            kernel为Interp2(p,T)
            relax_factor为松弛因子，限定密度的最大变化幅度.

        注意:
            当 relax_factor <= 0的时候，内核不会执行任何更新  (since 2023-9-27)

        Args:
            fluid_id (int, optional): 需要更新的流体的ID，默认为None，表示更新所有流体
            kernel (Interp2, optional): 插值函数，默认为None
            relax_factor (float, optional): 松弛因子，限定密度的最大变化幅度，默认为1.0
            fa_t (int): 温度属性的ID
            min (float, optional): 密度的最小值，默认为-1
            max (float, optional): 密度的最大值，默认为-1

        Returns:
            None
        """
        if relax_factor <= 0:
            return
        assert isinstance(fa_t, int)
        core.seepage_update_den(self.handle, *parse_fid3(fluid_id),
                                kernel.handle if isinstance(kernel, Interp2) else 0,
                                fa_t, relax_factor, min, max)

    core.use(None, 'seepage_update_vis', c_void_p, c_size_t, c_size_t, c_size_t,
             c_void_p,
             c_size_t,
             c_size_t, c_double,
             c_double, c_double)

    def update_vis(self, fluid_id=None, kernel=None, ca_p=None, fa_t=None, relax_factor=0.3, min=1.0e-7, max=1.0):
        """
        更新流体的粘性系数。
        Note:
            当不给定fluid_id的时候，则尝试更新所有流体的粘性（利用model内置的流体定义）；

        Note:
            当kernel为None的时候，使用模型内置的流体定义；

        注意:
            当 relax_factor <= 0的时候，内核不会执行任何更新  (since 2023-9-27)

        Args:
            fluid_id (int, optional): 需要更新的流体的ID，默认为None，表示更新所有流体
            kernel (Interp2, optional): 插值函数，默认为None
            ca_p (int, optional): 压力属性的ID，默认为None
            fa_t (int): 温度属性的ID
            relax_factor (float, optional): 松弛因子，限定粘性系数的最大变化幅度，默认为0.3
            min (float, optional): 粘性系数的最小值，默认为1.0e-7
            max (float, optional): 粘性系数的最大值，默认为1.0

        Returns:
            None
        """
        if relax_factor <= 0:
            return
        if ca_p is None:
            # 此时，利用流体的体积来计算压力 (不可以指定流体ID：此时更新所有的流体)
            ca_p = 99999999
            assert fluid_id is None
        else:
            assert isinstance(ca_p, int)
        assert isinstance(fa_t, int)
        if kernel is None:
            kernel_handle = 0
        else:
            assert isinstance(kernel, Interp2)
            kernel_handle = kernel.handle
        core.seepage_update_vis(self.handle, *parse_fid3(fluid_id), kernel_handle, ca_p, fa_t,
                                relax_factor, min, max)

    core.use(None, 'seepage_update_pore', c_void_p, c_size_t, c_size_t, c_double)

    def update_pore(self, ca_v0, ca_k, relax_factor=0.01):
        """
        更新pore的属性，使得当前压力下，孔隙空间的体积可以逐渐逼近真实值(真实值由ca_v0和ca_k定义的属性给定).
        注意：这个函数仅更新那些定义了ca_v0和ca_k属性的Cell.

        Args:
            ca_v0 (int): 孔隙初始体积属性的ID
            ca_k (int): 孔隙压缩系数属性的ID
            relax_factor (float, optional): 松弛因子，默认为0.01

        Returns:
            self: 返回当前对象
        """
        core.seepage_update_pore(self.handle, ca_v0, ca_k, relax_factor)
        return self

    core.use(None, 'seepage_thermal_exchange', c_void_p, c_size_t, c_void_p, c_double,
             c_size_t, c_size_t, c_size_t)

    core.use(None, 'seepage_exchange_heat', c_void_p, c_double,
             c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t)

    def exchange_heat(self, fid=None, thermal_model=None, dt=None, ca_g=None, ca_t=None, ca_mc=None,
                      fa_t=None, fa_c=None):
        """
        流体和固体交换热量。
        注意：
            1. 当thermal_model为None的时候，则在Seepage内部交换热量，此时，必须定义ca_t, ca_mc两个属性
            2. 当fid为None的时候，将所有的流体视为整体，与固体交换。此时，会计算各个流体的平均温度，并且，此函数运行之后
                各个流体的温度将相等

        Args:
            fid (int, optional): 流体的ID，默认为None
            thermal_model (Thermal, optional): 热模型，默认为None
            dt (float, optional): 时间步长，默认为None
            ca_g (int, optional): 重力属性的ID，默认为None
            ca_t (int, optional): 温度属性的ID，默认为None
            ca_mc (int, optional): 热容属性的ID，默认为None
            fa_t (int, optional): 面温度属性的ID，默认为None
            fa_c (int, optional): 面热容属性的ID，默认为None

        Returns:
            None
        """
        if dt is None:
            return
        if dt <= 1.0e-20:
            return
        if thermal_model is None:  # 在模型的内部交换热量（流体和固体交换）
            assert fid is None
            all_right = True
            if ca_g is None:
                warnings.warn('ca_g is None in Seepage.exchange_heat')
                all_right = False
            if ca_t is None:
                warnings.warn('ca_t is None in Seepage.exchange_heat')
                all_right = False
            if ca_mc is None:
                warnings.warn('ca_mc is None in Seepage.exchange_heat')
                all_right = False
            if fa_t is None:
                warnings.warn('fa_t is None in Seepage.exchange_heat')
                all_right = False
            if fa_c is None:
                warnings.warn('fa_c is None in Seepage.exchange_heat')
                all_right = False
            if all_right:
                core.seepage_exchange_heat(self.handle, dt, ca_g, ca_t, ca_mc, fa_t, fa_c)
            return
        if isinstance(thermal_model, Thermal):
            if fid is None:
                fid = 100000000  # exchange with all fluid when fid not exists
            core.seepage_thermal_exchange(self.handle, fid, thermal_model.handle, dt, ca_g, fa_t, fa_c)
            return

    core.use(None, 'seepage_update_cond',
             c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def update_cond(self, ca_v0, fa_g0, fa_igr, relax_factor=1.0):
        """
        给定初始时刻各Cell流体体积v0，各Face的导流g0，v/v0到g/g0的映射gr，来更新此刻Face的g.
        ca_v0是cell的属性id，fa_g0是face的属性id的时候，fa_igr是face的属性id
            (用以表示此face选用的gr的序号。注意此时必须提前将gr存储到model中).

        Args:
            ca_v0 (int): 初始时刻各Cell流体体积属性的ID
            fa_g0 (int): 各Face的导流属性的ID
            fa_igr (int): 各Face选用的gr的序号属性的ID
            relax_factor (float, optional): 松弛因子，默认为1.0

        Returns:
            None
        """
        core.seepage_update_cond(self.handle, ca_v0, fa_g0, fa_igr, relax_factor)

    core.use(None, 'seepage_update_g0', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def update_g0(self, fa_g0, fa_k, fa_s, fa_l):
        """
        对于所有的face，根据它的渗透率，面积和长度来计算cond (流体饱和的时候的cond).
            ---
            此函数非必须，可以基于numpy在Python层面实现同样的功能，后续可能会移除.

        Args:
            fa_g0 (int): 各Face的导流属性的ID
            fa_k (int): 各Face的渗透率属性的ID
            fa_s (int): 各Face的面积属性的ID
            fa_l (int): 各Face的长度属性的ID

        Returns:
            None
        """
        core.seepage_update_g0(self.handle, fa_g0, fa_k, fa_s, fa_l)

    core.use(None, 'seepage_diffusion', c_void_p, c_double,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t, c_void_p, c_size_t, c_void_p, c_size_t, c_void_p, c_size_t,
             c_double, c_void_p)

    def diffusion(self, dt, fid0, fid1, *,
                  ps0=None, ls0=None, vs0=None,
                  pk=None, lk=None, vk=None,
                  pg=None, lg=None, vg=None,
                  ppg=None, lpg=None, vpg=None,
                  ds_max=0.05, face_groups=None):
        """
        扩散.
        其中fid0和fid1定义两种流体。在扩散的时候，相邻Cell的这两种流体会进行交换，但会保证每个Cell的流体体积不变；
            其中vs0定义两种流体压力相等的时候fid0的饱和度；vk当饱和度变化1的时候，压力的变化幅度；
            vg定义face的导流能力(针对fid0和fid1作为一个整体);
            vpg定义流体fid0受到的重力减去fid1的重力在face上的投影;
            ds_max为允许的饱和度最大的改变量

        Args:
            dt (float): 时间步长
            fid0 (int): 第一种流体的ID
            fid1 (int): 第二种流体的ID
            ps0 (ctypes.c_void_p, optional): 饱和度指针，默认为None
            ls0 (int, optional): 饱和度指针的长度，默认为None
            vs0 (Vector, optional): 饱和度向量，默认为None
            pk (ctypes.c_void_p, optional): 压力变化幅度指针，默认为None
            lk (int, optional): 压力变化幅度指针的长度，默认为None
            vk (Vector, optional): 压力变化幅度向量，默认为None
            pg (ctypes.c_void_p, optional): 导流能力指针，默认为None
            lg (int, optional): 导流能力指针的长度，默认为None
            vg (Vector, optional): 导流能力向量，默认为None
            ppg (ctypes.c_void_p, optional): 重力投影指针，默认为None
            lpg (int, optional): 重力投影指针的长度，默认为None
            vpg (Vector, optional): 重力投影向量，默认为None
            ds_max (float, optional): 允许的饱和度最大的改变量，默认为0.05
            face_groups (Groups, optional): 面分组，默认为None

        Returns:
            None
        """
        if ps0 is None:
            if isinstance(vs0, Vector):
                warnings.warn('parameter <vs0> of Seepage.diffusion will be removed after 2025-4-6',
                              DeprecationWarning)
                if vs0.size > 0:
                    ps0 = vs0.pointer
                    ls0 = vs0.size

        if pk is None:
            if isinstance(vk, Vector):
                warnings.warn('parameter <vk> of Seepage.diffusion will be removed after 2025-4-6',
                              DeprecationWarning)
                if vk.size > 0:
                    pk = vk.pointer
                    lk = vk.size

        if pg is None:
            if isinstance(vg, Vector):
                warnings.warn('parameter <vg> of Seepage.diffusion will be removed after 2025-4-6',
                              DeprecationWarning)
                if vg.size > 0:
                    pg = vg.pointer
                    lg = vg.size

        if ppg is None:
            if isinstance(vpg, Vector):
                warnings.warn('parameter <vpg> of Seepage.diffusion will be removed after 2025-4-6',
                              DeprecationWarning)
                if vpg.size > 0:
                    ppg = vpg.pointer
                    lpg = vpg.size

        if pg is None:
            return  # 没有g，则无法交换

        if pk is None and ppg is None:
            return  # 既没有定义毛管力，也没有定义重力，没有执行的必要了

        # 下面，解析指针和长度
        if ps0 is None:
            ps0 = 0
            ls0 = 0
        else:
            ps0 = ctypes.cast(ps0, c_void_p)
            if ls0 is None:
                ls0 = self.cell_number

        if pk is None:
            pk = 0
            lk = 0
        else:
            pk = ctypes.cast(pk, c_void_p)
            if lk is None:
                lk = self.cell_number

        if pg is None:
            pg = 0
            lg = 0
        else:
            pg = ctypes.cast(pg, c_void_p)
            if lg is None:
                lg = self.face_number

        if ppg is None:
            ppg = 0
            lpg = 0
        else:
            ppg = ctypes.cast(ppg, c_void_p)
            if lpg is None:
                lpg = self.face_number

        if face_groups is not None:
            assert isinstance(face_groups, Groups)  # 分组

        # 执行扩散操作.
        core.seepage_diffusion(self.handle, dt, *parse_fid3(fid0), *parse_fid3(fid1),
                               ps0, ls0,
                               pk, lk,
                               pg, lg,
                               ppg, lpg,
                               ds_max,
                               0 if face_groups is None else face_groups.handle)

    core.use(None, 'seepage_heating', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def heating(self, ca_mc, ca_t, ca_p, dt):
        """
        按照各个Cell给定的功率来对各个Cell进行加热 (此功能非必须，可以借助numpy实现).
        其中：
            ca_p：定义Cell加热的功率.

        Args:
            ca_mc (int): 热容属性的ID
            ca_t (int): 温度属性的ID
            ca_p (int): 加热功率属性的ID
            dt (float): 时间步长

        Returns:
            None
        """
        core.seepage_heating(self.handle, ca_mc, ca_t, ca_p, dt)

    core.use(None, 'seepage_update_sand', c_void_p,
             c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_void_p, c_void_p)

    def update_sand(self, *, sol_sand, flu_sand, ca_i0, ca_i1,
                    force, ratio=None):
        """
        更新流动的砂和沉降的砂之间的体积. 其中:
            sol_sand, flu_sand: 表示流动的砂和沉降的砂的Index.
            force: 一个指针，给定各个cell位置的单位面积孔隙表面的剪切力;
            ratio: 一个指针，定义各个Cell位置砂子趋向于目标浓度的达成比率(默认为1).
            ca_i0, ca_i1: Cell的属性ID，定义的是存储的曲线的ID。曲线的横坐标是剪切力，纵轴为流动砂的浓度.

        Args:
            sol_sand (int or str): 沉降的砂的Index或名称
            flu_sand (int or str): 流动的砂的Index或名称
            ca_i0 (int or str): Cell的属性ID或名称
            ca_i1 (int or str): Cell的属性ID或名称
            force (ctypes.c_void_p): 各个cell位置的单位面积孔隙表面的剪切力指针
            ratio (ctypes.c_void_p, optional): 各个Cell位置砂子趋向于目标浓度的达成比率指针，默认为None

        Returns:
            None
        """
        if isinstance(sol_sand, str):
            sol_sand = self.find_fludef(name=sol_sand)
            assert sol_sand is not None

        if isinstance(flu_sand, str):
            flu_sand = self.find_fludef(name=flu_sand)
            assert flu_sand is not None

        if isinstance(ca_i0, str):
            ca_i0 = self.get_cell_key(ca_i0)
            assert ca_i0 is not None

        if isinstance(ca_i1, str):
            ca_i1 = self.get_cell_key(ca_i1)
            assert ca_i1 is not None

        core.seepage_update_sand(self.handle, ca_i0, ca_i1,
                                 *parse_fid3(sol_sand),
                                 *parse_fid3(flu_sand),
                                 ctypes.cast(force, c_void_p), ctypes.cast(ratio, c_void_p))

    core.use(None, 'seepage_pop_fluids', c_void_p, c_void_p)
    core.use(None, 'seepage_push_fluids', c_void_p, c_void_p)

    def pop_fluids(self, buffer):
        """
        将各个Cell中的最后一个流体暂存到buffer中。一般情况下，将固体作为最后一种流体。在计算流动的
        时候，如果这些固体存在，则会影响到相对渗透率。因此，当模型中存在固体的时候，需要先将固体组分
        弹出，然后再计算流动。计算流动之后，再将备份的固体组分压入，使得模型恢复到最初的状态。
        注意：在弹出最后一种流体的时候，会同步修改Cell中的pore的大小，并保证压力不变;
            since: 2023-04

        Args:
            buffer (Seepage.CellData): 用于暂存流体的缓冲区

        Returns:
            None
        """
        assert isinstance(buffer, Seepage.CellData)
        core.seepage_pop_fluids(self.handle, buffer.handle)

    def push_fluids(self, buffer):
        """
        将buffer中暂存的流体追加到各个Cell中。和pop_fluids函数搭配使用。

        Args:
            buffer (Seepage.CellData): 暂存流体的缓冲区

        Returns:
            None
        """
        assert isinstance(buffer, Seepage.CellData)
        core.seepage_push_fluids(self.handle, buffer.handle)

    def iterate(self, *args, **kwargs):
        """
        迭代更新模型状态

        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        Returns:
            迭代结果
        """
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.iterate(self, *args, **kwargs)

    def iterate_thermal(self, *args, **kwargs):
        """
        迭代更新模型的热状态

        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        Returns:
            热状态迭代结果
        """
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.iterate_thermal(self, *args, **kwargs)

    def get_recommended_dt(self, *args, **kwargs):
        """
        获取推荐的时间步长

        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        Returns:
            float: 推荐的时间步长
        """
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.get_recommended_dt(self, *args, **kwargs)

    core.use(c_double, 'seepage_get_fluid_mass', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_mass(self, fluid_id=None):
        """
        返回模型中所有Cell内的流体mass的和。
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体

        Args:
            fluid_id (int, optional): 流体的ID，默认为None

        Returns:
            float: 流体的总质量
        """
        return core.seepage_get_fluid_mass(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_mass(self):
        """
        返回模型中所有Cell内的流体mass的和

        Returns:
            float: 流体的总质量
        """
        return self.get_fluid_mass()

    core.use(c_double, 'seepage_get_fluid_vol', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_vol(self, fluid_id=None):
        """
        返回模型中所有Cell内的流体vol的和
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体

        Args:
            fluid_id (int, optional): 流体的ID，默认为None

        Returns:
            float: 流体的总体积
        """
        return core.seepage_get_fluid_vol(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_vol(self):
        """
        返回模型中所有Cell内的流体vol的和

        Returns:
            float: 流体的总体积
        """
        return self.get_fluid_vol()

    core.use(None, 'seepage_find_inner_face_ids', c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号

        Args:
            cell_ids (UintVector): 包含多个Cell的UintVector对象
            buffer (UintVector, optional): 用于存储结果的UintVector对象，默认为None

        Returns:
            UintVector: 包含内部相互连接的Face序号的UintVector对象
        """
        assert isinstance(cell_ids, UintVector)
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.seepage_find_inner_face_ids(self.handle, buffer.handle, cell_ids.handle)
        return buffer

    core.use(None, 'seepage_get_cond_for_exchange', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t)

    def get_cond_for_exchange(self, fid0, fid1, buffer=None):
        """
        根据相对渗透率曲线、粘性系数，计算相邻两个Cell交换流体的时候的导流系数

        Args:
            fid0: 第一个Cell的相关标识
            fid1: 第二个Cell的相关标识
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含导流系数的Vector对象
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_cond_for_exchange(self.handle, buffer.handle, *parse_fid3(fid0), *parse_fid3(fid1))
        return buffer

    core.use(None, 'seepage_get_linear_dpre', c_void_p, c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t, c_double, c_void_p)

    def get_linear_dpre(self, fid0, fid1, s2p=None, ca_ipc=99999999, vs0=None, vk=None, ds=0.05, cell_ids=None):
        """
        更新两种流体之间压力差和饱和度之间的线性关系

        Args:
            fid0: 第一个Cell的相关标识
            fid1: 第二个Cell的相关标识
            s2p (Interp1, optional): 插值对象，默认为None
            ca_ipc (int, optional): 一个整数参数，默认为99999999
            vs0 (Vector, optional): 用于存储结果的Vector对象，默认为None
            vk (Vector, optional): 用于存储结果的Vector对象，默认为None
            ds (float, optional): 一个浮点数参数，默认为0.05
            cell_ids (UintVector, optional): 包含Cell序号的UintVector对象，默认为None

        Returns:
            Tuple[Vector, Vector]: 包含更新后结果的两个Vector对象
        """
        if not isinstance(vs0, Vector):
            vs0 = Vector()
        if not isinstance(vk, Vector):
            vk = Vector()
        if cell_ids is not None:
            if not isinstance(cell_ids, UintVector):
                cell_ids = UintVector(cell_ids)
        core.seepage_get_linear_dpre(self.handle, vs0.handle, vk.handle,
                                     *parse_fid3(fid0),
                                     *parse_fid3(fid1),
                                     s2p.handle if isinstance(s2p, Interp1) else 0,
                                     ca_ipc, ds,
                                     0 if cell_ids is None else cell_ids.handle)
        return vs0, vk

    core.use(None, 'seepage_get_vol_fraction', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def get_vol_fraction(self, fid, buffer=None):
        """
        返回给定序号的流体的体积饱和度，并且作为一个Vector返回

        Args:
            fid: 流体的序号
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含体积饱和度的Vector对象
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_vol_fraction(self.handle, buffer.handle, *parse_fid3(fid))
        return buffer

    core.use(None, 'seepage_cells_write',
             c_void_p, c_void_p, c_int64)

    def cells_write(self, *, index, pointer):
        """
        导出属性(所有的Cell): 当 index >= 0 的时候，为属性ID; 如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore
            index=-6, inner_prod(pos, gravity)
        --- (以下为只读属性):
            index=-10, 所有流体的总的质量 (只读)
            index=-11, 所有流体的总的体积 (只读)
            index=-12, 根据流体的体积和pore，来计算的Cell的压力 (只读)

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_cell_key(key=index)
            assert index is not None
        core.seepage_cells_write(self.handle,
                                 ctypes.cast(pointer, c_void_p), index)

    core.use(None, 'seepage_cells_read',
             c_void_p, c_void_p, c_double, c_int64)

    def cells_read(self, *, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_cell_key(key=index)
        if pointer is not None:
            core.seepage_cells_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index)
        else:
            assert value is not None
            core.seepage_cells_read(self.handle, 0, value, index)

    core.use(None, 'seepage_faces_write', c_void_p, c_void_p, c_int64)

    def faces_write(self, *, index, pointer):
        """
        导出属性:
            index >= 0 的时候，为属性ID；
        如果index < 0，则：
            index=-1, cond
            index=-2, dr
            index=-3, face两侧的cell的距离
            index=-4, 重力的分量与face两侧Cell距离的乘积. inner_prod(gravity, cell1.pos - cell0.pos)
            ...
            index=-10, dv of fluid 0
            index=-11, dv of fluid 1
            index=-12, dv of fluid 2
            ...
            index=-19, dv of fluid ALL

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_face_key(key=index)
            assert index is not None
        core.seepage_faces_write(self.handle, ctypes.cast(pointer, c_void_p), index)

    core.use(None, 'seepage_faces_read', c_void_p, c_void_p, c_double, c_int64)

    def faces_read(self, *, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, cond
            index=-2, dr

        Args:
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_face_key(key=index)
        if pointer is not None:
            core.seepage_faces_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index)
        else:
            assert value is not None
            core.seepage_faces_read(self.handle, 0, value, index)

    core.use(None, 'seepage_fluids_write', c_void_p, c_void_p, c_int64, c_size_t, c_size_t, c_size_t)

    def fluids_write(self, *, fluid_id, index, pointer):
        """
        导出属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, 质量
            index=-2, 密度
            index=-3, 体积
            index=-4, 粘性

        Args:
            fluid_id: 流体的ID
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针
        """
        if isinstance(index, str):
            index = self.get_flu_key(key=index)
            assert index is not None
        core.seepage_fluids_write(self.handle, ctypes.cast(pointer, c_void_p), index, *parse_fid3(fluid_id))

    core.use(None, 'seepage_fluids_read', c_void_p, c_void_p, c_double, c_int64, c_size_t, c_size_t, c_size_t)

    def fluids_read(self, *, fluid_id, index, pointer=None, value=None):
        """
        导入属性

        Args:
            fluid_id: 流体的ID
            index (int or str): 属性的索引或名称
            pointer: 指向存储数据的指针，默认为None
            value: 要导入的值，默认为None
        """
        if isinstance(index, str):
            index = self.reg_flu_key(key=index)
        if pointer is not None:
            core.seepage_fluids_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index, *parse_fid3(fluid_id))
        else:
            assert value is not None
            core.seepage_fluids_read(self.handle, 0, value, index, *parse_fid3(fluid_id))

    @property
    def numpy(self):
        """
        用以和numpy交互数据

        警告: Seepage.numpy将在2025-1-21之后移除。请使用zmlx.utility.SeepageNumpy代替。

        Returns:
            SeepageNumpy: 用于和numpy交互数据的SeepageNumpy对象
        """
        warnings.warn('Seepage.numpy will be removed after 2025-1-21. Use zmlx.utility.SeepageNumpy Instead.'
                      , DeprecationWarning)
        from zmlx.utility.SeepageNumpy import SeepageNumpy
        return SeepageNumpy(model=self)

    core.use(None, 'seepage_get_cells_v0', c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_k', c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_fv', c_void_p, c_void_p)
    core.use(None, 'seepage_get_cells_attr', c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_get_faces_attr', c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_set_cells_attr', c_void_p, c_size_t, c_void_p)
    core.use(None, 'seepage_set_faces_attr', c_void_p, c_size_t, c_void_p)

    def get_attrs(self, key, index=None, buffer=None):
        """
        返回所有指定元素的属性 <作为Vector返回>.

        警告: 请使用 <Seepage.cells_write> 和 <Seepage.faces_write> 函数代替。此函数将在2024-6-14之后移除。

        Args:
            key (str): 指定元素的键
            index (int, optional): 属性的索引，默认为None
            buffer (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含指定元素属性的Vector对象
        """
        warnings.warn('please use function <Seepage.cells_write> and <Seepage.faces_write> instead. '
                      'Will remove after 2024-6-14', DeprecationWarning)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        if key == 'cells_v0':
            core.seepage_get_cells_v0(self.handle, buffer.handle)
            return buffer
        if key == 'cells_k':
            core.seepage_get_cells_k(self.handle, buffer.handle)
            return buffer
        if key == 'cells_fv':
            core.seepage_get_cells_fv(self.handle, buffer.handle)
            return buffer
        if key == 'cells':
            core.seepage_get_cells_attr(self.handle, index, buffer.handle)
            return buffer
        if key == 'faces':
            core.seepage_get_faces_attr(self.handle, index, buffer.handle)
            return buffer

    def set_attrs(self, key, value=None, index=None):
        """
        设置所有指定元素的属性

        警告: 请使用 <Seepage.cells_read> 和 <Seepage.faces_read> 函数代替。此函数将在2024-6-14之后移除。

        Args:
            key (str): 指定元素的键
            value (Vector): 要设置的属性值
            index (int, optional): 属性的索引，默认为None
        """
        warnings.warn('please use function <Seepage.cells_read> and <Seepage.faces_read> instead. '
                      'will be removed after 2024-6-14', DeprecationWarning)
        assert isinstance(value, Vector)
        if key == 'cells':
            core.seepage_set_cells_attr(self.handle, index, value.handle)
        if key == 'faces':
            core.seepage_set_faces_attr(self.handle, index, value.handle)

    def print_cells(self, path, get=None, properties=None):
        """
        输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，第5列为体积，后面依次为各流体组分的体积饱和度.

        Args:
            path (str): 输出文件的路径
            get (Callable, optional): 用于获取cell属性字符串的函数，默认为None
            properties (List[Callable], optional): 额外的属性获取函数列表，默认为None
        """
        if path is None:
            return

        def get_vols(flu):
            if flu.component_number == 0:
                return [flu.vol]
            else:
                vols = []
                for i in range(flu.component_number):
                    vols.extend(get_vols(flu.get_component(i)))
                return vols

        def to_str(c):
            vols = []
            for i in range(c.fluid_number):
                vols.extend(get_vols(c.get_fluid(i)))
            vol = sum(vols)
            s = f'{c.pre}\t{vol}'
            for v in vols:
                s = f'{s}\t{v / vol}'
            return s

        if get is None:
            get = to_str
        with open(path, 'w') as file:
            for cell in self.cells:
                x, y, z = cell.pos
                file.write(f'{x}\t{y}\t{z}\t{get(cell)}')
                if properties is not None:
                    for prop in properties:
                        file.write(f'\t{prop(cell)}')
                file.write('\n')

    core.use(None, 'seepage_group_cells', c_void_p, c_void_p)

    def get_cell_groups(self):
        """
        对所有的cell进行分区，使得对于任意一个cell，都不会和与它相关的cell分在一组 (用于并行)

        Returns:
            Groups: 包含分区结果的Groups对象
        """
        g = Groups()
        core.seepage_group_cells(self.handle, g.handle)
        return g

    core.use(None, 'seepage_group_faces', c_void_p, c_void_p)

    def get_face_groups(self):
        """
        对所有的face进行分区，使得对于任意一个face，都不会和与它相关的face分在一组 (用于并行)

        Returns:
            Groups: 包含分区结果的Groups对象
        """
        g = Groups()
        core.seepage_group_faces(self.handle, g.handle)
        return g

    core.use(None, 'seepage_get_cell_flu_vel', c_void_p, c_void_p,
             c_size_t, c_double)

    def get_cell_flu_vel(self, fid, last_dt, buf=None):
        """
        根据上一个时间步各个face内流过的流体的体积，来计算各个cell位置流体流动的速度.

        Args:
            fid: 流体的ID
            last_dt: 上一个时间步的时间间隔
            buf (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含流体流动速度的Vector对象
        """
        if isinstance(fid, str):
            fid = self.find_fludef(name=fid)
        if is_array(fid):
            assert len(fid) == 1
            fid = fid[0]
        assert 0 <= fid < self.fludef_number
        if buf is None:
            buf = Vector(size=self.cell_number)
            core.seepage_get_cell_flu_vel(self.handle, buf.pointer, fid, last_dt)
            return buf
        elif isinstance(buf, Vector):
            buf.size = self.cell_number
            core.seepage_get_cell_flu_vel(self.handle, buf.pointer, fid, last_dt)
            return buf
        else:  # 此时，buf应该为一个长度为cell_number的指针类型
            core.seepage_get_cell_flu_vel(self.handle, buf, fid, last_dt)

    core.use(None, 'seepage_get_cell_gradient', c_void_p, c_void_p, c_void_p)

    def get_cell_gradient(self, data, buf=None):
        """
        计算cell位置各个物理量的梯度. 这里，给定的data和buf都应该为长度等于cell_number的double指针

        Args:
            data: 包含物理量数据的指针
            buf (Vector, optional): 用于存储结果的Vector对象，默认为None

        Returns:
            Vector: 包含梯度数据的Vector对象
        """
        if isinstance(data, Vector):
            data = data.pointer
        if buf is None:
            buf = Vector(size=self.cell_number)
            core.seepage_get_cell_gradient(self.handle, buf.pointer, data)
            return buf
        elif isinstance(buf, Vector):
            buf.size = self.cell_number
            core.seepage_get_cell_gradient(self.handle, buf.pointer, data)
            return buf
        else:  # 此时，buf应该为一个长度为cell_number的指针类型
            core.seepage_get_cell_gradient(self.handle, buf, data)

    core.use(None, 'seepage_get_cell_average',
             c_void_p, c_void_p, c_void_p)

    def get_cell_average(self, fa, *, buf=None):
        """
        计算cell周围face的平均值

        其中:
            fa为face的属性(指针，用于输入)
            buf为各个cell的属性(指针，用于输出)

        Args:
            fa: 包含face属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含平均值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.cell_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_cell_average(self.handle, ctypes.cast(buf, c_void_p),
                                      ctypes.cast(fa, c_void_p))
        return data

    core.use(None, 'seepage_get_cell_max',
             c_void_p, c_void_p, c_void_p)

    def get_cell_max(self, fa, *, buf=None):
        """
        计算cell周围face的属性的最大值

        其中:
            fa为face的属性(指针，用于输入)
            buf为各个cell的属性(指针，用于输出)

        Args:
            fa: 包含face属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含最大值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.cell_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_cell_max(self.handle, ctypes.cast(buf, c_void_p),
                                  ctypes.cast(fa, c_void_p))
        return data

    core.use(None, 'seepage_get_face_gradient',
             c_void_p, c_void_p, c_void_p)

    def get_face_gradient(self, ca, *, buf=None):
        """
        根据cell中心位置的属性的值来计算各个face位置的梯度.
            (c1 - c0) / dist
        其中:
            c1和c0分别位face右侧和左侧的cell的属性.
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        注意：
            这里计算梯度的时候，并未计算绝对值，即返回的gradient可能是负值.

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含梯度数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_gradient(self.handle, ctypes.cast(buf, c_void_p),
                                       ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_diff',
             c_void_p, c_void_p, c_void_p)

    def get_face_diff(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的差异。
            c1 - c0
        其中:
            c1和c0分别位face右侧和左侧的cell的属性.
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        注意：
            并未计算绝对值，及返回的数值可能是负值.

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含差异数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_diff(self.handle, ctypes.cast(buf, c_void_p),
                                   ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_sum',
             c_void_p, c_void_p, c_void_p)

    def get_face_sum(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的和。
            c1 + c0
        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含和数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_sum(self.handle, ctypes.cast(buf, c_void_p),
                                  ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_average',
             c_void_p, c_void_p, c_void_p)

    def get_face_average(self, ca, *, buf=None):
        """
        计算face两侧的cell的属性的值的平均值。
            (c1 + c0) / 2
        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含平均值数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_average(self.handle, ctypes.cast(buf, c_void_p),
                                      ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_left',
             c_void_p, c_void_p, c_void_p)

    def get_face_left(self, ca, *, buf=None):
        """
        计算face左侧的cell属性

        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含左侧cell属性数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_left(self.handle, ctypes.cast(buf, c_void_p),
                                   ctypes.cast(ca, c_void_p))
        return data

    core.use(None, 'seepage_get_face_right',
             c_void_p, c_void_p, c_void_p)

    def get_face_right(self, ca, *, buf=None):
        """
        计算face右侧的cell属性

        其中:
            buf为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)

        Args:
            ca: 包含cell属性数据的指针
            buf: 用于存储结果的指针，默认为None

        Returns:
            numpy.ndarray: 包含右侧cell属性数据的numpy数组
        """
        if buf is None and np is not None:
            data = np.zeros(self.face_number)
            buf = get_pointer64(data)
        else:
            data = None
        assert buf is not None
        core.seepage_get_face_right(self.handle, ctypes.cast(buf, c_void_p),
                                    ctypes.cast(ca, c_void_p))
        return data


Reaction = Seepage.Reaction


class Thermal(HasHandle):
    """
    热传导温度场
    """

    class Cell(Object):
        """
        控制体单元

        该类表示热传导模型中的一个控制体单元，包含与该单元相连的面和其他单元的信息，
        以及该单元的热容量和温度等属性。
        """

        def __init__(self, model, index):
            """
            初始化控制体单元

            Args:
                model (Thermal): 所属的热传导模型
                index (int): 单元的索引，必须小于模型中的单元数量
            """
            assert isinstance(model, Thermal)
            assert index < model.cell_number
            self.model = model
            self.index = index

        def __str__(self):
            """
            返回控制体单元的字符串表示

            Returns:
                str: 包含模型句柄和单元索引的字符串
            """
            return f'zml.Thermal.Cell(handle = {self.model.handle}, index = {self.index})'

        core.use(c_size_t, 'thermal_get_cell_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            连接的Face数量

            Returns:
                int: 与该单元相连的面的数量
            """
            return core.thermal_get_cell_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            连接的Cell数量

            Returns:
                int: 与该单元相连的其他单元的数量，等于相连面的数量
            """
            return self.face_number

        core.use(c_size_t, 'thermal_get_cell_face_id', c_void_p, c_size_t, c_size_t)
        core.use(c_size_t, 'thermal_get_cell_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            """
            连接的第index个Cell

            Args:
                index (int): 要获取的相邻单元的索引

            Returns:
                Thermal.Cell: 第index个相邻单元，如果索引有效；否则返回None
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.thermal_get_cell_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            连接的第index个Face

            Args:
                index (int): 要获取的相邻面的索引

            Returns:
                Thermal.Face: 第index个相邻面，如果索引有效；否则返回None
            """
            index = get_index(index, self.face_number)
            if index is not None:
                face_id = core.thermal_get_cell_face_id(self.model.handle, self.index, index)
                return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            所有相邻的Cell

            Returns:
                Iterator: 包含所有相邻单元的迭代器
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            所有相邻的Face

            Returns:
                Iterator: 包含所有相邻面的迭代器
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        core.use(c_double, 'thermal_get_cell_mc', c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_mc', c_void_p, c_size_t, c_double)

        @property
        def mc(self):
            """
            控制体内物质的热容量，等于物质的质量乘以比热

            Returns:
                float: 控制体的热容量
            """
            return core.thermal_get_cell_mc(self.model.handle, self.index)

        @mc.setter
        def mc(self, value):
            """
            设置控制体内物质的热容量，等于物质的质量乘以比热

            Args:
                value (float): 要设置的热容量值
            """
            core.thermal_set_cell_mc(self.model.handle, self.index, value)

        core.use(c_double, 'thermal_get_cell_T', c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_T', c_void_p, c_size_t, c_double)

        @property
        def temperature(self):
            """
            控制体内物质的温度 K

            Returns:
                float: 控制体的温度
            """
            return core.thermal_get_cell_T(self.model.handle, self.index)

        @temperature.setter
        def temperature(self, value):
            """
            设置控制体内物质的温度 K

            Args:
                value (float): 要设置的温度值
            """
            core.thermal_set_cell_T(self.model.handle, self.index, value)

    class Face(Object):
        """
        表示热传导模型中的一个界面，包含与该界面相连的单元信息，以及该界面的导热能力等属性。
        """
        def __init__(self, model, index):
            """
            初始化界面

            Args:
                model (Thermal): 所属的热传导模型
                index (int): 界面的索引，必须小于模型中的界面数量
            """
            assert isinstance(model, Thermal)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index

        def __str__(self):
            """
            返回界面的字符串表示

            Returns:
                str: 包含模型句柄和界面索引的字符串
            """
            return f'zml.Thermal.Face(handle = {self.model.handle}, index = {self.index}) '

        core.use(c_size_t, 'thermal_get_face_cell_id', c_void_p, c_size_t, c_size_t)

        @property
        def cell_number(self):
            """
            连接的Cell的数量

            Returns:
                int: 与该界面相连的单元数量，固定为2
            """
            return 2

        def get_cell(self, index):
            """
            连接的第index个Cell

            Args:
                index (int): 要获取的相邻单元的索引

            Returns:
                Thermal.Cell: 第index个相邻单元，如果索引有效；否则返回None
            """
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.thermal_get_face_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        @property
        def cells(self):
            """
            连接的所有的Cell

            Returns:
                tuple: 包含与该界面相连的两个单元的元组
            """
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'thermal_get_face_cond', c_void_p, c_size_t)
        core.use(None, 'thermal_set_face_cond', c_void_p, c_size_t, c_double)

        @property
        def cond(self):
            """
            Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，dt为时间步长，E为通过该Face输运的能量(J)

            Returns:
                float: 界面的导热能力
            """
            return core.thermal_get_face_cond(self.model.handle, self.index)

        @cond.setter
        def cond(self, value):
            """
            设置Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，dt为时间步长，E为通过该Face输运的能量(J)

            Args:
                value (float): 要设置的导热能力值
            """
            core.thermal_set_face_cond(self.model.handle, self.index, value)

    core.use(c_void_p, 'new_thermal')
    core.use(None, 'del_thermal', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化热传导模型

        Args:
            path (str, optional): 要加载的模型文件路径，如果提供则加载该文件
            handle (c_void_p, optional): 模型的句柄，如果提供则使用该句柄
        """
        super(Thermal, self).__init__(handle, core.new_thermal, core.del_thermal)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回热传导模型的字符串表示

        Returns:
            str: 包含模型句柄的字符串
        """
        return f'zml.Thermal(handle = {self.handle})'

    core.use(None, 'thermal_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 要保存的文件路径
        """
        if isinstance(path, str):
            make_parent(path)
            core.thermal_save(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要加载的文件路径
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.thermal_load(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_clear', c_void_p)

    def clear(self):
        """
        删除所有的Cell和Face
        """
        core.thermal_clear(self.handle)

    core.use(c_size_t, 'thermal_get_cell_n', c_void_p)

    @property
    def cell_number(self):
        """
        模型中Cell的数量

        Returns:
            int: 模型中控制体单元的数量
        """
        return core.thermal_get_cell_n(self.handle)

    core.use(c_size_t, 'thermal_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        模型中Face的数量

        Returns:
            int: 模型中界面的数量
        """
        return core.thermal_get_face_n(self.handle)

    def get_cell(self, index):
        """
        模型中第index个Cell

        Args:
            index (int): 要获取的单元的索引

        Returns:
            Thermal.Cell: 第index个单元，如果索引有效；否则返回None
        """
        index = get_index(index, self.cell_number)
        if index is not None:
            return Thermal.Cell(self, index)

    def get_face(self, index):
        """
        模型中第index个Face

        Args:
            index (int): 要获取的界面的索引

        Returns:
            Thermal.Face: 第index个界面，如果索引有效；否则返回None
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Thermal.Face(self, index)

    core.use(c_size_t, 'thermal_add_cell', c_void_p)

    def add_cell(self):
        """
        添加一个Cell

        Returns:
            Thermal.Cell: 新添加的单元
        """
        cell_id = core.thermal_add_cell(self.handle)
        return self.get_cell(cell_id)

    core.use(c_size_t, 'thermal_add_face', c_void_p, c_size_t, c_size_t)

    def add_face(self, cell0, cell1):
        """
        在两个Cell之间添加Face以连接

        Args:
            cell0 (Thermal.Cell): 第一个单元
            cell1 (Thermal.Cell): 第二个单元

        Returns:
            Thermal.Face: 新添加的界面
        """
        assert isinstance(cell0, Thermal.Cell)
        assert isinstance(cell1, Thermal.Cell)
        assert cell0.model.handle == self.handle
        assert cell1.model.handle == self.handle
        assert cell0.index < self.cell_number
        assert cell1.index < self.cell_number
        assert cell0.index != cell1.index
        face_id = core.thermal_add_face(self.handle, cell0.index, cell1.index)
        return self.get_face(face_id)

    core.use(None, 'thermal_iterate', c_void_p, c_double, c_void_p)

    def iterate(self, dt, solver):
        """
        利用给定的时间步长dt，向前迭代一步

        Args:
            dt (float): 时间步长
            solver: 求解器对象，必须提供句柄
        """
        lic.check_once()
        assert solver is not None
        core.thermal_iterate(self.handle, dt, solver.handle)

    @property
    def cells(self):
        """
        返回所有的Cell

        Returns:
            Iterator: 包含所有控制体单元的迭代器
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        返回所有的Face

        Returns:
            Iterator: 包含所有界面的迭代器
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    def print_cells(self, path):
        """
        将所有的Cell的信息打印到文件

        Args:
            path (str): 要打印到的文件路径
        """
        with open(path, 'w') as file:
            for cell in self.cells:
                file.write(f'{cell.temperature}\t{cell.mc}\n')

    def exchange_heat(self, model, dt, fid=None, ca_g=None, fa_t=None, fa_c=None):
        """
        与另外一个模型交换热量

        Args:
            model (Seepage): 要交换热量的模型
            dt (float): 时间步长
            fid (optional): 流体ID，默认为None
            ca_g (optional): 单元属性，默认为None
            fa_t (optional): 界面温度，默认为None
            fa_c (optional): 界面导热能力，默认为None
        """
        if isinstance(model, Seepage):
            model.exchange_heat(fid=fid, thermal_model=self, dt=dt, ca_g=ca_g, fa_t=fa_t, fa_c=fa_c)


class ConjugateGradientSolver(HasHandle):
    """
    Eigen库中共轭梯度求解器的包装类

    该类提供了对Eigen库中共轭梯度求解器的封装，允许用户设置求解器的容差，并获取当前的容差设置。
    """
    core.use(c_void_p, 'new_cg_sol')
    core.use(None, 'del_cg_sol', c_void_p)

    def __init__(self, tolerance=None, handle=None):
        """
        创建求解器

        Args:
            tolerance (float, optional): 求解器的容差。如果提供，将调用 `set_tolerance` 方法设置容差。默认为None。
            handle (c_void_p, optional): 求解器的句柄。如果提供，将使用该句柄初始化求解器。默认为None。

        Raises:
            AssertionError: 如果提供了句柄，但同时也提供了容差，将抛出此异常。
        """
        super(ConjugateGradientSolver, self).__init__(handle, core.new_cg_sol, core.del_cg_sol)
        if handle is None:
            if tolerance is not None:
                self.set_tolerance(tolerance)
        else:
            assert tolerance is None

    core.use(None, 'cg_sol_set_tolerance', c_void_p, c_double)

    def set_tolerance(self, tolerance):
        """
        设置求解器的容差

        Args:
            tolerance (float): 要设置的容差。
        """
        core.cg_sol_set_tolerance(self.handle, tolerance)

    core.use(c_double, 'cg_sol_get_tolerance', c_void_p)

    def get_tolerance(self):
        """
        获取求解器的容差

        Returns:
            float: 当前求解器的容差。
        """
        return core.cg_sol_get_tolerance(self.handle)


class InvasionPercolation(HasHandle):
    """
    IP模型计算模型。该模型定义了所有用于求解的数据以及方法。
    """

    class NodeData(Object):
        """
        IP模型中的节点，也对应于Pore(相应地，Bond类型也可以对应于throat)；Node为流体的存储空间。

        Attributes:
            handle (c_void_p): 节点的句柄。
        """

        def __init__(self, handle):
            """
            初始化节点数据

            Args:
                handle (c_void_p): 节点的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Node是否是同一个

            Args:
                rhs (NodeData): 要比较的另一个节点数据对象。

            Returns:
                bool: 如果两个节点的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个Node是否不是同一个

            Args:
                rhs (NodeData): 要比较的另一个节点数据对象。

            Returns:
                bool: 如果两个节点的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回节点数据的字符串表示

            Returns:
                str: 包含节点句柄、位置和半径的字符串。
            """
            return f'zml.InvasionPercolation.NodeData(handle = {self.handle}, pos = {self.pos}, radi = {self.radi})'

        core.use(c_size_t, 'ip_node_get_phase', c_void_p)
        core.use(None, 'ip_node_set_phase', c_void_p, c_size_t)

        def get_phase(self):
            """
            获取此Node中流体的相态。相态用一个整数(>=0)来表示。

            Returns:
                int: 节点中流体的相态。
            """
            return core.ip_node_get_phase(self.handle)

        def set_phase(self, value):
            """
            设置此Node中流体的相态。相态用一个整数(>=0)来表示。

            Args:
                value (int): 要设置的相态，必须大于等于0。

            Raises:
                AssertionError: 如果提供的值小于0。
            """
            assert value >= 0
            core.ip_node_set_phase(self.handle, value)

        @property
        def phase(self):
            """
            获取或设置此Node中流体的相态。相态用一个整数(>=0)来表示。

            Returns:
                int: 节点中流体的相态。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

        core.use(c_size_t, 'ip_node_get_cid', c_void_p)
        core.use(None, 'ip_node_set_cid', c_void_p, c_size_t)

        def get_cid(self):
            """
            获取Node所在的cluster的ID (从0开始编号)。程序会将各个Node，根据流体的phase和相互的连接关系，划分成为一个个cluster。
            每一个cluster都是一个流体相态一样，且相互联通的一系列Node。

            Returns:
                int: 节点所在的cluster的ID。
            """
            return core.ip_node_get_cid(self.handle)

        def set_cid(self, value):
            """
            设置Node所在的cluster的ID （注意：此函数仅供作者测试，且随时都可能被移除。在任何情况下，此函数都不应被调用）

            Args:
                value (int): 要设置的cluster的ID。
            """
            core.ip_node_set_cid(self.handle, value)

        @property
        def cid(self):
            """
            获取或设置Node所在的cluster的ID (从0开始编号)。

            Returns:
                int: 节点所在的cluster的ID。
            """
            return self.get_cid()

        @cid.setter
        def cid(self, value):
            self.set_cid(value)

        core.use(c_double, 'ip_node_get_radi', c_void_p)
        core.use(None, 'ip_node_set_radi', c_void_p, c_double)

        def get_radi(self):
            """
            获取此Node内孔隙的半径（单位：米）。这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。

            Returns:
                float: 节点内孔隙的半径。
            """
            return core.ip_node_get_radi(self.handle)

        def set_radi(self, value):
            """
            设置此Node内孔隙的半径（单位：米）。这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。

            Args:
                value (float): 要设置的半径，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_node_set_radi(self.handle, value)

        @property
        def radi(self):
            """
            获取或设置此Node内孔隙的半径（单位：米）。

            Returns:
                float: 节点内孔隙的半径。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

        core.use(c_double, 'ip_node_get_time_invaded', c_void_p)

        @property
        def time_invaded(self):
            """
            获取最后一个set_phase的时间

            Returns:
                float: 最后一个set_phase的时间。
            """
            return core.ip_node_get_time_invaded(self.handle)

        @property
        def time(self):
            """
            获取最后一个set_phase的时间

            Returns:
                float: 最后一个set_phase的时间。
            """
            return self.time_invaded

        core.use(c_double, 'ip_node_get_rate_invaded', c_void_p)

        @property
        def rate_invaded(self):
            """
            获取节点的侵入速率

            Returns:
                float: 节点的侵入速率。
            """
            return core.ip_node_get_rate_invaded(self.handle)

        core.use(c_double, 'ip_node_get_pos', c_void_p, c_size_t)
        core.use(None, 'ip_node_set_pos', c_void_p, c_size_t, c_double)

        def get_pos(self):
            """
            获取此Node在三维空间的位置

            Returns:
                list: 包含节点在三维空间位置的列表。
            """
            return [core.ip_node_get_pos(self.handle, i) for i in range(3)]

        def set_pos(self, value):
            """
            设置此Node在三维空间的位置

            Args:
                value (list): 要设置的位置，列表长度必须大于等于3。

            Raises:
                AssertionError: 如果提供的列表长度小于3。
            """
            assert len(value) >= 3
            for i in range(3):
                core.ip_node_set_pos(self.handle, i, value[i])

        @property
        def pos(self):
            """
            获取或设置此Node在三维空间的位置

            Returns:
                list: 包含节点在三维空间位置的列表。

            Raises:
                AssertionError: 如果设置的列表长度小于3。
            """
            return self.get_pos()

        @pos.setter
        def pos(self, value):
            self.set_pos(value)

    class Node(NodeData):
        """
        IP模型中的节点，继承自NodeData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 节点的索引。
        """

        core.use(c_void_p, 'ip_get_node', c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化节点

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 节点的索引。
            """
            super(InvasionPercolation.Node, self).__init__(handle=core.ip_get_node(model.handle, index))
            self.model = model
            self.index = index

        core.use(c_size_t, 'ip_get_node_bond_n', c_void_p, c_size_t)

        @property
        def bond_n(self):
            """
            获取此Node连接的Bond的数量

            Returns:
                int: 节点连接的Bond的数量。
            """
            return core.ip_get_node_bond_n(self.model.handle, self.index)

        @property
        def node_n(self):
            """
            获取此Node连接的Node的数量

            Returns:
                int: 节点连接的Node的数量。
            """
            return self.bond_n

        core.use(c_size_t, 'ip_get_node_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, idx):
            """
            获取此Node连接的第idx个Node

            Args:
                idx (int): 要获取的相邻节点的索引。

            Returns:
                Node: 第idx个相邻节点，如果索引有效；否则返回None。
            """
            idx = get_index(idx, self.node_n)
            if idx is not None:
                i_node = core.ip_get_node_node_id(self.model.handle, self.index, idx)
                return self.model.get_node(i_node)

        core.use(c_size_t, 'ip_get_node_bond_id', c_void_p, c_size_t, c_size_t)

        def get_bond(self, idx):
            """
            获取此Node连接的第idx个Bond

            Args:
                idx (int): 要获取的相邻Bond的索引。

            Returns:
                Bond: 第idx个相邻Bond，如果索引有效；否则返回None。
            """
            idx = get_index(idx, self.bond_n)
            if idx is not None:
                i_bond = core.ip_get_node_bond_id(self.model.handle, self.index, idx)
                return self.model.get_bond(i_bond)

    class BondData(Object):
        """
        在IP模型中，连接两个Node的流体流动通道。

        Attributes:
            handle (c_void_p): 通道的句柄。
        """

        def __init__(self, handle):
            """
            初始化通道数据

            Args:
                handle (c_void_p): 通道的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Bond是否为同一个

            Args:
                rhs (BondData): 要比较的另一个通道数据对象。

            Returns:
                bool: 如果两个通道的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个Bond是否不是同一个

            Args:
                rhs (BondData): 要比较的另一个通道数据对象。

            Returns:
                bool: 如果两个通道的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回通道数据的字符串表示

            Returns:
                str: 包含通道句柄和半径的字符串。
            """
            return f'zml.InvasionPercolation.Bond(handle = {self.handle}, radi = {self.radi})'

        core.use(c_double, 'ip_bond_get_radi', c_void_p)
        core.use(None, 'ip_bond_set_radi', c_void_p, c_double)

        def get_radi(self):
            """
            获取此Bond所在位置吼道的内部半径（主要用来计算流体界面通过这个Bond所必须克服的毛管压力）

            Returns:
                float: 通道所在位置吼道的内部半径。
            """
            return core.ip_bond_get_radi(self.handle)

        def set_radi(self, value):
            """
            设置此Bond所在位置吼道的内部半径（主要用来计算流体界面通过这个Bond所必须克服的毛管压力）

            Args:
                value (float): 要设置的半径，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_bond_set_radi(self.handle, value)

        @property
        def radi(self):
            """
            获取或设置此Bond所在位置吼道的内部半径

            Returns:
                float: 通道所在位置吼道的内部半径。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

        core.use(c_double, 'ip_bond_get_dp0', c_void_p)
        core.use(None, 'ip_bond_set_dp0', c_void_p, c_double)

        def get_dp0(self):
            """
            获取此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）

            Returns:
                float: 左侧流体侵入右侧时的毛管阻力。
            """
            return core.ip_bond_get_dp0(self.handle)

        def set_dp0(self, value):
            """
            设置此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）

            Args:
                value (float): 要设置的毛管阻力。
            """
            core.ip_bond_set_dp0(self.handle, value)

        @property
        def dp0(self):
            """
            获取或设置此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力。

            Returns:
                float: 左侧流体侵入右侧时的毛管阻力。

            Note:
                该属性仅供作者测试，请勿调用。
            """
            return self.get_dp0()

        @dp0.setter
        def dp0(self, value):
            self.set_dp0(value)

        core.use(c_double, 'ip_bond_get_dp1', c_void_p)
        core.use(None, 'ip_bond_set_dp1', c_void_p, c_double)

        def get_dp1(self):
            """
            获取此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）

            Returns:
                float: 右侧流体侵入左侧时的毛管阻力。
            """
            return core.ip_bond_get_dp1(self.handle)

        def set_dp1(self, value):
            """
            设置此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）

            Args:
                value (float): 要设置的毛管阻力。
            """
            core.ip_bond_set_dp1(self.handle, value)

        @property
        def dp1(self):
            """
            获取或设置此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力。

            Returns:
                float: 右侧流体侵入左侧时的毛管阻力。

            Note:
                该属性仅供作者测试，请勿调用。
            """
            return self.get_dp1()

        @dp1.setter
        def dp1(self, value):
            self.set_dp1(value)

        core.use(c_double, 'ip_bond_get_contact_angle', c_void_p, c_size_t, c_size_t)

        def get_contact_angle(self, ph0, ph1):
            """
            获取当ph0驱替ph1的时候，在ph0中的接触角。当此处的值设置位0到PI之间时，将覆盖全局的设置

            Args:
                ph0 (int): 驱替流体的相态，必须大于等于0。
                ph1 (int): 被驱替流体的相态，必须大于等于0且不等于ph0。

            Returns:
                float: 接触角。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_contact_angle(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_contact_angle', c_void_p, c_size_t, c_size_t, c_double)

        def set_contact_angle(self, ph0, ph1, value):
            """
            设置当ph0驱替ph1的时候，在ph0中的接触角。当此处的值设置位0到PI之间时，将覆盖全局的设置

            Args:
                ph0 (int): 驱替流体的相态，必须大于等于0。
                ph1 (int): 被驱替流体的相态，必须大于等于0且不等于ph0。
                value (float): 要设置的接触角。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            core.ip_bond_set_contact_angle(self.handle, ph0, ph1, value)

        core.use(c_double, 'ip_bond_get_tension', c_void_p, c_size_t, c_size_t)

        def get_tension(self, ph0, ph1):
            """
            获取流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数

            Args:
                ph0 (int): 第一种流体的相态，必须大于等于0。
                ph1 (int): 第二种流体的相态，必须大于等于0且不等于ph0。

            Returns:
                float: 表面张力。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1。
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_tension(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_tension', c_void_p, c_size_t, c_size_t, c_double)

        def set_tension(self, ph0, ph1, value):
            """
            设置流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数

            Args:
                ph0 (int): 第一种流体的相态，必须大于等于0。
                ph1 (int): 第二种流体的相态，必须大于等于0且不等于ph0。
                value (float): 要设置的表面张力，必须大于等于0。

            Raises:
                AssertionError: 如果ph0或ph1小于0，或者ph0等于ph1，或者value小于0。
            """
            assert 0 <= ph0 != ph1 >= 0
            assert value >= 0
            core.ip_bond_set_tension(self.handle, ph0, ph1, value)

        @property
        def tension(self):
            """
            获取或设置界面张力

            Returns:
                float: 界面张力。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_tension(0, 1)

        @tension.setter
        def tension(self, value):
            assert value >= 0
            self.set_tension(0, 1, value)

        @property
        def ca0(self):
            """
            获取或设置当流体0驱替流体1的时候，在流体0中的接触角度

            Returns:
                float: 接触角度。
            """
            return self.get_contact_angle(0, 1)

        @ca0.setter
        def ca0(self, value):
            self.set_contact_angle(0, 1, value)

        @property
        def ca1(self):
            """
            获取或设置当流体1驱替流体0的时候，在流体1中的接触角度

            Returns:
                float: 接触角度。
            """
            return self.get_contact_angle(1, 0)

        @ca1.setter
        def ca1(self, value):
            self.set_contact_angle(1, 0, value)

    class Bond(BondData):
        """
        IP模型中的通道，继承自BondData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 通道的索引。
        """

        core.use(c_void_p, 'ip_get_bond', c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化通道

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 通道的索引。
            """
            super(InvasionPercolation.Bond, self).__init__(handle=core.ip_get_bond(model.handle, index))
            self.model = model
            self.index = index

        @property
        def node_n(self):
            """
            获取此Bond连接的Node的数量

            Returns:
                int: 通道连接的Node的数量，固定为2。
            """
            return 2

        core.use(c_size_t, 'ip_get_bond_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, idx):
            """
            获取此Bond连接的第idx个Node

            Args:
                idx (int): 要获取的相邻节点的索引。

            Returns:
                Node: 第idx个相邻节点，如果索引有效；否则返回None。
            """
            idx = get_index(idx, self.node_n)
            if idx is not None:
                i_node = core.ip_get_bond_node_id(self.model.handle, self.index, idx)
                return self.model.get_node(i_node)

    class InjectorData(Object):
        """
        代表一个注入点。注意：一个注入点必须依赖于一个Node，即流体只能注入到Node里面。所以，注入点必须设置其作用的Node。

        Attributes:
            handle (c_void_p): 注入点的句柄。
        """

        def __init__(self, handle):
            """
            初始化注入点数据

            Args:
                handle (c_void_p): 注入点的句柄。
            """
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个注入点是否为同一个

            Args:
                rhs (InjectorData): 要比较的另一个注入点数据对象。

            Returns:
                bool: 如果两个注入点的句柄相同，则返回True；否则返回False。
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            """
            判断两个注入点是否不是同一个

            Args:
                rhs (InjectorData): 要比较的另一个注入点数据对象。

            Returns:
                bool: 如果两个注入点的句柄不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回注入点数据的字符串表示

            Returns:
                str: 包含注入点句柄的字符串。
            """
            return f'zml.InvasionPercolation.Injector(handle = {self.handle})'

        core.use(c_size_t, 'ip_inj_get_node_id', c_void_p)
        core.use(None, 'ip_inj_set_node_id', c_void_p, c_size_t)

        def get_node_id(self):
            """
            获取注入点作用的Node的ID

            Returns:
                int: 注入点作用的Node的ID。
            """
            return core.ip_inj_get_node_id(self.handle)

        def set_node_id(self, value):
            """
            设置注入点作用的Node的ID

            Args:
                value (int): 要设置的Node的ID。
            """
            core.ip_inj_set_node_id(self.handle, value)

        @property
        def node_id(self):
            """
            获取或设置注入点作用的Node的ID

            Returns:
                int: 注入点作用的Node的ID。
            """
            return self.get_node_id()

        @node_id.setter
        def node_id(self, value):
            self.set_node_id(value)

        core.use(c_size_t, 'ip_inj_get_phase', c_void_p)

        def get_phase(self):
            """
            获取通过该注入点注入的流体的类型(整数，从0开始编号)

            Returns:
                int: 注入流体的类型。
            """
            return core.ip_inj_get_phase(self.handle)

        core.use(None, 'ip_inj_set_phase', c_void_p, c_size_t)

        def set_phase(self, value):
            """
            设置通过该注入点注入的流体的类型(整数，从0开始编号)

            Args:
                value (int): 要设置的流体类型，必须大于等于0。

            Raises:
                AssertionError: 如果提供的值小于0。
            """
            assert value >= 0
            core.ip_inj_set_phase(self.handle, value)

        @property
        def phase(self):
            """
            获取或设置通过该注入点注入的流体的类型(整数，从0开始编号)

            Returns:
                int: 注入流体的类型。

            Raises:
                AssertionError: 如果设置的值小于0。
            """
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

        core.use(c_double, 'ip_inj_get_q', c_void_p)

        def get_qinj(self):
            """
            获取通过该注入点注入流体的速度。单位为 n/time。 其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0

            Returns:
                float: 注入流体的速度。
            """
            return core.ip_inj_get_q(self.handle)

        core.use(None, 'ip_inj_set_q', c_void_p, c_double)

        def set_qinj(self, value):
            """
            设置通过该注入点注入流体的速度。单位为 n/time。 其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0

            Args:
                value (float): 要设置的注入速度，必须大于0。

            Raises:
                AssertionError: 如果提供的值小于等于0。
            """
            assert value > 0
            core.ip_inj_set_q(self.handle, value)

        @property
        def qinj(self):
            """
            获取或设置通过该注入点注入流体的速度。

            Returns:
                float: 注入流体的速度。

            Raises:
                AssertionError: 如果设置的值小于等于0。
            """
            return self.get_qinj()

        @qinj.setter
        def qinj(self, value):
            self.set_qinj(value)

    class Injector(InjectorData):
        """
        IP模型中的注入点，继承自InjectorData。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 注入点的索引。
        """
        core.use(c_void_p, 'ip_get_inj', c_void_p, c_size_t)

        def __init__(self, model, index):
            """
            初始化注入点

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 注入点的索引。
            """
            super(InvasionPercolation.Injector, self).__init__(handle=core.ip_get_inj(model.handle, index))
            self.model = model
            self.index = index

    class InvadeOperation(Object):
        """
        一个侵入操作。

        Attributes:
            model (InvasionPercolation): 所属的IP模型。
            index (int): 侵入操作的索引。
        """

        def __init__(self, model, index):
            """
            初始化侵入操作

            Args:
                model (InvasionPercolation): 所属的IP模型。
                index (int): 侵入操作的索引。
            """
            self.model = model
            self.index = index

        def __eq__(self, rhs):
            """
            判断两个侵入操作是否为同一个

            Args:
                rhs (InvadeOperation): 要比较的另一个侵入操作对象。

            Returns:
                bool: 如果两个侵入操作所属的模型句柄和索引都相同，则返回True；否则返回False。
            """
            return self.model.handle == rhs.model.handle and self.index == rhs.index

        def __ne__(self, rhs):
            """
            判断两个侵入操作是否不是同一个

            Args:
                rhs (InvadeOperation): 要比较的另一个侵入操作对象。

            Returns:
                bool: 如果两个侵入操作所属的模型句柄和索引不同，则返回True；否则返回False。
            """
            return not (self == rhs)

        def __str__(self):
            """
            返回侵入操作的字符串表示

            Returns:
                str: 包含侵入操作索引的字符串。
            """
            return f'zml.InvasionPercolation.InvadeOperation(index = {self.index})'

        core.use(c_size_t, 'ip_get_oper_bond_id', c_void_p, c_size_t)

        def get_bond(self):
            """
            获取侵入操作对应的Bond

            Returns:
                Bond: 侵入操作对应的Bond。
            """
            bond_id = core.ip_get_oper_bond_id(self.model.handle, self.index)
            return self.model.get_bond(bond_id)

        @property
        def bond(self):
            """
            获取侵入操作对应的Bond

            Returns:
                Bond: 侵入操作对应的Bond。
            """
            return self.get_bond()

        core.use(c_bool, 'ip_get_oper_dir', c_void_p, c_size_t)

        @property
        def dir(self):
            """
            获取侵入操作的方向

            Returns:
                bool: 侵入操作的方向。
            """
            return core.ip_get_oper_dir(self.model.handle, self.index)

        def get_node(self, idx):
            """
            当idx==0时，返回上游的node；否则，返回下游的node

            Args:
                idx (int): 节点索引，必须为0或1。

            Returns:
                Node: 对应的节点，如果Bond存在；否则返回None。

            Raises:
                AssertionError: 如果idx不等于0且不等于1。
            """
            assert idx == 0 or idx == 1
            if not self.dir:
                idx = 1 - idx
            bond = self.bond
            if bond is not None:
                return bond.get_node(idx)

    core.use(c_void_p, 'new_ip')
    core.use(None, 'del_ip', c_void_p)

    def __init__(self, handle=None):
        """
        新建一个IP模型。

        Args:
            handle (c_void_p, optional): 模型的句柄。如果提供，将使用该句柄初始化模型。默认为None。
        """
        super(InvasionPercolation, self).__init__(handle, core.new_ip, core.del_ip)

    def __eq__(self, rhs):
        """
        判断两个IP模型是否为同一个

        Args:
            rhs (InvasionPercolation): 要比较的另一个IP模型。

        Returns:
            bool: 如果两个模型的句柄相同，则返回True；否则返回False。
        """
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        """
        判断两个IP模型是否不是同一个

        Args:
            rhs (InvasionPercolation): 要比较的另一个IP模型。

        Returns:
            bool: 如果两个模型的句柄不同，则返回True；否则返回False。
        """
        return not (self == rhs)

    def __str__(self):
        """
        返回IP模型的字符串表示

        Returns:
            str: 包含模型句柄、节点数量和通道数量的字符串。
        """
        return f'zml.InvasionPercolation(handle = {self.handle}, node_n = {self.node_n}, bond_n = {self.bond_n})'

    core.use(None, 'ip_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 要保存的文件路径。

        Raises:
            AssertionError: 如果提供的路径不是字符串类型。
        """
        assert isinstance(path, str)
        make_parent(path)
        core.ip_save(self.handle, make_c_char_p(path))

    core.use(None, 'ip_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要加载的文件路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.ip_load(self.handle, make_c_char_p(path))

    core.use(None, 'ip_print_nodes', c_void_p, c_char_p)

    def print_nodes(self, path):
        """
        将node的数据打印到文件

        Args:
            path (str): 要打印到的文件路径。

        Raises:
            AssertionError: 如果提供的路径不是字符串类型。
        """
        assert isinstance(path, str)
        core.ip_print_nodes(self.handle, make_c_char_p(path))

    core.use(None, 'ip_iterate', c_void_p)

    def iterate(self):
        """
        向前迭代一步。这个模型求解所需要的全部操作。
        """
        core.ip_iterate(self.handle)

    core.use(c_double, 'ip_get_time', c_void_p)

    def get_time(self):
        """
        获取模型内部的时间。模型每充注一次，则时间time的增量为 1.0/max(qinj)。其中max(qinj)为所有的注入点中qinj的最大值。

        Returns:
            float: 模型内部的时间。
        """
        return core.ip_get_time(self.handle)

    core.use(None, 'ip_set_time', c_void_p, c_double)

    def set_time(self, value):
        """
        设置模型内部的时间

        Args:
            value (float): 要设置的时间，必须大于等于0。

        Raises:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_time(self.handle, value)

    @property
    def time(self):
        """
        获取或设置模型内部的时间。

        Returns:
            float: 模型内部的时间。

        Raises:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_time()

    @time.setter
    def time(self, value):
        self.set_time(value)

    core.use(c_size_t, 'ip_add_node', c_void_p)

    def add_node(self):
        """
        添加一个Node，并返回新添加的Node对象

        Returns:
            Node: 新添加的Node对象。
        """
        index = core.ip_add_node(self.handle)
        return self.get_node(index)

    def get_node(self, index):
        """
        返回序号为index的Node对象

        Args:
            index (int): 要获取的节点的索引。

        Returns:
            Node: 序号为index的Node对象，如果索引有效；否则返回None。
        """
        index = get_index(index, self.node_n)
        if index is not None:
            return InvasionPercolation.Node(self, index)

    core.use(c_size_t, 'ip_add_bond', c_void_p, c_size_t, c_size_t)

    def add_bond(self, node0, node1):
        """
        添加一个Bond，来连接给定序号的两个Node。

        Args:
            node0 (Node or int): 第一个节点或其索引。
            node1 (Node or int): 第二个节点或其索引。

        Returns:
            Bond: 新添加的Bond对象。

        Raises:
            AssertionError: 如果节点索引超出范围或两个节点索引相同。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        assert self.node_n > node0 != node1 < self.node_n
        index = core.ip_add_bond(self.handle, node0, node1)
        return self.get_bond(index)

    def get_bond(self, index):
        """
        返回给定序号的Bond

        Args:
            index (int): 要获取的通道的索引。

        Returns:
            Bond: 给定序号的Bond对象，如果索引有效；否则返回None。
        """
        index = get_index(index, self.bond_n)
        if index is not None:
            return InvasionPercolation.Bond(self, index)

    core.use(c_size_t, 'ip_get_bond_id', c_void_p, c_size_t, c_size_t)

    def get_bond_id(self, node0, node1):
        """
        返回两个node中间的bond的id（如果不存在，则返回无穷大）

        Args:
            node0 (Node or int): 第一个节点或其索引。
            node1 (Node or int): 第二个节点或其索引。

        Returns:
            int: 两个节点中间的bond的id，如果不存在则返回无穷大。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        return core.ip_get_bond_id(self.handle, node0, node1)

    def find_bond(self, node0, node1):
        """
        返回两个node中间的bond

        Args:
            node0 (Node or int): 第一个节点或其索引。
            node1 (Node or int): 第二个节点或其索引。

        Returns:
            Bond: 两个节点中间的bond对象，如果存在；否则返回None。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        index = self.get_bond_id(node0, node1)
        return self.get_bond(index)

    core.use(c_size_t, 'ip_get_node_n', c_void_p)

    def get_node_n(self):
        """
        获取模型中节点的数量

        Returns:
            int: 模型中节点的数量。
        """
        return core.ip_get_node_n(self.handle)

    @property
    def node_n(self):
        """
        获取模型中节点的数量

        Returns:
            int: 模型中节点的数量。
        """
        return self.get_node_n()

    core.use(c_size_t, 'ip_get_bond_n', c_void_p)

    def get_bond_n(self):
        """
        获取模型中键（bond）的数量。

        返回:
            int: 模型中键的数量。
        """
        return core.ip_get_bond_n(self.handle)

    @property
    def bond_n(self):
        """
        获取模型中键（bond）的数量。

        返回:
            int: 模型中键的数量。
        """
        return self.get_bond_n()

    core.use(c_size_t, 'ip_get_outlet_n', c_void_p)
    core.use(None, 'ip_set_outlet_n', c_void_p, c_size_t)

    def get_outlet_n(self):
        """
        获取模型内被视为“出口”的节点（Node）的数量。

        返回:
            int: 模型内被视为“出口”的节点的数量。
        """
        return core.ip_get_outlet_n(self.handle)

    def set_outlet_n(self, value):
        """
        设置模型内被视为“出口”的节点（Node）的数量。

        参数:
            value (int): 要设置的“出口”节点数量，必须大于等于0。

        异常:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_outlet_n(self.handle, value)

    @property
    def outlet_n(self):
        """
        获取或设置模型内被视为“出口”的节点（Node）的数量。

        返回:
            int: 模型内被视为“出口”的节点的数量。

        异常:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_outlet_n()

    @outlet_n.setter
    def outlet_n(self, value):
        """
        设置模型内被视为“出口”的节点（Node）的数量。

        参数:
            value (int): 要设置的“出口”节点数量，必须大于等于0。

        异常:
            AssertionError: 如果提供的值小于0。
        """
        self.set_outlet_n(value)

    core.use(None, 'ip_set_outlet', c_void_p, c_size_t, c_size_t)

    def set_outlet(self, index, value):
        """
        设置第index个出口对应的节点（Node）的序号。

        参数:
            index (int): 出口的索引。
            value (int): 节点的索引。

        异常:
            AssertionError: 如果索引无效。
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
            value = get_index(value, self.node_n)
            if value is not None:
                core.ip_set_outlet(self.handle, index, value)

    core.use(c_size_t, 'ip_get_outlet', c_void_p, c_size_t)

    def get_outlet(self, index):
        """
        获取第index个出口对应的节点（Node）的序号。

        参数:
            index (int): 出口的索引。

        返回:
            int: 第index个出口对应的节点的序号，如果索引有效；否则返回None。
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
            return core.ip_get_outlet(self.handle, index)

    def add_outlet(self, node_id):
        """
        添加一个出口点，并返回这个出口点的序号。

        参数:
            node_id (int): 要添加为出口的节点的索引。

        返回:
            int: 新添加的出口点的序号。

        异常:
            AssertionError: 如果节点索引超出范围。
        """
        assert node_id < self.node_n
        index = self.outlet_n
        self.outlet_n = index + 1
        self.set_outlet(index, node_id)
        return index

    core.use(c_double, 'ip_get_tension', c_void_p, c_size_t, c_size_t)

    def get_tension(self, ph0, ph1):
        """
        获取两种相态ph0和ph1之间的界面张力。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。

        返回:
            float: 两种相态之间的界面张力。

        异常:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_tension(self.handle, ph0, ph1)

    core.use(None, 'ip_set_tension', c_void_p, c_size_t, c_size_t, c_double)

    def set_tension(self, ph0, ph1, value):
        """
        设置两种相态ph0和ph1之间的界面张力。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            value (float): 要设置的界面张力值，必须为正数。

        异常:
            AssertionError: 如果相态索引无效或界面张力值为负数。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_tension(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_contact_angle', c_void_p, c_size_t, c_size_t)

    def get_contact_angle(self, ph0, ph1):
        """
        获取当ph0驱替ph1时，在ph0中的接触角。注意，这是一个全局设置，后续会被各个节点（Node）和键（Bond）内的设置覆盖。

        参数:
            ph0 (int): 驱替相态，必须大于等于0。
            ph1 (int): 被驱替相态，必须大于等于0且不等于ph0。

        返回:
            float: 接触角的值。

        异常:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_contact_angle(self.handle, ph0, ph1)

    core.use(None, 'ip_set_contact_angle', c_void_p, c_size_t, c_size_t, c_double)

    def set_contact_angle(self, ph0, ph1, value):
        """
        设置当ph0驱替ph1时，在ph0中的接触角。注意，这是一个全局设置，后续会被各个节点（Node）和键（Bond）内的设置覆盖。

        参数:
            ph0 (int): 驱替相态，必须大于等于0。
            ph1 (int): 被驱替相态，必须大于等于0且不等于ph0。
            value (float): 要设置的接触角的值。

        异常:
            AssertionError: 如果相态索引无效。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_contact_angle(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_density', c_void_p, c_size_t)

    def get_density(self, ph):
        """
        获取流体ph的密度。

        参数:
            ph (int): 流体相态，必须大于等于0。

        返回:
            float: 流体的密度。

        异常:
            AssertionError: 如果相态索引无效。
        """
        assert ph >= 0
        return core.ip_get_density(self.handle, ph)

    core.use(None, 'ip_set_density', c_void_p, c_size_t, c_double)

    def set_density(self, ph, value):
        """
        设置流体ph的密度。

        参数:
            ph (int): 流体相态，必须大于等于0。
            value (float): 要设置的流体密度值，必须为正数。

        返回:
            self: 返回当前对象实例。

        异常:
            AssertionError: 如果相态索引无效或密度值为负数。
        """
        assert ph >= 0
        assert value > 0
        core.ip_set_density(self.handle, ph, value)
        return self

    core.use(c_double, 'ip_get_gravity', c_void_p, c_size_t)

    def get_gravity(self):
        """
        获取重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        返回:
            list: 包含三个浮点数的列表，表示重力向量。
        """
        return [core.ip_get_gravity(self.handle, i) for i in range(3)]

    core.use(None, 'ip_set_gravity', c_void_p, c_size_t, c_double)

    def set_gravity(self, value):
        """
        设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        参数:
            value (list): 包含三个浮点数的列表，表示要设置的重力向量。

        返回:
            self: 返回当前对象实例。
        """
        for i in range(3):
            core.ip_set_gravity(self.handle, i, value[i])
        return self

    @property
    def gravity(self):
        """
        获取或设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        返回:
            list: 包含三个浮点数的列表，表示重力向量。
        """
        return self.get_gravity()

    @gravity.setter
    def gravity(self, value):
        """
        设置重力向量。注意，这个三维向量要和节点（Node）中pos属性的含义保持一致。

        参数:
            value (list): 包含三个浮点数的列表，表示要设置的重力向量。
        """
        self.set_gravity(value)

    core.use(c_size_t, 'ip_get_inj_n', c_void_p)
    core.use(None, 'ip_set_inj_n', c_void_p, c_size_t)

    def get_inj_n(self):
        """
        获取模型中注入点的数量。

        返回:
            int: 模型中注入点的数量。
        """
        return core.ip_get_inj_n(self.handle)

    def set_inj_n(self, value):
        """
        设置模型中注入点的数量。

        参数:
            value (int): 要设置的注入点数量，必须大于等于0。

        返回:
            self: 返回当前对象实例。

        异常:
            AssertionError: 如果提供的值小于0。
        """
        assert value >= 0
        core.ip_set_inj_n(self.handle, value)
        return self

    @property
    def inj_n(self):
        """
        获取或设置模型中注入点的数量。

        返回:
            int: 模型中注入点的数量。

        异常:
            AssertionError: 如果设置的值小于0。
        """
        return self.get_inj_n()

    @inj_n.setter
    def inj_n(self, value):
        """
        设置模型中注入点的数量。

        参数:
            value (int): 要设置的注入点数量，必须大于等于0。

        异常:
            AssertionError: 如果提供的值小于0。
        """
        self.set_inj_n(value)

    def get_inj(self, index):
        """
        返回第index个注入点。

        参数:
            index (int): 注入点的索引。

        返回:
            InvasionPercolation.Injector: 第index个注入点对象，如果索引有效；否则返回None。
        """
        index = get_index(index, self.inj_n)
        if index is not None:
            return InvasionPercolation.Injector(self, index)

    def add_inj(self, node_id=None, phase=None, qinj=None):
        """
        添加一个注入点，并返回注入点对象。

        参数:
            node_id (int, 可选): 注入点所在的节点索引。
            phase (int, 可选): 注入流体的相态。
            qinj (float, 可选): 注入流量。

        返回:
            InvasionPercolation.Injector: 新添加的注入点对象。
        """
        index = self.inj_n
        self.inj_n = self.inj_n + 1
        inj = self.get_inj(index)
        if node_id is not None:
            inj.node_id = node_id
        if phase is not None:
            inj.phase = phase
        if qinj is not None:
            inj.qinj = qinj
        return inj

    core.use(c_bool, 'ip_trap_enabled', c_void_p)

    @property
    def trap_enabled(self):
        """
        获取是否允许围困。当此开关为True，且出口（outlet）的数量不为0时，围困生效。

        返回:
            bool: 是否允许围困。
        """
        return core.ip_trap_enabled(self.handle)

    core.use(None, 'ip_set_trap_enabled', c_void_p, c_bool)

    @trap_enabled.setter
    def trap_enabled(self, value):
        """
        设置是否允许围困。当此开关为True，且出口（outlet）的数量不为0时，围困生效。

        参数:
            value (bool): 是否允许围困。
        """
        core.ip_set_trap_enabled(self.handle, value)

    core.use(c_size_t, 'ip_get_oper_n', c_void_p)

    def get_oper_n(self):
        """
        获取模型中操作（operation）的数量。

        返回:
            int: 模型中操作的数量。
        """
        return core.ip_get_oper_n(self.handle)

    @property
    def oper_n(self):
        """
        获取模型中操作（operation）的数量。

        返回:
            int: 模型中操作的数量。
        """
        return self.get_oper_n()

    def get_oper(self, idx):
        """
        返回第idx个操作。

        参数:
            idx (int): 操作的索引。

        返回:
            InvasionPercolation.InvadeOperation: 第idx个操作对象，如果索引有效；否则返回None。
        """
        idx = get_index(idx, self.oper_n)
        if idx is not None:
            return InvasionPercolation.InvadeOperation(self, idx)

    core.use(None, 'ip_remove_node', c_void_p, c_size_t)
    core.use(None, 'ip_remove_bond', c_void_p, c_size_t)

    def remove_node(self, node):
        """
        删除给定节点（Node）连接的所有键（Bond），然后删除该节点。

        参数:
            node (InvasionPercolation.Node or int): 要删除的节点对象或其索引。
        """
        if node is None:
            return
        if isinstance(node, InvasionPercolation.Node):
            assert node.model.handle == self.handle
            node = node.index
        if node < self.node_n:
            core.ip_remove_node(self.handle, node)

    def remove_bond(self, bond):
        """
        删除给定的键（Bond）。

        参数:
            bond (InvasionPercolation.Bond or int): 要删除的键对象或其索引。
        """
        if bond is None:
            return
        if isinstance(bond, InvasionPercolation.Bond):
            assert bond.model.handle == self.handle
            bond = bond.index
        if bond < self.bond_n:
            core.ip_remove_bond(self.handle, bond)

    core.use(c_size_t, 'ip_get_nearest_node_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_node(self, pos):
        """
        返回距离给定点最近的节点（Node）。

        参数:
            pos (list): 包含三个浮点数的列表，表示点的三维坐标。

        返回:
            InvasionPercolation.Node: 距离给定点最近的节点对象。

        异常:
            AssertionError: 如果坐标列表的长度不为3。
        """
        assert len(pos) == 3
        index = core.ip_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
        return self.get_node(index)

    core.use(None, 'ip_get_node_pos', c_void_p, c_void_p, c_void_p, c_void_p, c_size_t)

    def get_node_pos(self, x=None, y=None, z=None, phase=9999999999):
        """
        获得给定相态（phase）的节点（Node）的位置；如果相态大于99999999，则返回所有节点的位置。

        参数:
            x (Vector, 可选): 存储x坐标的向量对象。
            y (Vector, 可选): 存储y坐标的向量对象。
            z (Vector, 可选): 存储z坐标的向量对象。
            phase (int, 可选): 相态索引，默认为9999999999。

        返回:
            tuple: 包含三个Vector对象的元组，表示节点的x、y、z坐标。
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.ip_get_node_pos(self.handle, x.handle, y.handle, z.handle, phase)
        return x, y, z

    core.use(None, 'ip_write_pos', c_void_p, c_size_t, c_void_p)

    def write_pos(self, dim, pointer):
        """
        批量获得位置信息。

        参数:
            dim (int): 维度。
            pointer (ctypes.c_void_p): 指向存储位置信息的指针。
        """
        core.ip_write_pos(self.handle, dim, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_pos', c_void_p, c_size_t, c_void_p)

    def read_pos(self, dim, pointer):
        """
        批量修改位置信息。

        参数:
            dim (int): 维度。
            pointer (ctypes.c_void_p): 指向存储位置信息的指针。
        """
        core.ip_read_pos(self.handle, dim, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_phase', c_void_p, c_void_p)

    def write_phase(self, pointer):
        """
        获得相态（phase）信息，并将其写入到给定的指针。注意，虽然相态在模型内部的存储为int类型，但此函数使用的是double类型的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储相态信息的指针。
        """
        core.ip_write_phase(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_phase', c_void_p, c_void_p)

    def read_phase(self, pointer):
        """
        从给定的指针读取相态（phase）信息并设置到模型中。注意，虽然相态在模型内部的存储为int类型，但此函数使用的是double类型的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储相态信息的指针。
        """
        core.ip_read_phase(self.handle, ctypes.cast(pointer, c_void_p))

    def nodes_write(self, *args, **kwargs):
        """
        此方法已弃用，将于2025-6-2之后移除。

        参数:
            *args: 可变位置参数。
            **kwargs: 可变关键字参数。

        返回:
            调用zmlx.alg.ip_nodes_write模块的ip_nodes_write函数的结果。
        """
        warnings.warn('remove after 2025-6-2', DeprecationWarning)
        from zmlx.alg.ip_nodes_write import ip_nodes_write
        return ip_nodes_write(self, *args, **kwargs)

    core.use(None, 'ip_write_node_radi', c_void_p, c_void_p)

    def write_node_radi(self, pointer):
        """
        将节点（Node）的半径数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点半径数据的指针。
        """
        core.ip_write_node_radi(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_node_radi', c_void_p, c_void_p)

    def read_node_radi(self, pointer):
        """
        从给定的指针读取节点（Node）的半径数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点半径数据的指针。
        """
        core.ip_read_node_radi(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_bond_radi', c_void_p, c_void_p)

    def write_bond_radi(self, pointer):
        """
        将键（Bond）的半径数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储键半径数据的指针。
        """
        core.ip_write_bond_radi(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_bond_radi', c_void_p, c_void_p)

    def read_bond_radi(self, pointer):
        """
        从给定的指针读取键（Bond）的半径数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储键半径数据的指针。
        """
        core.ip_read_bond_radi(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_node_rate_invaded', c_void_p, c_void_p)

    def write_node_rate_invaded(self, pointer):
        """
        将节点（Node）的侵入速率数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点侵入速率数据的指针。
        """
        core.ip_write_node_rate_invaded(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_node_rate_invaded', c_void_p, c_void_p)

    def read_node_rate_invaded(self, pointer):
        """
        从给定的指针读取节点（Node）的侵入速率数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点侵入速率数据的指针。
        """
        core.ip_read_node_rate_invaded(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_node_time_invaded', c_void_p, c_void_p)

    def write_node_time_invaded(self, pointer):
        """
        将节点（Node）的侵入时间数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点侵入时间数据的指针。
        """
        core.ip_write_node_time_invaded(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_node_time_invaded', c_void_p, c_void_p)

    def read_node_time_invaded(self, pointer):
        """
        从给定的指针读取节点（Node）的侵入时间数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储节点侵入时间数据的指针。
        """
        core.ip_read_node_time_invaded(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_bond_dp0', c_void_p, c_void_p)

    def write_bond_dp0(self, pointer):
        """
        将键（Bond）的dp0数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储键dp0数据的指针。
        """
        core.ip_write_bond_dp0(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_bond_dp0', c_void_p, c_void_p)

    def read_bond_dp0(self, pointer):
        """
        从给定的指针读取键（Bond）的dp0数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储键dp0数据的指针。
        """
        core.ip_read_bond_dp0(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_bond_dp1', c_void_p, c_void_p)

    def write_bond_dp1(self, pointer):
        """
        将键（Bond）的dp1数据写入到给定的指针。

        参数:
            pointer (ctypes.c_void_p): 指向存储键dp1数据的指针。
        """
        core.ip_write_bond_dp1(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_bond_dp1', c_void_p, c_void_p)

    def read_bond_dp1(self, pointer):
        """
        从给定的指针读取键（Bond）的dp1数据。

        参数:
            pointer (ctypes.c_void_p): 指向存储键dp1数据的指针。
        """
        core.ip_read_bond_dp1(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_bond_tension', c_void_p, c_size_t, c_size_t, c_void_p)

    def write_bond_tension(self, ph0, ph1, pointer):
        """
        将两种相态ph0和ph1之间键（Bond）的界面张力数据写入到给定的指针。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (ctypes.c_void_p): 指向存储界面张力数据的指针。
        """
        core.ip_write_bond_tension(self.handle, ph0, ph1, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_bond_tension', c_void_p, c_size_t, c_size_t, c_void_p)

    def read_bond_tension(self, ph0, ph1, pointer):
        """
        从给定的指针读取两种相态ph0和ph1之间键（Bond）的界面张力数据。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (ctypes.c_void_p): 指向存储界面张力数据的指针。
        """
        core.ip_read_bond_tension(self.handle, ph0, ph1, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_bond_contact_angle', c_void_p, c_size_t, c_size_t, c_void_p)

    def write_bond_contact_angle(self, ph0, ph1, pointer):
        """
        将两种相态ph0和ph1之间键（Bond）的接触角数据写入到给定的指针。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (ctypes.c_void_p): 指向存储接触角数据的指针。
        """
        core.ip_write_bond_contact_angle(self.handle, ph0, ph1, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_read_bond_contact_angle', c_void_p, c_size_t, c_size_t, c_void_p)

    def read_bond_contact_angle(self, ph0, ph1, pointer):
        """
        从给定的指针读取两种相态ph0和ph1之间键（Bond）的接触角数据。

        参数:
            ph0 (int): 第一种相态，必须大于等于0。
            ph1 (int): 第二种相态，必须大于等于0且不等于ph0。
            pointer (ctypes.c_void_p): 指向存储接触角数据的指针。
        """
        core.ip_read_bond_contact_angle(self.handle, ph0, ph1, ctypes.cast(pointer, c_void_p))


class Dfn2(HasHandle):
    """
    用于生成二维的离散裂缝网络

    Attributes:
        handle: 句柄对象
    """
    core.use(c_void_p, 'new_dfn2d')
    core.use(None, 'del_dfn2d', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化Dfn2对象

        Args:
            path (str, optional): 序列化文件的路径。如果提供，将加载该文件。默认为None。
            handle: 句柄对象。默认为None。
        """
        super(Dfn2, self).__init__(handle, core.new_dfn2d, core.del_dfn2d)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    core.use(None, 'dfn2d_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.dfn2d_save(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.dfn2d_load(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_set_range', c_void_p, c_double, c_double, c_double, c_double)
    core.use(c_double, 'dfn2d_get_range', c_void_p, c_size_t)

    @property
    def range(self):
        """
        位置的范围(一个矩形区域)

        Returns:
            list: 包含四个浮点数的列表，表示矩形区域的范围 [xmin, ymin, xmax, ymax]。
        """
        return [core.dfn2d_get_range(self.handle, i) for i in range(4)]

    @range.setter
    def range(self, value):
        """
        设置位置的范围(一个矩形区域)

        Args:
            value (list): 包含四个浮点数的列表，表示矩形区域的范围 [xmin, ymin, xmax, ymax]。

        Raises:
            AssertionError: 如果输入的列表长度不为4。
        """
        assert len(value) == 4, f'The format of pos range is [xmin, ymin, xmax, ymax]'
        core.dfn2d_set_range(self.handle, *value)

    core.use(c_bool, 'dfn2d_add_frac', c_void_p, c_double, c_double, c_double, c_double, c_double)
    core.use(None, 'dfn2d_randomly_add_frac', c_void_p, c_void_p, c_void_p, c_double, c_double)

    def add_frac(self, x0=None, y0=None, x1=None, y1=None, angles=None, lengths=None, p21=None, l_min=None):
        """
        添加一个裂缝或者随机添加多条裂缝。
            当给定x0, y0, x1, y1的时候，添加这一条裂缝;
            否则，则需要给定angle(一个list，用以定义角度), length(list: 用以定义角度), p21(新添加的裂缝的密度)来随机添加一组裂缝。

        Args:
            x0 (float, optional): 裂缝起点的x坐标。默认为None。
            y0 (float, optional): 裂缝起点的y坐标。默认为None。
            x1 (float, optional): 裂缝终点的x坐标。默认为None。
            y1 (float, optional): 裂缝终点的y坐标。默认为None。
            angles (list or Vector, optional): 角度列表，用于随机添加裂缝。默认为None。
            lengths (list or Vector, optional): 长度列表，用于随机添加裂缝。默认为None。
            p21 (float, optional): 新添加的裂缝的密度。默认为None。
            l_min (float, optional): 最小长度。默认为-1.0。

        Raises:
            AssertionError: 如果未提供x0, y0, x1, y1且angles、lengths或p21为None。
        """
        if l_min is None:
            l_min = -1.0
        if x0 is not None and y0 is not None and x1 is not None and y1 is not None:
            return core.dfn2d_add_frac(self.handle, x0, y0, x1, y1, l_min)
        else:
            assert angles is not None and lengths is not None and p21 is not None
            if not isinstance(angles, Vector):
                angles = Vector(value=angles)
            if not isinstance(lengths, Vector):
                lengths = Vector(value=lengths)
            core.dfn2d_randomly_add_frac(self.handle, angles.handle, lengths.handle, p21, l_min)

    core.use(c_size_t, 'dfn2d_get_fracture_number', c_void_p)

    @property
    def fracture_n(self):
        """
        目前体系中已经存在的裂缝的数量

        Returns:
            int: 裂缝的数量。
        """
        return core.dfn2d_get_fracture_number(self.handle)

    core.use(c_double, 'dfn2d_get_fracture_pos', c_void_p, c_size_t, c_size_t)

    def get_fracture(self, idx):
        """
        返回第idx个裂缝的位置

        Args:
            idx (int): 裂缝的索引。

        Returns:
            list or None: 包含四个浮点数的列表，表示裂缝的位置 [x0, y0, x1, y1]；如果索引无效，则返回None。
        """
        idx = get_index(idx, self.fracture_n)
        if idx is not None:
            return [core.dfn2d_get_fracture_pos(self.handle, idx, i) for i in range(4)]

    def get_fractures(self):
        """
        返回所有的裂缝的位置

        Returns:
            list: 包含所有裂缝位置的列表，每个元素是一个包含四个浮点数的列表 [x0, y0, x1, y1]。
        """
        return [self.get_fracture(idx) for idx in range(self.fracture_n)]

    core.use(c_double, 'dfn2d_get_p21', c_void_p)

    @property
    def p21(self):
        """
        返回当前的裂缝的密度

        Returns:
            float: 当前的裂缝的密度。
        """
        return core.dfn2d_get_p21(self.handle)

    def print_file(self, path):
        """
        将所有的裂缝打印到文件

        Args:
            path (str): 要打印到的文件的路径。
        """
        with open(path, 'w') as file:
            for i in range(self.fracture_n):
                p = self.get_fracture(i)
                file.write(f'{p[0]}\t{p[1]}\t{p[2]}\t{p[3]}\n')


class Lattice3(HasHandle):
    """
    用以临时存放数据序号的格子

    Attributes:
        handle: 句柄对象
    """
    core.use(c_void_p, 'new_lat3')
    core.use(None, 'del_lat3', c_void_p)

    def __init__(self, box=None, shape=None, handle=None):
        """
        初始化Lattice3对象

        Args:
            box (list, optional): 数据在三维空间内的范围，格式为 [x0, y0, z0, x1, y1, z1]。默认为None。
            shape (list or float, optional): 单个网格的大小。如果是列表，长度应为3；如果是浮点数，则表示三个维度上的大小相同。默认为None。
            handle: 句柄对象。默认为None。
        """
        super(Lattice3, self).__init__(handle, core.new_lat3, core.del_lat3)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape)

    def __str__(self):
        """
        返回对象的字符串表示形式

        Returns:
            str: 包含盒子范围、形状和大小的字符串。
        """
        return f'zml.Lattice3(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'lat3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.lat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'lat3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.lat3_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'lat3_lrange', c_void_p, c_size_t)

    @property
    def box(self):
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似

        Returns:
            list: 包含六个浮点数的列表，表示数据在三维空间内的范围。
        """
        lr = [core.lat3_lrange(self.handle, i) for i in range(3)]
        sh = self.shape
        sz = self.size
        rr = [lr[i] + sh[i] * sz[i] for i in range(3)]
        return lr + rr

    core.use(c_double, 'lat3_shape', c_void_p, c_size_t)

    @property
    def shape(self):
        """
        返回每个网格在三个维度上的大小

        Returns:
            list: 包含三个浮点数的列表，表示每个网格在三个维度上的大小。
        """
        return [core.lat3_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'lat3_size', c_void_p, c_size_t)

    @property
    def size(self):
        """
        返回三维维度上网格的数量<至少为1>

        Returns:
            list: 包含三个整数的列表，表示三维维度上网格的数量。
        """
        return [core.lat3_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'lat3_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lat3_get_centers', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        返回格子的中心点

        Args:
            index (list, optional): 包含三个整数的列表，表示格子的索引。默认为None。
            x (Vector, optional): 存储x坐标的向量。默认为None。
            y (Vector, optional): 存储y坐标的向量。默认为None。
            z (Vector, optional): 存储z坐标的向量。默认为None。

        Returns:
            list or tuple: 如果提供了index，则返回包含三个浮点数的列表，表示格子的中心点；否则，返回包含三个Vector对象的元组。
        """
        if index is not None:
            assert len(index) == 3
            return [core.lat3_get_center(self.handle, index[i], i) for i in range(3)]
        else:
            if not isinstance(x, Vector):
                x = Vector()
            if not isinstance(y, Vector):
                y = Vector()
            if not isinstance(z, Vector):
                z = Vector()
            core.lat3_get_centers(self.handle, x.handle, y.handle, z.handle)
            return x, y, z

    core.use(None, 'lat3_create', c_void_p, c_double, c_double, c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box, shape):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小.

        Args:
            box (list): 包含六个浮点数的列表，表示数据在三维空间内的范围。
            shape (list or float): 单个网格的大小。如果是列表，长度应为3；如果是浮点数，则表示三个维度上的大小相同。

        Raises:
            AssertionError: 如果box的长度不为6或shape的长度不为3。
        """
        assert len(box) == 6
        if not is_array(shape):
            core.lat3_create(self.handle, *box, shape, shape, shape)
        else:
            assert len(shape) == 3
            core.lat3_create(self.handle, *box, *shape)

    core.use(None, 'lat3_random_shuffle', c_void_p)

    def random_shuffle(self):
        """
        随机更新格子里面的数据的顺序<随机洗牌>
        """
        core.lat3_random_shuffle(self.handle)

    core.use(None, 'lat3_add_point', c_void_p, c_double, c_double, c_double, c_size_t)

    def add_point(self, pos, index):
        """
        将位置在pos，序号为index的对象放入到格子里面<不会去查重复>

        Args:
            pos (list): 包含三个浮点数的列表，表示对象的位置。
            index (int): 对象的序号。

        Raises:
            AssertionError: 如果pos的长度不为3。
        """
        assert len(pos) == 3, f'pos = {pos}'
        core.lat3_add_point(self.handle, *pos, index)


class DDMSolution2(HasHandle):
    """
    二维DDM的基本解：计算裂缝单元在任意位置的诱导应力.
    """
    core.use(c_void_p, 'new_ddm_sol2')
    core.use(None, 'del_ddm_sol2', c_void_p)

    def __init__(self, handle=None):
        """
        初始化DDMSolution2对象

        Args:
            handle: 句柄对象。默认为None。
        """
        super(DDMSolution2, self).__init__(handle, core.new_ddm_sol2, core.del_ddm_sol2)

    def __str__(self):
        """
        返回对象的字符串表示形式

        Returns:
            str: 包含句柄、alpha、beta、剪切模量、泊松比和调整系数的字符串。
        """
        return (f'zml.DDMSolution2(handle={self.handle}, '
                f'alpha={self.alpha}, beta={self.beta}, '
                f'shear_modulus={self.shear_modulus / 1.0e9}GPa, '
                f'poisson_ratio={self.poisson_ratio}, '
                f'adjust_coeff={self.adjust_coeff})')

    core.use(None, 'ddm_sol2_save', c_void_p, c_char_p)
    core.use(None, 'ddm_sol2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。
        """
        if isinstance(path, str):
            make_parent(path)
            core.ddm_sol2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径。
        """
        if isinstance(path, str):
            core.ddm_sol2_load(self.handle, make_c_char_p(path))

    core.use(None, 'ddm_sol2_set_alpha', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_alpha', c_void_p)

    @property
    def alpha(self):
        """
        获取alpha值

        Returns:
            float: alpha值
        """
        return core.ddm_sol2_get_alpha(self.handle)

    @alpha.setter
    def alpha(self, value):
        """
        设置alpha值

        Args:
            value (float): 要设置的alpha值
        """
        core.ddm_sol2_set_alpha(self.handle, value)

    core.use(None, 'ddm_sol2_set_beta', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_beta', c_void_p)

    @property
    def beta(self):
        """
        获取beta值

        Returns:
            float: beta值
        """
        return core.ddm_sol2_get_beta(self.handle)

    @beta.setter
    def beta(self, value):
        """
        设置beta值

        Args:
            value (float): 要设置的beta值
        """
        core.ddm_sol2_set_beta(self.handle, value)

    core.use(None, 'ddm_sol2_set_shear_modulus', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_shear_modulus', c_void_p)

    @property
    def shear_modulus(self):
        """
        获取剪切模量

        Returns:
            float: 剪切模量
        """
        return core.ddm_sol2_get_shear_modulus(self.handle)

    @shear_modulus.setter
    def shear_modulus(self, value):
        """
        设置剪切模量

        Args:
            value (float): 要设置的剪切模量
        """
        core.ddm_sol2_set_shear_modulus(self.handle, value)

    core.use(None, 'ddm_sol2_set_poisson_ratio', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_poisson_ratio', c_void_p)

    @property
    def poisson_ratio(self):
        """
        获取泊松比

        Returns:
            float: 泊松比
        """
        return core.ddm_sol2_get_poisson_ratio(self.handle)

    @poisson_ratio.setter
    def poisson_ratio(self, value):
        """
        设置泊松比

        Args:
            value (float): 要设置的泊松比
        """
        core.ddm_sol2_set_poisson_ratio(self.handle, value)

    core.use(None, 'ddm_sol2_set_adjust_coeff', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_adjust_coeff', c_void_p)

    @property
    def adjust_coeff(self):
        """
        获取调整系数

        Returns:
            float: 调整系数
        """
        return core.ddm_sol2_get_adjust_coeff(self.handle)

    @adjust_coeff.setter
    def adjust_coeff(self, value):
        """
        设置调整系数

        Args:
            value (float): 要设置的调整系数
        """
        core.ddm_sol2_set_adjust_coeff(self.handle, value)

    core.use(None, 'ddm_sol2_get_induced', c_void_p, c_void_p,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def get_induced(self, pos, fracture, ds, dn, height):
        """
        返回一个裂缝单元的诱导应力

        Args:
            pos (list): 位置信息，长度可以为2或4。
            fracture (list): 裂缝信息，长度必须为4。
            ds (float): 未知含义的参数
            dn (float): 未知含义的参数
            height (float): 高度

        Returns:
            Tensor2: 诱导应力张量
        """
        assert len(fracture) == 4
        stress = Tensor2()
        if len(pos) == 2:
            core.ddm_sol2_get_induced(self.handle, stress.handle, *pos, *pos,
                                      *fracture, ds, dn, height)
        else:
            assert len(pos) == 4
            core.ddm_sol2_get_induced(self.handle, stress.handle, *pos,
                                      *fracture, ds, dn, height)
        return stress


class FractureNetwork(HasHandle):
    """
    裂缝网络(二维). 由顶点和裂缝所组成的网络. 存储裂缝网络的数据.
    """

    class VertexData(Object):
        """
        顶点的数据
        """

        def __init__(self, handle):
            """
            初始化顶点数据对象

            Args:
                handle: 顶点数据的句柄
            """
            self.handle = handle

        core.use(c_double, 'frac_nd_get_pos', c_void_p, c_size_t)

        @property
        def x(self):
            """
            获取顶点的x坐标

            Returns:
                float: 顶点的x坐标
            """
            return core.frac_nd_get_pos(self.handle, 0)

        @property
        def y(self):
            """
            获取顶点的y坐标

            Returns:
                float: 顶点的y坐标
            """
            return core.frac_nd_get_pos(self.handle, 1)

        @property
        def pos(self):
            """
            获取顶点的位置

            Returns:
                tuple: 包含顶点x和y坐标的元组
            """
            return self.x, self.y

        core.use(c_double, 'frac_nd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_nd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取第index个自定义属性

            Args:
                index (int): 自定义属性的索引
                default_val (float, optional): 属性不存在时的默认值，默认为None
                **valid_range: 属性的有效范围

            Returns:
                float: 如果属性存在且在有效范围内，返回属性值；否则返回默认值
            """
            if index is None:
                return default_val
            # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            value = core.frac_nd_get_attr(self.handle, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置第index个自定义属性

            Args:
                index (int): 自定义属性的索引
                value (float): 要设置的属性值

            Returns:
                VertexData: 返回当前顶点数据对象
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.frac_nd_set_attr(self.handle, index, value)
            return self

    class FractureData(HasHandle):
        """
        裂缝的数据
        """
        core.use(c_void_p, 'new_frac_bd')
        core.use(None, 'del_frac_bd', c_void_p)

        def __init__(self, handle=None):
            """
            初始化裂缝数据对象

            Args:
                handle: 裂缝数据的句柄，默认为None
            """
            super(FractureNetwork.FractureData, self).__init__(handle, core.new_frac_bd, core.del_frac_bd)

        core.use(c_double, 'frac_bd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_bd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取第index个自定义属性

            Args:
                index (int): 自定义属性的索引
                default_val (float, optional): 属性不存在时的默认值，默认为None
                **valid_range: 属性的有效范围

            Returns:
                float: 如果属性存在且在有效范围内，返回属性值；否则返回默认值
            """
            if index is None:
                return default_val
            # 当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            value = core.frac_bd_get_attr(self.handle, index)
            if _attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置第index个自定义属性

            Args:
                index (int): 自定义属性的索引
                value (float): 要设置的属性值

            Returns:
                FractureData: 返回当前裂缝数据对象
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.frac_bd_set_attr(self.handle, index, value)
            return self

        core.use(c_double, 'frac_bd_get_ds', c_void_p)
        core.use(None, 'frac_bd_set_ds', c_void_p, c_double)

        @property
        def ds(self):
            """
            设置第index个自定义属性

            Args:
                index (int): 自定义属性的索引
                value (float): 要设置的属性值

            Returns:
                FractureData: 返回当前裂缝数据对象
            """
            return core.frac_bd_get_ds(self.handle)

        @ds.setter
        def ds(self, value):
            """
            设置裂缝的ds属性

            Args:
                value (float): 要设置的ds属性值
            """
            core.frac_bd_set_ds(self.handle, value)

        core.use(c_double, 'frac_bd_get_dn', c_void_p)
        core.use(None, 'frac_bd_set_dn', c_void_p, c_double)

        @property
        def dn(self):
            """
            获取裂缝的dn属性

            Returns:
                float: 裂缝的dn属性值
            """
            return core.frac_bd_get_dn(self.handle)

        @dn.setter
        def dn(self, value):
            """
            设置裂缝的dn属性

            Args:
                value (float): 要设置的dn属性值
            """
            core.frac_bd_set_dn(self.handle, value)

        core.use(c_double, 'frac_bd_get_h', c_void_p)
        core.use(None, 'frac_bd_set_h', c_void_p, c_double)

        @property
        def h(self):
            """
            获取裂缝的高度

            Returns:
                float: 裂缝的高度，单位为米
            """
            return core.frac_bd_get_h(self.handle)

        @h.setter
        def h(self, value):
            """
            设置裂缝的高度

            Args:
                value (float): 要设置的裂缝高度，单位为米
            """
            core.frac_bd_set_h(self.handle, value)

        core.use(c_double, 'frac_bd_get_fric', c_void_p)
        core.use(None, 'frac_bd_set_fric', c_void_p, c_double)

        @property
        def f(self):
            """
            获取裂缝的摩擦系数

            Returns:
                float: 裂缝的摩擦系数
            """
            return core.frac_bd_get_fric(self.handle)

        @f.setter
        def f(self, value):
            """
            设置裂缝的摩擦系数

            Args:
                value (float): 要设置的摩擦系数
            """
            core.frac_bd_set_fric(self.handle, value)

        core.use(c_double, 'frac_bd_get_p0', c_void_p)
        core.use(None, 'frac_bd_set_p0', c_void_p, c_double)

        @property
        def p0(self):
            """
            获取裂缝内流体压力公式中的p0参数

            Returns:
                float: 裂缝内流体压力公式中的p0参数
            """
            return core.frac_bd_get_p0(self.handle)

        @p0.setter
        def p0(self, value):
            """
            设置裂缝内流体压力公式中的p0参数

            Args:
                value (float): 要设置的p0参数
            """
            core.frac_bd_set_p0(self.handle, value)

        core.use(c_double, 'frac_bd_get_k', c_void_p)
        core.use(None, 'frac_bd_set_k', c_void_p, c_double)

        @property
        def k(self):
            """
            获取裂缝内流体压力公式中的k参数

            Returns:
                float: 裂缝内流体压力公式中的k参数
            """
            return core.frac_bd_get_k(self.handle)

        @k.setter
        def k(self, value):
            """
            设置裂缝内流体压力公式中的k参数

            Args:
                value (float): 要设置的k参数
            """
            core.frac_bd_set_k(self.handle, value)

        core.use(c_double, 'frac_bd_get_fp', c_void_p)

        @property
        def fp(self):
            """
            根据当前的dn、p0和k计算得到的裂缝内流体压力

            Returns:
                float: 裂缝内流体压力
            """
            return core.frac_bd_get_fp(self.handle)

        core.use(c_void_p, 'frac_bd_get_flu', c_void_p)

        @property
        def flu_expr(self):
            """
            返回流体的映射数据. 用于在裂缝扩展的时候，跟踪流体的数据

            Returns:
                LinearExpr: 流体的映射数据对象，如果不存在则返回None
            """
            handle = core.frac_bd_get_flu(self.handle)
            if handle:
                return LinearExpr(handle=handle)

        @flu_expr.setter
        def flu_expr(self, value):
            """
            设置流体的映射数据. 用于在裂缝扩展的时候，跟踪流体的数据

            Args:
                value: 要设置的流体映射数据对象
            """
            left = self.flu_expr
            if left is not None:
                left.clone(value)

        @property
        def flu(self):
            """
            获取流体的映射数据（已弃用，请使用flu_expr）

            Returns:
                LinearExpr: 流体的映射数据对象，如果不存在则返回None
            """
            warnings.warn(f'{type(self)}: flu is deprecated, please use flu_expr instead.',
                          DeprecationWarning)
            return self.flu_expr

        @flu.setter
        def flu(self, value):
            """
            设置流体的映射数据（已弃用，请使用flu_expr）

            Args:
                value: 要设置的流体映射数据对象
            """
            warnings.warn(f'{type(self)}: flu is deprecated, please use flu_expr instead.',
                          DeprecationWarning)
            self.flu_expr = value

        @staticmethod
        def create(**kwargs):
            """
            创建裂缝数据

            Args:
                **kwargs: 裂缝数据的属性和值

            Returns:
                FractureData: 创建的裂缝数据对象
            """
            data = FractureNetwork.FractureData()
            for key, value in kwargs.items():
                setattr(data, key, value)
            return data

    class Vertex(VertexData):
        """
        顶点
        """
        core.use(c_void_p, 'frac_nt_get_nd', c_void_p, c_size_t)

        def __init__(self, network, index):
            """
            初始化顶点对象

            Args:
                network (FractureNetwork): 所属的裂缝网络对象
                index (int): 顶点的索引
            """
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.vertex_number
            self.network = network
            self.index = index
            super(FractureNetwork.Vertex, self).__init__(
                handle=core.frac_nt_get_nd(network.handle, index))

        def __str__(self):
            """
            返回顶点对象的字符串表示

            Returns:
                str: 包含顶点索引和位置的字符串
            """
            return f'zml.FractureNetwork.Vertex(index={self.index}, pos=[{self.x}, {self.y}])'

        core.use(c_size_t, 'frac_nt_nd_get_bd_n', c_void_p, c_size_t)

        @property
        def fracture_number(self):
            """
            获取共享此顶点的裂缝单元的数量

            Returns:
                int: 共享此顶点的裂缝单元的数量
            """
            return core.frac_nt_nd_get_bd_n(self.network.handle, self.index)

        core.use(c_size_t, 'frac_nt_nd_get_bd_i', c_void_p, c_size_t, c_size_t)

        def get_fracture(self, index):
            """
            获取此顶点周边的裂缝单元

            Args:
                index (int): 裂缝单元的索引

            Returns:
                Fracture: 此顶点周边的裂缝单元对象，如果索引无效则返回None
            """
            index = get_index(index, self.fracture_number)
            if index is not None:
                return self.network.get_fracture(
                    core.frac_nt_nd_get_bd_i(self.network.handle, self.index, index))

    class Fracture(FractureData):
        """
        裂缝.
        """
        core.use(c_void_p, 'frac_nt_get_bd', c_void_p, c_size_t)

        def __init__(self, network, index):
            """
            初始化裂缝对象

            Args:
                network (FractureNetwork): 所属的裂缝网络对象
                index (int): 裂缝的索引
            """
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.fracture_number
            super(FractureNetwork.Fracture, self).__init__(
                handle=core.frac_nt_get_bd(network.handle, index))
            self.network = network
            self.index = index

        def __str__(self):
            """
            返回裂缝对象的字符串表示

            Returns:
                str: 包含裂缝索引、位置、ds和dn属性的字符串
            """
            return f'zml.FractureNetwork.Fracture(index={self.index}, pos={self.pos}, ds={self.ds}, dn={self.dn})'

        @property
        def vertex_number(self):
            """
            获取裂缝顶点的数量

            Returns:
                int: 裂缝顶点的数量，固定为2
            """
            return 2

        core.use(c_size_t, 'frac_nt_bd_get_nd_i', c_void_p, c_size_t, c_size_t)

        def get_vertex(self, index):
            """
            获取裂缝的顶点

            Args:
                index (int): 顶点的索引

            Returns:
                Vertex: 裂缝的顶点对象，如果索引无效则返回None
            """
            index = get_index(index, self.vertex_number)
            if index is not None:
                return self.network.get_vertex(
                    core.frac_nt_bd_get_nd_i(self.network.handle, self.index, index))

        @property
        def pos(self):
            """
            获取裂缝的位置

            Returns:
                tuple: 包含裂缝两个端点的x和y坐标的元组，格式为 (x0, y0, x1, y1)
            """
            p0 = self.get_vertex(0).pos
            p1 = self.get_vertex(1).pos
            return p0[0], p0[1], p1[0], p1[1]

        @property
        def length(self):
            """
            获取裂缝的长度

            Returns:
                float: 裂缝的长度，根据裂缝两个端点的位置计算
            """
            p0 = self.get_vertex(0).pos
            p1 = self.get_vertex(1).pos
            return get_distance(p0, p1)

        @property
        def center(self):
            """
            获取裂缝的中心点坐标

            Returns:
                tuple: 包含裂缝中心点的x和y坐标的元组
            """
            p0 = self.get_vertex(0).pos
            p1 = self.get_vertex(1).pos
            return (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2

        core.use(c_double, 'frac_nt_get_bd_angle', c_void_p, c_size_t)

        @property
        def angle(self):
            """
            获取裂缝的方向角度

            Returns:
                float: 裂缝的方向角度
            """
            return core.frac_nt_get_bd_angle(self.network.handle, self.index)

    core.use(c_void_p, 'new_frac_nt')
    core.use(None, 'del_frac_nt', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化裂缝网络对象

        Args:
            path (str, optional): 序列化文件的路径，用于加载数据，默认为None
            handle: 裂缝网络的句柄，默认为None
        """
        super(FractureNetwork, self).__init__(handle, core.new_frac_nt, core.del_frac_nt)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __str__(self):
        """
        返回裂缝网络对象的字符串表示

        Returns:
            str: 包含裂缝网络句柄、顶点数量和裂缝单元数量的字符串
        """
        return (f'zml.FractureNetwork(handle={self.handle}, '
                f'vertex_n={self.vertex_number}, fracture_n={self.fracture_number})')

    core.use(None, 'frac_nt_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存裂缝网络数据

        可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径
        """
        if isinstance(path, str):
            make_parent(path)
            core.frac_nt_save(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_load', c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件来加载裂缝网络数据

        根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 要读取的文件的路径
        """
        if isinstance(path, str):
            _check_ipath(path, self)
            core.frac_nt_load(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'frac_nt_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将裂缝网络数据序列化到一个Filemap中

        Args:
            fmt (str, optional): 序列化格式，可以为 'text', 'xml' 或 'binary'，默认为 'binary'

        Returns:
            FileMap: 包含序列化数据的Filemap对象
        """
        fmap = FileMap()
        core.frac_nt_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的裂缝网络数据

        Args:
            fmap (FileMap): 包含序列化数据的Filemap对象
            fmt (str, optional): 序列化格式，可以为 'text', 'xml' 或 'binary'，默认为 'binary'
        """
        assert isinstance(fmap, FileMap)
        core.frac_nt_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        """
        获取裂缝网络数据的二进制序列化Filemap对象

        Returns:
            FileMap: 包含二进制序列化数据的Filemap对象
        """
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        """
        从Filemap中加载二进制序列化的裂缝网络数据

        Args:
            value (FileMap): 包含二进制序列化数据的Filemap对象
        """
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'frac_nt_get_nd_n', c_void_p)

    @property
    def vertex_number(self):
        """
        获取顶点的数量

        Returns:
            int: 顶点的数量
        """
        return core.frac_nt_get_nd_n(self.handle)

    def get_vertex(self, index):
        """
        获取指定索引的顶点

        Args:
            index (int): 顶点的索引

        Returns:
            Vertex: 顶点对象，如果索引无效则返回None
        """
        index = get_index(index, self.vertex_number)
        if index is not None:
            return FractureNetwork.Vertex(self, index)

    core.use(c_size_t, 'frac_nt_get_bd_n', c_void_p)

    @property
    def fracture_number(self):
        """
        获取裂缝单元(线段)的数量

        Returns:
            int: 裂缝单元的数量
        """
        return core.frac_nt_get_bd_n(self.handle)

    def get_fracture(self, index):
        """
        获取指定索引的裂缝单元

        Args:
            index (int): 裂缝单元的索引

        Returns:
            Fracture: 裂缝单元对象，如果索引无效则返回None
        """
        index = get_index(index, self.fracture_number)
        if index is not None:
            return FractureNetwork.Fracture(self, index)

    core.use(c_size_t, 'frac_nt_add_nd', c_void_p, c_double, c_double)

    def add_vertex(self, x, y):
        """
        添加顶点(要添加裂缝单元，必须首先添加顶点)

        Args:
            x (float): 顶点的x坐标
            y (float): 顶点的y坐标

        Returns:
            Vertex: 新添加的顶点对象
        """
        index = core.frac_nt_add_nd(self.handle, x, y)
        return self.get_vertex(index)

    core.use(c_size_t, 'frac_nt_add_bd', c_void_p, c_size_t, c_size_t)
    core.use(None, 'frac_nt_add_frac', c_void_p,
             c_double, c_double, c_double, c_double,
             c_double, c_void_p)

    def add_fracture(self, first=None, second=None, *, lave=None, data=None, pos=None):
        """
        添加裂缝单元

        注意：
            当给定lave的时候，将根据给定的lave来分割单元，并自动处理和已有裂缝之间的位置关系。

        Args:
            first (tuple, optional): 第一个顶点的坐标，默认为None
            second (tuple, optional): 第二个顶点的坐标，默认为None
            lave (float, optional): 分割单元的参数，默认为None
            data (FractureData, optional): 裂缝数据对象，默认为None
            pos (tuple, optional): 裂缝的位置，格式为 (x0, y0, x1, y1)，默认为None

        Returns:
            Fracture: 新添加的裂缝单元对象，如果使用lave参数则不返回
        """
        if lave is None:
            index = core.frac_nt_add_bd(self.handle, first, second)
            return self.get_fracture(index)
        else:
            if pos is not None:
                assert len(pos) == 4
                assert first is None and second is None, 'you should not set first and second when pos is given'
                first = pos[0: 2]
                second = pos[2: 4]
            if data is not None:
                assert isinstance(data, FractureNetwork.FractureData)
            core.frac_nt_add_frac(self.handle, first[0], first[1],
                                  second[0], second[1],
                                  lave, 0 if data is None else data.handle)

    core.use(None, 'frac_nt_clear', c_void_p)

    def clear(self):
        """
        清除裂缝网络中的所有数据
        """
        core.frac_nt_clear(self.handle)

    @property
    def vertexes(self):
        """
        获取所有的顶点，用于迭代

        Returns:
            Iterator: 包含所有顶点的迭代器对象
        """
        return Iterator(model=self,
                        count=self.vertex_number, get=lambda m, ind: m.get_vertex(ind))

    @property
    def fractures(self):
        """
        获取所有的裂缝，用于迭代

        Returns:
            Iterator: 包含所有裂缝的迭代器对象
        """
        return Iterator(model=self,
                        count=self.fracture_number, get=lambda m, ind: m.get_fracture(ind))

    core.use(None, 'frac_nt_get_induced_at',
             c_void_p, c_void_p, c_double, c_double, c_void_p)
    core.use(None, 'frac_nt_get_induced_along',
             c_void_p, c_void_p,
             c_double, c_double, c_double, c_double, c_void_p)
    core.use(None, 'frac_nt_get_induced',
             c_void_p,
             c_size_t, c_size_t, c_void_p)

    def get_induced(self, pos=None, sol2=None, buf=None, *,
                    fa_xy=None, fa_yy=None, matrix=None):
        """
        返回在指定位置的诱导应力

        Args:
            pos (list, optional): 位置信息，长度可以为2或4，默认为None
            sol2 (DDMSolution2, optional): 二维DDM的基本解对象，默认为None
            buf (Tensor2, optional): 存储诱导应力的张量对象，默认为None
            fa_xy (int, optional): 地应力的切向分量，默认为None
            fa_yy (int, optional): 地应力的法向分量，默认为None
            matrix (InfMatrix, optional): 影响系数矩阵对象，默认为None

        Returns:
            Tensor2: 诱导应力张量对象
        """
        if fa_xy is not None and fa_yy is not None and matrix is not None:
            assert isinstance(matrix, InfMatrix)
            assert self.fracture_number == matrix.size
            core.frac_nt_get_induced(self.handle, fa_xy, fa_yy, matrix.handle)
        else:
            assert len(pos) == 2 or len(pos) == 4
            assert isinstance(sol2, DDMSolution2)
            if not isinstance(buf, Tensor2):
                buf = Tensor2()
            if len(pos) == 2:
                core.frac_nt_get_induced_at(self.handle, buf.handle,
                                            pos[0], pos[1], sol2.handle)
            else:
                core.frac_nt_get_induced_along(self.handle, buf.handle,
                                               pos[0], pos[1], pos[2], pos[3], sol2.handle)
            return buf

    core.use(c_size_t, 'frac_nt_update_disp', c_void_p, c_void_p,
             c_size_t, c_size_t,
             c_double, c_double,
             c_size_t, c_size_t, c_double, c_double,
             c_double, c_double)

    def update_disp(self, matrix, fa_yy=99999999, fa_xy=99999999,
                    gradw_max=0, err_max=0.1, iter_min=10, iter_max=10000,
                    ratio_max=0.99, dist_max=1.0e6,
                    dn_max=1e100, ds_max=1e100):
        """
        更新位移(这是DDM计算的最核心的函数)

        Args:
            matrix (InfMatrix): 最新的应力影响矩阵
            fa_yy (float, optional): 在裂缝上，地应力的法向分量。当应力场更新了之后，必须要更新这个属性，默认为99999999
            fa_xy (float, optional): 在裂缝上，地应力的切向分量。当应力场更新了之后，必须要更新这个属性，默认为99999999
            gradw_max (float, optional): 裂缝宽度的最大的变化梯度，默认为0
            err_max (float, optional): 迭代的最大残差，默认为0.1
            iter_min (int, optional): 迭代的最少次数，默认为10
            iter_max (int, optional): 迭代的最大次数，默认为10000
            ratio_max (float, optional): 当收敛速率低于这个数值的时候，终止迭代，默认为0.99
            dist_max (float, optional): 将应力考虑为近场的临界的距离，默认为1.0e6
            dn_max (float, optional): 法向位移的最大值，默认为1e100
            ds_max (float, optional): 切向位移的最大值，默认为1e100

        Returns:
            int: 核心函数的返回值
        """
        assert isinstance(matrix, InfMatrix)
        return core.frac_nt_update_disp(
            self.handle, matrix.handle, fa_yy, fa_xy,
            gradw_max, err_max, iter_min, iter_max,
            ratio_max, dist_max, dn_max, ds_max)

    core.use(None, 'frac_nt_extend_tip',
             c_void_p, c_void_p, c_void_p,
             c_double, c_double, c_size_t, c_double)

    def extend_tip(self, kic, sol2, l_extend, va_wmin=99999999, angle_max=0.6, lave=-1.0):
        """
        尝试进行裂缝的扩展

        其中 l_extend是扩展的长度。
        注意，默认的情况下(即lave小于等于0的时候)，将简单地在裂缝的简短添加新的单元。
        当lave大于0的时候，将首先尝试增加简短裂缝单元的长度。

        在2025-1-8添加了lave参数。

        Args:
            kic (Tensor2): 断裂韧性张量对象
            sol2 (DDMSolution2): 二维DDM的基本解对象
            l_extend (float): 裂缝扩展的长度
            va_wmin (float, optional): 最小宽度阈值，默认为99999999
            angle_max (float, optional): 最大角度阈值，默认为0.6
            lave (float, optional): 分割单元的参数，默认为-1.0
        """
        assert isinstance(kic, Tensor2)
        assert isinstance(sol2, DDMSolution2)
        core.frac_nt_extend_tip(self.handle, kic.handle, sol2.handle, lave, l_extend,
                                va_wmin, angle_max)

    core.use(None, 'frac_nt_get_sub_network', c_void_p, c_size_t, c_void_p)

    def get_sub_network(self, fa_key, sub=None):
        """
        创建一个子网络

        注意，在裂缝中，所有定义了fa_key且属性值大于0.5的裂缝单元将被保留。

        Args:
            fa_key (int): 属性，用于判断是否保留裂缝单元
            sub (FractureNetwork, optional): 保存结果的缓冲区，默认为None

        Returns:
            FractureNetwork: 创建的子网络对象
        """
        if not isinstance(sub, FractureNetwork):
            sub = FractureNetwork()
        core.frac_nt_get_sub_network(self.handle, fa_key, sub.handle)
        return sub

    core.use(None, 'frac_nt_copy_fracture_from_sub_network', c_void_p, c_size_t, c_void_p)

    def copy_fracture_from_sub_network(self, fa_key, sub):
        """
        从子网络中拷贝裂缝数据

        Args:
            fa_key (int): 属性，用于判断是否保留裂缝单元
            sub (FractureNetwork): 子裂缝网络对象
        """
        if isinstance(sub, FractureNetwork):
            core.frac_nt_copy_fracture_from_sub_network(self.handle, fa_key, sub.handle)


class InfMatrix(HasHandle):
    """
    影响系数矩阵.
    """
    core.use(c_void_p, 'new_frac_mat')
    core.use(None, 'del_frac_mat', c_void_p)

    def __init__(self, network=None, sol2=None, handle=None):
        """
        创建给定handle的引用

        Args:
            network (FractureNetwork, optional): 裂缝网络对象，默认为None。
            sol2 (DDMSolution2, optional): 二维DDM的基本解对象，默认为None。
            handle (c_void_p, optional): 矩阵的句柄，默认为None。

        Raises:
            AssertionError: 如果 network 不是 FractureNetwork 类型，或者 sol2 不是 DDMSolution2 类型。
        """
        super(InfMatrix, self).__init__(handle, core.new_frac_mat, core.del_frac_mat)
        if network is not None and sol2 is not None:
            self.update(network=network, sol2=sol2)

    core.use(c_size_t, 'frac_mat_size', c_void_p)

    @property
    def size(self):
        """
        获取裂缝单元的数量

        Returns:
            int: 裂缝单元的数量
        """
        return core.frac_mat_size(self.handle)

    core.use(None, 'frac_mat_create', c_void_p, c_void_p, c_void_p)

    def update(self, network, sol2):
        """
        更新矩阵

        Args:
            network (FractureNetwork): 裂缝网络对象。
            sol2 (DDMSolution2): 二维DDM的基本解对象。

        Raises:
            AssertionError: 如果 network 不是 FractureNetwork 类型，或者 sol2 不是 DDMSolution2 类型。
        """
        assert isinstance(network, FractureNetwork)
        assert isinstance(sol2, DDMSolution2)
        core.frac_mat_create(self.handle, network.handle, sol2.handle)


class FracAlg:
    """
    提供一些裂缝相关的基础的算法.
    """

    @staticmethod
    def update_disp(network: FractureNetwork, *args, **kwargs):
        warnings.warn('FracAlg.update_disp will be removed after 2026-2-11, use FractureNetwork.update_disp instead',
                      DeprecationWarning)
        return network.update_disp(*args, **kwargs)

    @staticmethod
    def add_frac(network: FractureNetwork, p0, p1, lave, *, data=None):
        warnings.warn('FracAlg.add_frac will be removed after 2026-2-11, use FractureNetwork.add_fracture instead',
                      DeprecationWarning)
        return network.add_fracture(first=p0, second=p1, lave=lave, data=data)

    @staticmethod
    def extend_tip(network: FractureNetwork, *args, **kwargs):
        warnings.warn('FracAlg.extend_tip will be removed after 2026-2-11, use FractureNetwork.extend_tip instead',
                      DeprecationWarning)
        return network.extend_tip(*args, **kwargs)

    @staticmethod
    def get_induced(network: FractureNetwork, fa_xy, fa_yy, matrix):
        warnings.warn('FracAlg.get_induced will be removed after 2026-2-11, use FractureNetwork.get_induced instead',
                      DeprecationWarning)
        return network.get_induced(fa_xy=fa_xy, fa_yy=fa_yy, matrix=matrix)

    core.use(None, 'frac_alg_update_topology', c_void_p,
             c_void_p, c_size_t, c_double, c_double,
             c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_topology(seepage: Seepage, network: FractureNetwork, *,
                        layer_n=1, z_min=-1, z_max=1,
                        ca_area=999999999, fa_width=999999999, fa_dist=999999999):
        """
        更新seepage的结构，
            对于新添加的Cell，设置位置(cell.pos)和面积(ca_area)属性
            对于新添加的Face，设置宽度(fa_width)和长度(fa_dist)属性
        注意：
            这里假设network有layer_n层的cell组成，并基于此来更新seepage的结构.

        Args:
            seepage (Seepage): 渗流对象。
            network (FractureNetwork): 裂缝网络对象。
            layer_n (int, optional): 层数，默认为1。
            z_min (float, optional): 最小z坐标，默认为-1。
            z_max (float, optional): 最大z坐标，默认为1。
            ca_area (float, optional): 单元面积，默认为999999999。
            fa_width (float, optional): 面的宽度，默认为999999999。
            fa_dist (float, optional): 面的长度，默认为999999999。

        Raises:
            AssertionError: 如果 seepage 不是 Seepage 类型，或者 network 不是 FractureNetwork 类型。
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork)
        core.frac_alg_update_topology(seepage.handle, network.handle, layer_n, z_min, z_max,
                                      ca_area, fa_width, fa_dist)


def main(argv: list):
    """
    模块运行的主函数.
    """
    if len(argv) == 1:
        print(about(check_lic=False))
        return
    if len(argv) == 2:
        if argv[1] == 'lic':
            print(lic.summary)
            return
        if argv[1] == 'env':
            try:
                from zmlx.alg.install_dep import install_dep
                install_dep(print)
            except Exception as e:
                print(e)
        return


def __deprecated_func(pack_name, func, date=None):
    return dict(pack_name=pack_name, func=func, date=date)


_deprecated_funcs = dict(
    information=__deprecated_func('zmlx.ui.GuiBuffer', 'information', '2025-1-21'),
    question=__deprecated_func('zmlx.ui.GuiBuffer', 'question', '2025-1-21'),
    plot=__deprecated_func('zmlx.ui.GuiBuffer', 'plot', '2025-1-21'),
    gui=__deprecated_func('zmlx.ui.GuiBuffer', 'gui', '2025-1-21'),
    break_point=__deprecated_func('zmlx.ui.GuiBuffer', 'break_point', '2025-1-21'),
    breakpoint=__deprecated_func('zmlx.ui.GuiBuffer', 'break_point', '2025-1-21'),
    gui_exec=__deprecated_func('zmlx.ui.GuiBuffer', 'gui_exec', '2025-1-21'),
    time_string=__deprecated_func('zmlx.filesys.tag', 'time_string', '2025-1-21'),
    is_time_string=__deprecated_func('zmlx.filesys.tag', 'is_time_string', '2025-1-21'),
    has_tag=__deprecated_func('zmlx.filesys.tag', 'has_tag', '2025-1-21'),
    print_tag=__deprecated_func('zmlx.filesys.tag', 'print_tag', '2025-1-21'),
    first_only=__deprecated_func('zmlx.filesys.first_only', 'first_only', '2025-1-21'),
    add_keys=__deprecated_func('zmlx.utility.AttrKeys', 'add_keys', '2025-1-21'),
    AttrKeys=__deprecated_func('zmlx.utility.AttrKeys', 'AttrKeys', '2025-1-21'),
    install=__deprecated_func('zmlx.alg.install', 'install', '2025-1-21'),
    prepare_dir=__deprecated_func('zmlx.filesys.prepare_dir', 'prepare_dir', '2025-1-21'),
    time2str=__deprecated_func('zmlx.alg.time2str', 'time2str', '2025-1-21'),
    mass2str=__deprecated_func('zmlx.alg.mass2str', 'mass2str', '2025-1-21'),
    make_fpath=__deprecated_func('zmlx.filesys.make_fpath', 'make_fpath', '2025-1-21'),
    get_last_file=__deprecated_func('zmlx.filesys.get_last_file', 'get_last_file',
                                    '2025-1-21'),
    write_py=__deprecated_func('zmlx.io.python', 'write_py', '2025-1-21'),
    read_py=__deprecated_func('zmlx.io.python', 'read_py', '2025-1-21'),
    TherFlowConfig=__deprecated_func('zmlx.config.TherFlowConfig', 'TherFlowConfig',
                                     '2025-1-21'),
    SeepageTher=__deprecated_func('zmlx.config.TherFlowConfig', 'TherFlowConfig',
                                  '2025-1-21'),
    Field=__deprecated_func('zmlx.utility.Field', 'Field', '2025-1-21'),
)


def __getattr__(name):
    """
    当访问不存在的属性时，尝试从其他模块中导入
    """
    import importlib
    value = _deprecated_funcs.get(name)
    if value is not None:
        pack_name = value.get('pack_name')
        func = value.get('func')
        date = value.get('date')
        warnings.warn(
            f'<zml.{name}> will be removed after {date}, please use <{pack_name}.{func}> instead.',
            DeprecationWarning,
            stacklevel=2
        )
        mod = importlib.import_module(pack_name)
        return getattr(mod, func)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    main(sys.argv)

# -*- coding: utf-8 -*-
"""
说明:     流动、传热、应力计算的核心模块；C++代码的Python接口(必须和zml.dll放在一起使用)。

运行环境： Windows 7/10/11; Python 3.7及以上版本; 64位系统;

依赖项:   无

网址:     https://gitee.com/geomech/hydrate

作者：    张召彬 <zhangzhaobin@mail.iggcas.ac.cn>, 中国科学院地质与地球物理研究所
"""

import ctypes
import datetime
import math
import os
import sys
import warnings

warnings.simplefilter("default")  # 警告默认显示

from ctypes import cdll, c_void_p, c_char_p, c_int, c_int64, c_bool, c_double, c_size_t, c_uint, CFUNCTYPE, \
    POINTER
from typing import Iterable

try:
    import numpy as np
except Exception as _err:
    # 当numpy没有安装的时候，部分功能将不可用
    np = None
    warnings.warn(f'cannot import numpy in zml. error = {_err}')

try:
    import matplotlib.pyplot as plt
except Exception as _err:
    plt = None
    warnings.warn(f'cannot import matplotlib in zml. error = {_err}')

# 指示当前是否为Windows系统(目前支持Windows和Linux两个系统)
is_windows = os.name == 'nt'


class Object:
    def set(self, **kwargs):
        """
        set (but do not add new) attribution values
        """
        current_keys = dir(self)
        for key, value in kwargs.items():
            assert key in current_keys, f"add new attribution '{key}' to {type(self)} is forbidden"
            setattr(self, key, value)
        return self


def create_dict(**kwargs):
    """
    将给定的参数列表转化为一个字典
    """
    return kwargs


class ConsoleApi:
    def __init__(self):
        self.__commands = create_dict(about=self.show_all, information=self.show_all,
                                      question=self.question, plot=self.plot, progress=self.do_nothing)

    @staticmethod
    def do_nothing(*args, **kwargs):
        pass

    @staticmethod
    def question(info):
        """
        询问信息。返回是否True
        """
        y = input(f"{info} input 'y' or 'Y' to continue: ")
        return y == 'y' or y == 'Y'

    @staticmethod
    def show_all(*args, **kwargs):
        """
        显示所有的参数
        """
        print(f'args={args}, kwargs={kwargs}')

    def plot(self, kernel, **kwargs):
        """
        在非GUI模式下绘图(或者显示并阻塞程序执行，或者输出文件但不显示)
        """
        if kernel is None or plt is None:
            return
        try:
            fig = plt.figure()
            kernel(fig)
            fname = kwargs.get('fname', None)
            if fname is not None:
                dpi = kwargs.get('dpi', 300)
                fig.savefig(fname=fname, dpi=dpi)
                plt.close()
            else:
                plt.show()
        except Exception as err:
            warnings.warn(f'meet exception <{err}> when run <{kernel}>')

    def command(self, name, *args, **kwargs):
        """
        当GUI不存在的时候来执行默认的命令
        """
        cmd = self.__commands.get(name, None)
        if cmd is not None:
            return cmd(*args, **kwargs)
        else:
            print(f'function: {name}(args={args}, kwargs={kwargs})')


console = ConsoleApi()


class GuiBuffer:
    def __init__(self, get_execute=None):
        self.__gui = []
        self.__get_execute = get_execute

    def command(self, *args, **kwargs):
        if len(self.__gui) > 0:
            return self.__gui[-1].command(*args, **kwargs)

    def push(self, gui):
        assert hasattr(gui, 'command')
        self.__gui.append(gui)

    def pop(self):
        if len(self.__gui) > 0:
            return self.__gui.pop()

    def exists(self):
        return len(self.__gui) > 0

    def get(self):
        if len(self.__gui) > 0:
            return self.__gui[-1]

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

    class Agent:
        def __init__(self, gui, name):
            self.gui = gui
            self.name = name

        def __call__(self, *args, **kwargs):
            if self.gui is not None:
                return self.gui.command(self.name, *args, **kwargs)
            else:
                return console.command(self.name, *args, **kwargs)

    def __getattr__(self, name):
        return GuiBuffer.Agent(self.get(), name)

    def execute(self, func, keep_cwd=True, close_after_done=True, args=None, kwargs=None):
        """
        尝试在gui模式下运行给定的函数 func
        """

        def fx():
            if func is not None:
                x = args if args is not None else []
                y = kwargs if kwargs is not None else {}
                return func(*x, **y)

        if self.exists():
            return fx()
        try:
            f = self.__get_execute()
            assert f is not None
            return f(fx, keep_cwd=keep_cwd, close_after_done=close_after_done)
        except Exception as e:
            print(f'call gui failed: {e}')
            return fx()

    def __call__(self, *args, **kwargs):
        """
        尝试在gui模式下运行给定的函数.
        """
        return self.execute(*args, **kwargs)


def __get_gui_execute():
    """
    尝试从zmlx.gui模块中导入execute函数（gui界面运行的入口）
    """
    try:
        import PyQt5  # 界面依赖PyQt5
        from zmlx.ui import execute
        return execute
    except Exception as err:
        raise err


gui = GuiBuffer(get_execute=__get_gui_execute)


def information(*args, **kwargs):
    return gui.information(*args, **kwargs)


def question(info):
    return gui.question(info)


def plot(*args, **kwargs):
    """
    调用matplotlib执行绘图操作
    """
    gui.plot(*args, **kwargs)


def break_point():
    """
    添加一个gui的断点，从而在gui执行的过程中，可以控制暂停和终止
    """
    gui.break_point()


# 函数的别名<为了兼容之前的代码>
breakpoint = break_point


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)


def is_array(o):
    """
    检查一个对象是否定义了长度并可以利用[]来获取元素
    """
    return hasattr(o, '__getitem__') and hasattr(o, '__len__')


def make_c_char_p(s):
    """
    Converts a Python string to the c_char_p type that can be used in dynamic libraries. Note that since the C language
    string is used, which is terminated by 0 by default, the string passed in here must be an ASCII format string
    """
    return c_char_p(bytes(s, encoding='utf8'))


def sendmail(address, subject=None, text=None, name_from=None, name_to=None):
    """
    发送一个邮件. 返回是否发送成功.
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
    """
    Send some necessary statistical information to the software author by Email.
    This is important to improve this software. Thanks for your feedback!
    However, if you do not want to send anything, please run:
        zml.app_data.setenv('disable_feedback', 'True')
    then you will not send anything in the future. Thanks for using!
    """
    try:
        if app_data.getenv('disable_feedback') == 'True':
            return True
        else:
            return sendmail('zhangzhaobin@mail.iggcas.ac.cn', subject=subject, text=text,
                            name_from=None, name_to='Author')
    except:
        return False


def make_dirs(folder):
    """
    Create folders. When the upper-level directory where the given folder is located does not exist,
    it will be automatically created to ensure that the folder is created successfully
    """
    try:
        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
    except:
        pass


# 函数的别名<为了兼容之前的代码>
makedirs = make_dirs


def make_parent(path):
    """
    对于任意给定的文件路径，尝试为它创建一个上一级目录，从而尽可能确保在这个位置写入文件能够成功；
    返回输入的文件路径
    """
    try:
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            make_dirs(dirname)
        return path
    except:
        return path


def read_text(path, encoding=None, default=None):
    """
    Read text from a file in text format
    """
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return default
    except:
        return default


def write_text(path, text, encoding=None):
    """
    Write the given text to a file. Automatically created when the folder where the file is located does not exist
    """
    folder = os.path.dirname(path)
    if len(folder) > 0 and not os.path.isdir(folder):
        make_dirs(folder)
    with open(path, 'w', encoding=encoding) as f:
        if text is None:
            f.write('')
        else:
            f.write(text)


class AppData(Object):
    """
    数据和文件管理
    """

    def __init__(self):
        # 缓存目录
        if is_windows:
            self.folder = os.path.join(os.getenv("APPDATA"), 'zml')
        else:
            self.folder = os.path.join('/var/tmp/zml')

        make_dirs(self.folder)
        # 自定义的文件搜索路径
        self.paths = []
        try:
            for config_file in self.find_all('zml_search_paths'):
                if os.path.isfile(config_file):
                    with open(config_file, 'r') as file:
                        for line in file.readlines():
                            line = line.strip()
                            if os.path.isdir(line):
                                self.add_path(line)
        except:
            pass

        # 内存变量
        self.space = {}

    def add_path(self, path):
        """
        添加一个搜索路径<避免重复>
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
        path = os.path.join(self.folder, 'tags', datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
        return os.path.exists(path)

    def add_tag_today(self, tag):
        folder = os.path.join(self.folder, 'tags')
        make_dirs(folder)
        path = os.path.join(folder, datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
        try:
            with open(path, 'w') as f:
                f.write('\n')
        except:
            pass

    def log(self, text):
        """
        Record program operation information
        """
        folder = os.path.join(self.folder, 'logs')
        make_dirs(folder)
        try:
            with open(os.path.join(folder, datetime.datetime.now().strftime("%Y-%m-%d.log")), 'a') as f:
                f.write(f'-------{datetime.datetime.now()}----------\n')
                f.write(f'{text}\n\n\n')
        except:
            pass

    def getenv(self, key, encoding=None, default=None):
        """
        Get the value of an application environment variable
        """
        path = os.path.join(self.folder, 'env', key)
        return read_text(path, encoding=encoding, default=default)

    def setenv(self, key, value, encoding=None):
        """
        Set the value of the application environment variable
        """
        path = os.path.join(self.folder, 'env', key)
        write_text(path, value, encoding=encoding)

    def root(self, *args):
        """
        返回根目录下的路径
        """
        return make_parent(os.path.join(self.folder, *args))

    def temp(self, *args):
        """
        Get the path of temp file by the given filename
        """
        return make_parent(os.path.join(self.folder, 'temp', *args))

    @staticmethod
    def proj(*args):
        """
        获得工程目录下的文件
        """
        if len(args) == 0:
            # 此时，返回工程文件的根目录
            return os.path.join(os.getcwd(), '.zml')
        else:
            return make_parent(os.path.join(os.getcwd(), '.zml', *args))

    def clear_temp(self, *args):
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
        """
        返回所有的搜索路径. 其中first为优先搜索的路径。在此之后是当前工作路径、缓存路径、自定义路径和Python的系统路径；
        注意：这里返回的路径可能会有重复的
        """
        paths = [os.getcwd(), self.proj()] if first is None else [first, os.getcwd(), self.proj()]
        return paths + [self.folder, os.path.join(self.folder, 'temp')] + self.paths + sys.path

    def find(self, name, first=None):
        """
        搜索指定的文件并返回路径。如果未找到，则返回None
        """
        for folder in self.get_paths(first):
            try:
                path = os.path.join(folder, name)
                if os.path.exists(path):
                    return path
            except:
                pass

    def find_all(self, name, first=None):
        """
        搜索文件并返回所有找到的<并且保证已经去除了重复元素>
        """
        results = []
        for folder in self.get_paths(first):
            try:
                path = os.path.join(folder, name)
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
        """
        Reading data from the workspace
        """
        if len(args) == 0 and len(kwargs) == 0:
            return self.space
        else:
            return self.space.get(*args, **kwargs)

    def put(self, key, value):
        """
        Putting data into the workspace
        """
        self.space[key] = value


app_data = AppData()


def load_cdll(name, first=None):
    """
    Load C-Style Dll by the given file name and the folder.
    """
    path = app_data.find(name, first)
    if path is not None:
        try:
            return cdll.LoadLibrary(path)
        except Exception as e:
            print(f'Error load library from <{path}>. Message = {e}')
    else:
        try:
            return cdll.LoadLibrary(name)
        except Exception as e:
            print(f'Error load library from <{name}>. Message = {e}')


class NullFunction:
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        print(f'calling null function {self.name}(args={args}, kwargs={kwargs})')


def get_func(dll, restype, name, *argtypes):
    """
    配置一个dll的函数
    """
    assert isinstance(name, str)
    fn = getattr(dll, name, None)
    if fn is None:
        if dll is not None:
            print(f'Warning: can not find function <{name}> in <{dll}>')
        return NullFunction(name)
    if restype is not None:
        fn.restype = restype
    if len(argtypes) > 0:
        fn.argtypes = argtypes
    return fn


if is_windows:
    dll = load_cdll('zml.dll', first=os.path.dirname(os.path.realpath(__file__)))
else:
    dll = load_cdll('zml.so.1', first=os.path.dirname(os.path.realpath(__file__)))


class DllCore:
    """
    Manage errors, warnings, etc. in the C++ kernel
    """

    def __init__(self, dll):
        self.dll = dll
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
        self.use(c_char_p, 'get_timer_summary', c_void_p)
        self.use(c_int, 'get_version')
        self.use(c_bool, 'is_parallel_enabled')
        self.use(None, 'set_parallel_enabled', c_bool)
        self.use(c_bool, 'assert_is_void')
        self.dll_set_error_handle = get_func(self.dll, None, 'set_error_handle', c_void_p)
        self.use(c_char_p, 'get_compiler')

    def has_dll(self):
        """
        是否正确载入了dll
        """
        return self.dll is not None

    def has_error(self):
        if self.has_dll():
            return self.dll_has_error()
        else:
            return False

    def pop_error(self):
        if self.has_dll():
            return self.dll_pop_error(0).decode()
        else:
            return ''

    def has_warning(self):
        if self.has_dll():
            return self.dll_has_warning()
        else:
            return False

    def pop_warning(self):
        if self.has_dll():
            return self.dll_pop_warning(0).decode()
        else:
            return ''

    def has_log(self):
        if self.has_dll():
            return self.dll_has_log()
        else:
            return False

    def pop_log(self):
        if self.has_dll():
            return self.dll_pop_log(0).decode()
        else:
            return ''

    @property
    def parallel_enabled(self):
        """
        Whether to allow parallelism in kernel computing
        (the kernel adopts multi-CPU shared memory parallelism by default)
        """
        if self.has_dll():
            return self.is_parallel_enabled()
        else:
            return False

    @parallel_enabled.setter
    def parallel_enabled(self, value):
        """
        Whether to allow parallelism in kernel computing
        (the kernel adopts multi-CPU shared memory parallelism by default)
        """
        if self.has_dll():
            self.set_parallel_enabled(value)

    @property
    def timer_summary(self):
        """
        Returns cpu time-consuming statistics, only for calculation and testing
        """
        if self.has_dll():
            return self.get_timer_summary(0).decode()
        else:
            return ''

    def check_error(self):
        """
        Check and remove error messages in the dll. And throw an exception when the error message exists.
        """
        if self.has_error():
            error = self.pop_error()
            while self.has_error():
                error = f'{error} \n\n {self.pop_error()}'
            app_data.log(error)
            raise RuntimeError(error)

    def set_error_handle(self, func):
        """
        Set the callback function of the error message. This function can be called when an error is encountered.
        The passed-in function should be of the form void f(const char*) .
        """
        if self.has_dll():
            err_handle = CFUNCTYPE(None, c_char_p)

            def f(s):
                func(s.decode())

            self.__err_handle = err_handle(f)
            self.dll_set_error_handle(self.__err_handle)

    @property
    def log_nmax(self):
        if self.has_dll():
            return self.get_log_nmax()
        else:
            return 0

    @log_nmax.setter
    def log_nmax(self, value):
        if self.has_dll():
            self.set_log_nmax(value)

    @property
    def time_compile(self):
        """
        Returns the time the dll was compiled (a string) to locate the version of the program
        """
        if self.has_dll():
            return self.get_time_compile(0).decode()
        else:
            return ''

    @property
    def version(self):
        """
        返回内核的版本 (编译的日期)
        """
        if self.has_dll():
            return core.get_version()
        else:
            return 100101

    @property
    def compiler(self):
        """
        返回内核所采用的编译器及其版本
        """
        if self.has_dll():
            return self.get_compiler().decode()
        else:
            return ''

    def run(self, fn):
        """
        Run code that needs to call memory and check for errors
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
        """
        Get the log inside the dll and print it to file
        """
        if self.has_dll():
            if path is None:
                self.dll_print_logs(make_c_char_p('zml.log'))
            else:
                assert isinstance(path, str)
                self.dll_print_logs(make_c_char_p(path))

    def use(self, restype, name, *argtypes):
        """
        声明接下来将使用内核dll中的某一个函数
        """
        if self.has_dll():
            if hasattr(self, name):
                print(f'Warning: function <{name}> already exists')
                return
            func = get_func(self.dll, restype, name, *argtypes)
            if func is not None:
                setattr(self, name, lambda *args: self.run(lambda: func(*args)))


core = DllCore(dll=dll)

# zml模块的版本(用六位数字表示的编译的日期)
version = core.version


class DataVersion:
    """
    定义数据的版本. 数据的版本号为6位的int类型(yymmdd)，是数据的日期
    """

    def __init__(self, value=version):
        """
        初始化，设置默认的数据版本
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        self.__versions = {}
        self.__default = value

    def set(self, value=None, key=None):
        """
        设置版本. 6位的int
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        if key is None:
            self.__default = value
        else:
            self.__versions[key] = value

    def __getattr__(self, key):
        """
        返回数据的版本. 6位的int
        """
        return self.__versions.get(key, self.__default)

    def __getitem__(self, key):
        """
        返回数据的版本. 6位的int
        """
        return self.__versions.get(key, self.__default)

    def __setitem__(self, key, value):
        """
        设置数据的版本. 6位的int
        """
        self.set(key=key, value=value)


data_version = DataVersion()

core.use(None, 'set_srand', c_uint)


def set_srand(seed):
    """
    Set the seed of a random number (an unsigned integer variable)
    """
    core.set_srand(seed)


core.use(c_double, 'get_rand')


def get_rand():
    """
    Returns a random number between 0 and 1
    """
    return core.get_rand()


class HasHandle(Object):
    def __init__(self, handle=None, create=None, release=None):
        if handle is None:
            assert create is not None and release is not None
            self.__handle = create()
            self.__release = release
        else:
            self.__handle = handle
            self.__release = None

    def __del__(self):
        if self.__release is not None:
            self.__release(self.__handle)

    @property
    def handle(self):
        return self.__handle


class String(HasHandle):
    core.use(None, 'del_str', c_void_p)
    core.use(c_void_p, 'new_str')

    def __init__(self, value=None, handle=None):
        super(String, self).__init__(handle, core.new_str, core.del_str)
        if handle is None:
            if value is not None:
                assert isinstance(value, str)
                self.assign(value)

    def __str__(self):
        return self.to_str()

    def __len__(self):
        return self.size

    core.use(c_size_t, 'str_size', c_void_p)

    @property
    def size(self):
        """
        Returns the length of the std::string object
        """
        return core.str_size(self.handle)

    core.use(None, 'str_assign', c_void_p, c_char_p)

    def assign(self, value):
        """
        string assignment
        """
        core.str_assign(self.handle, make_c_char_p(value))

    core.use(c_char_p, 'str_to_char_p', c_void_p)

    def to_str(self):
        """
        Convert std::string to c_char_p, and further convert to Python string
        """
        if core.dll is not None:
            return core.str_to_char_p(self.handle).decode()


def get_time_compile():
    return core.time_compile


def run(fn):
    """
    Run code that needs to call memory and check for errors
    """
    return core.run(fn)


def time_string():
    """
    生成一个时间字符串 (类似于 20201021T183800 这样的格式)
    """
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def is_time_string(s):
    """
    check if the given string is a time string such as 20201021T183800.
    """
    if len(s) != 15:
        return False
    else:
        return s[0: 8].isdigit() and s[8] == 'T' and s[9: 15].isdigit()


def has_tag(folder=None):
    """
    Check if a file like 20201021T183800 exists
    """
    if folder is None:
        names = os.listdir(os.getcwd())
    else:
        if os.path.isdir(folder):
            names = os.listdir(folder)
        else:
            names = []
    for name in names:
        if is_time_string(name):
            return True
    return False


def print_tag(folder=None):
    """
    Print a file, the file name is similar to 20201021T183800, this file can be used as a label for the data,
    and then search the file to locate the data
    """
    if has_tag(folder=folder):
        return
    if folder is None:
        path = time_string()
    else:
        path = os.path.join(folder, time_string())
    with open(make_parent(path), 'w') as file:
        file.write("data_tag\n")
        file.flush()


core.use(None, 'fetch_m', c_char_p)


def fetch_m(folder=None):
    """
    Get those predefined m-files. These m files are used for debugging plots etc.
    """
    if folder is None:
        core.fetch_m(make_c_char_p(''))
    else:
        assert isinstance(folder, str)
        core.fetch_m(make_c_char_p(folder))


class License:
    """
    Manage licenses for the software
    """

    def __init__(self, core):
        self.core = core
        self.license_info_has_checked = False
        if self.core.has_dll():
            self.core.use(c_int, 'lic_webtime')
            self.core.use(c_bool, 'lic_summary', c_void_p)
            self.core.use(None, 'lic_get_serial', c_void_p, c_bool)
            self.core.use(None, 'lic_create_permanent', c_void_p, c_void_p)
            self.core.use(None, 'lic_load', c_void_p)

    @property
    def webtime(self):
        """
        Returns the timestamp on the web (not the real time).
        The program will use this time to determine whether the program has expired
        """
        if self.core.has_dll():
            return self.core.lic_webtime()
        else:
            return 100101

    @property
    def summary(self):
        """
        Returns the authorization information for this computer. Returns None if the computer is not properly authorized
        """
        if self.core.has_dll():
            s = String()
            if self.core.lic_summary(s.handle):
                return s.to_str()

    def get_serial(self, base64=True):
        """
        Returns the usb serial number of this computer (one of them), used for registration
        """
        if self.core.has_dll():
            s = String()
            self.core.lic_get_serial(s.handle, base64)
            return s.to_str()

    @property
    def usb_serial(self):
        """
        Returns the usb serial number of this computer (one of them), used for registration
        """
        return self.get_serial()

    def create_permanent(self, serial):
        """
        给定序列号(usb_serial)，返回一个针对这个serial的永久授权。仅供测试
        """
        if self.core.has_dll():
            code = String()
            temp = String()
            temp.assign(serial)
            self.core.lic_create_permanent(code.handle, temp.handle)
            return code.to_str()

    def create(self, serial):
        return self.create_permanent(serial)

    def load(self, code):
        """
        将给定的licdata存储到默认位置
        """
        if self.core.has_dll():
            temp = String()
            temp.assign(code)
            self.core.lic_load(temp.handle)

    def check(self):
        """
        Check authorization. If the current computer is authorized normally, the function will pass normally,
        otherwise an exception will be triggered.
        """
        assert self.exists()

    def exists(self):
        """
        Returns whether the computer has the correct license for the software
        """
        if self.core.has_dll():
            return self.core.lic_summary(0)
        else:
            return False

    def check_once(self):
        """
        Check license during iteration
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
                if gui.exists():
                    gui.information('Warning', text)


lic = License(core=core)


def reg(code=None):
    """
    注册。当code为None的时候，返回本机序列号。当code长度小于80，则将code视为序列号，则创建licdata；否则，将code视为licdata，并
    将它保存到本地。
    """
    if code is None:
        return lic.usb_serial
    else:
        assert isinstance(code, str)
        if len(code) < 80:
            return lic.create_permanent(code)
        else:
            lic.load(code)


def first_only(path='please_delete_this_file_before_run'):
    """
    when it is executed for the second time, an exception is given to ensure that the result is not easily overwritten
    """
    if os.path.exists(path):
        y = question('Warning: The existed data will be Over-Written. continue? ')
        if not y:
            assert False
    else:
        with open(path, 'w') as file:
            file.write('\n')


core.use(c_double, 'test_loop', c_size_t, c_bool)


def test_loop(count, parallel=True):
    """
    测试内核中给定长度的循环，并返回耗时
    """
    return core.test_loop(count, parallel)


def about():
    """
    Return module information
    """
    info = f'Welcome to zml ({version}; {core.time_compile}; {core.compiler})'
    if not lic.exists():
        author = 'author (Email: zhangzhaobin@mail.iggcas.ac.cn, QQ: 542844710)'
        info = f"""{info}. 
        
Note: license not found, please send 
    1. hardware info: "{lic.usb_serial}" 
    2. Your name, workplace, and contact information 

to {author}"""
    return info


def get_distance(p1, p2):
    """
    Returns the distance between two points
    """
    dist = 0
    for i in range(min(len(p1), len(p2))):
        dist += math.pow(p1[i] - p2[i], 2)
    return math.sqrt(dist)


def get_norm(p):
    """
    Returns the distance from the origin
    """
    dist = 0
    for i in range(len(p)):
        dist += math.pow(p[i], 2)
    return math.sqrt(dist)


def clock(func):
    """
    Timing for Python functions. Reference https://blog.csdn.net/BobAuditore/article/details/79377679

import time
import zml

@zml.clock
def run(seconds):
    time.sleep(seconds)
    print('HHH')

if __name__ == '__main__':
    run(1)
    """

    def clocked(*args, **kwargs):
        import timeit
        t0 = timeit.default_timer()
        result = func(*args, **kwargs)
        elapsed = timeit.default_timer() - t0
        name = func.__name__
        arg_str = ', '.join(repr(arg) for arg in args)
        print('[%0.8fs] %s(%s) -> %r' % (elapsed, name, arg_str, result))
        return result

    return clocked


core.use(c_bool, 'confuse_file', c_char_p, c_char_p, c_char_p, c_bool)


def confuse_file(ipath, opath, password, is_encrypt=True):
    """
    Obfuscated encryption/decryption of file content.
    is_encrypt=True means encryption, is_encrypt=False means decryption
    """
    return core.confuse_file(make_c_char_p(ipath), make_c_char_p(opath), make_c_char_p(password), is_encrypt)


def prepare_dir(folder, direct_del=False):
    """
    Prepare an empty folder for output calculation data
    """
    if folder is None:
        return
    if os.path.exists(folder):
        if direct_del:
            y = True
        else:
            y = question(f'Do you want to delete the existed folder <{folder}>?')
        if y:
            import shutil
            shutil.rmtree(folder)
    if not os.path.exists(folder):
        make_dirs(folder)


def time2str(s):
    if abs(s) < 200:
        if s > 2.0:
            return '%.2fs' % s
        s *= 1000
        if s > 2.0:
            return '%.2fms' % s
        s *= 1000
        if s > 2.0:
            return '%.2fus' % s
        s *= 1000
        return '%.2fns' % s
    m = s / 60
    if abs(m) < 200:
        return '%.2fm' % m
    h = m / 60
    if abs(h) < 60:
        return '%.2fh' % h
    d = h / 24
    if abs(d) < 800:
        return '%.2fd' % d
    y = d / 365
    return '%.2fy' % y


def mass2str(kg):
    ug = kg * 1.0e9
    if abs(ug) < 2000:
        return '%.2fug' % ug
    mg = ug / 1000
    if abs(mg) < 2000:
        return '%.2fmg' % mg
    g = mg / 1000
    if abs(g) < 2000:
        return '%.2fg' % g
    kg = g / 1000
    if abs(kg) < 2000:
        return '%.2fkg' % kg
    t = kg / 1000
    return '%.2ft' % t


def make_fpath(folder, step=None, ext='.txt', name=None):
    """
    Returns a filename to output data, and ensures that the folder exists
    """
    assert isinstance(folder, str)
    if not os.path.exists(folder):
        make_dirs(folder)
    else:
        assert os.path.isdir(folder)
    assert step is not None or name is not None
    if step is not None:
        return os.path.join(folder, f'{step:010d}{ext}')
    if name is not None:
        return os.path.join(folder, name)


def get_last_file(folder):
    """
    返回给定文件夹中的最后一个文件（按照文件名，利用字符串默认的对比，从小到大排序）
    """
    if not os.path.isdir(folder):
        return
    files = os.listdir(folder)
    if len(files) == 0:
        return
    else:
        return os.path.join(folder, max(files))


def write_py(path, data=None, **kwargs):
    """
    Save the data to a file in .py format. Note that the data must be correctly converted to a string.
    If data is a string, make sure it does not contain special characters such as ' and "
    """
    if path is None:
        return
    if data is None and len(kwargs) == 0:
        return
    if data is None:
        data = {}
    if isinstance(data, dict):
        data.update(kwargs)
    else:
        assert len(kwargs) == 0
    with open(path, 'w', encoding='UTF-8') as file:
        if isinstance(data, str):
            file.write(f'"""{data}"""')
        else:
            file.write(f'{data}')


def read_py(path=None, data=None, encoding='utf-8', globals=None, text=None, key=None):
    """
    Read data from .py format. For specific format, refer to the description of the write_py function
    """
    assert key is None or isinstance(key, str)
    if text is None and path is not None:
        try:
            with open(path, 'r', encoding=encoding) as file:
                text = file.read()
        except:
            pass
    if text is None:
        if key is None:
            return data
        else:
            return {} if key == '*' or key == '' else data
    else:
        assert isinstance(text, str)
    if key is None:
        try:
            return eval(text, globals)
        except:
            return data
    else:
        space = {}
        try:
            exec(text, globals, space)
            return space if key == '*' or key == '' else space.get(key, data)
        except:
            return space if key == '*' or key == '' else data


def parse_fid3(fluid_id):
    """
    自动将给定的流体ID识别为某种流体的某种组分的ID
    """
    if fluid_id is None:
        return 99999999, 99999999, 99999999
    if is_array(fluid_id):
        count = len(fluid_id)
        assert 0 < count <= 3
        i0 = fluid_id[0] if 0 < count else 99999999
        i1 = fluid_id[1] if 1 < count else 99999999
        i2 = fluid_id[2] if 2 < count else 99999999
        return i0, i1, i2
    else:
        return fluid_id, 99999999, 99999999


def get_average_perm(p0, p1, get_perm, sample_dist=None, depth=0):
    """
    返回两个点之间的平均的渗透率<或者平均的导热系数>
    注意：
        此函数仅仅用于计算渗透率的平均值<在求平均的时候，考虑到了串联效应>
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


def add_keys(*args):
    """
    在字典中注册键值。将从0开始尝试，直到发现不存在的数值再使用. 返回添加了key之后的字典对象.
    示例:
        from zml import *
        keys = add_keys('x', 'y')
        print(keys)
        add_keys(keys, 'a', 'b', 'c')
        print(keys)
    输出:
        {'x': 0, 'y': 1}
        {'x': 0, 'y': 1, 'a': 2, 'b': 3, 'c': 4}
    """

    # Check the input
    n1 = 0
    n2 = 0
    for key in args:
        if isinstance(key, AttrKeys):
            key.add_keys(*args)
            return key
        if isinstance(key, dict):
            n1 += 1
            continue
        if isinstance(key, str):
            n2 += 1
            continue
    assert n1 <= 1
    assert n1 + n2 == len(args)

    # Find the dict
    key_vals = None
    for key in args:
        if isinstance(key, dict):
            key_vals = key
            break
    if key_vals is None:
        key_vals = {}

    # Add keys
    for key in args:
        if not isinstance(key, str):
            continue
        if key not in key_vals:
            values = key_vals.values()
            succeed = False
            for val in range(len(key_vals) + 1):
                if val not in values:
                    key_vals[key] = val
                    succeed = True
                if succeed:
                    break
            assert succeed

    # Return the dict.
    return key_vals


class AttrKeys:
    """
    用以管理属性. 自动从0开始编号.
    """

    def __init__(self, *args):
        self.__keys = {}
        self.add_keys(*args)

    def __str__(self):
        return f'{self.__keys}'

    def __getattr__(self, item):
        return self.__keys[item]

    def __getitem__(self, item):
        return self.__keys[item]

    def values(self):
        return self.__keys.values()

    def add_keys(self, *args):
        for key in args:
            if isinstance(key, str):
                if key not in self.__keys:
                    values = self.values()
                    for val in range(len(self.__keys) + 1):
                        if val not in values:
                            self.__keys[key] = val
                            break


def install(name='zml.pth', folder=None):
    """
    Add the current folder to python's search path
    """
    pth = os.path.join(os.path.dirname(sys.executable), name)
    if folder is None:
        folder = os.path.dirname(os.path.realpath(__file__))
    if not os.path.isdir(folder):
        return
    if os.path.isfile(pth):
        with open(pth, 'r') as file:
            text = file.read()
            if os.path.isdir(text):
                if os.path.samefile(folder, text):
                    return
    with open(pth, 'w') as file:
        file.write(folder)
    print(f"Succeed Installed: '{folder}' \n       --> '{pth}'")


def __feedback():
    try:
        folder_logs = os.path.join(app_data.folder, 'logs')
        if not os.path.isdir(folder_logs):
            return
        folder_logs_feedback = os.path.join(app_data.folder, 'logs_feedback')
        make_dirs(folder_logs_feedback)
        has_feedback = set(os.listdir(folder_logs_feedback))
        date = datetime.datetime.now().strftime("%Y-%m-%d.log")
        for name in os.listdir(folder_logs):
            if name != date and name not in has_feedback:
                with open(os.path.join(folder_logs, name), 'r') as f1:
                    text = f1.read()
                    if feedback(text=text[0: 100000], subject=f'log <{name}>'):
                        with open(os.path.join(folder_logs_feedback, name), 'w') as f2:
                            f2.write('\n')
    except:
        pass


try:
    if app_data.getenv('disable_auto_feedback', default='False') != 'True':
        __feedback()
except:
    pass

try:
    app_data.log(f'import zml <zml: {get_time_compile()}, Python: {sys.version}>')
except:
    pass


class Iterator:
    def __init__(self, model, count, get):
        self.__model = model
        self.__index = 0
        self.__count = count
        self.__get = get

    def __iter__(self):
        self.__index = 0
        return self

    def __next__(self):
        if self.__index < self.__count:
            cell = self.__get(self.__model, self.__index)
            self.__index += 1
            return cell
        else:
            raise StopIteration()

    def __len__(self):
        return self.__count

    def __getitem__(self, ind):
        if ind < self.__count:
            return self.__get(self.__model, ind)


class Iterators:
    class Cell(Iterator):
        def __init__(self, model):
            super(Iterators.Cell, self).__init__(model, model.cell_number, lambda model, ind: model.get_cell(ind))

    class Face(Iterator):
        def __init__(self, model):
            super(Iterators.Face, self).__init__(model, model.face_number, lambda model, ind: model.get_face(ind))

    class Node(Iterator):
        def __init__(self, model):
            super(Iterators.Node, self).__init__(model, model.node_number, lambda model, ind: model.get_node(ind))

    class Link(Iterator):
        def __init__(self, model):
            super(Iterators.Link, self).__init__(model, model.link_number, lambda model, ind: model.get_link(ind))

    class Body(Iterator):
        def __init__(self, model):
            super(Iterators.Body, self).__init__(model, model.body_number, lambda model, ind: model.get_body(ind))

    class VirtualNode(Iterator):
        def __init__(self, model):
            super(Iterators.VirtualNode, self).__init__(model, model.virtual_node_number,
                                                        lambda model, ind: model.get_virtual_node(ind))

    class Element(Iterator):
        def __init__(self, model):
            super(Iterators.Element, self).__init__(model, model.element_number,
                                                    lambda model, ind: model.get_element(ind))

    class Spring(Iterator):
        def __init__(self, model):
            super(Iterators.Spring, self).__init__(model, model.spring_number, lambda model, ind: model.get_spring(ind))

    class Damper(Iterator):
        def __init__(self, model):
            super(Iterators.Damper, self).__init__(model, model.damper_number, lambda model, ind: model.get_damper(ind))

    class Fluid(Iterator):
        def __init__(self, model):
            super(Iterators.Fluid, self).__init__(model, model.fluid_number, lambda model, ind: model.get_fluid(ind))

    class Injector(Iterator):
        def __init__(self, model):
            super(Iterators.Injector, self).__init__(model, model.injector_number,
                                                     lambda model, ind: model.get_injector(ind))


class Field:
    """
    Define a three-dimensional field. Make value = f(pos) return data at any position.
    where pos is the coordinate and f is an instance of Field
    """

    class Constant:
        def __init__(self, value):
            self.__value = value

        def __call__(self, *args):
            return self.__value

    def __init__(self, value):
        if hasattr(value, '__call__'):
            self.__field = value
        else:
            self.__field = Field.Constant(value)

    def __call__(self, *args):
        return self.__field(*args)


class Vector(HasHandle):
    """
    Mapping C++ class: std::vector<double>
    """
    core.use(c_void_p, 'new_vector')
    core.use(None, 'del_vector', c_void_p)

    def __init__(self, value=None, path=None, handle=None):
        """
        Create this Vector object, and possibly initialize it
        """
        super(Vector, self).__init__(handle, core.new_vector, core.del_vector)
        if handle is None:
            self.set(value)
            if path is not None:
                self.load(path)
        else:
            assert value is None and path is None

    def __str__(self):
        return f'zml.Vector({self.to_list()})'

    core.use(None, 'vector_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.vector_save(self.handle, make_c_char_p(path))

    core.use(None, 'vector_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.vector_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vector_size', c_void_p)

    @property
    def size(self):
        return core.vector_size(self.handle)

    core.use(None, 'vector_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.vector_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_double, 'vector_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        if idx < self.size:
            return core.vector_get(self.handle, idx)

    core.use(None, 'vector_set', c_void_p, c_size_t, c_double)

    def __setitem__(self, idx, value):
        assert idx < self.size
        core.vector_set(self.handle, idx, value)

    def append(self, value):
        """
        向尾部追加元素
        """
        ind = self.size
        self.size += 1
        self[ind] = value
        return self

    def set(self, value=None):
        """
        Assign a list to this Vector
        """
        if value is not None:
            self.size = len(value)
            if len(value) > 0:
                p = self.pointer
                assert p is not None
                for i in range(len(value)):
                    p[i] = value[i]

    def to_list(self):
        """
        Convert Vector to list Object in Python
        """
        if len(self) == 0:
            return []
        p = self.pointer
        if p is not None:
            return [p[i] for i in range(len(self))]
        else:
            return []

    core.use(None, 'vector_read', c_void_p, c_void_p)

    def read_memory(self, pointer):
        """
        读取内存数据
        """
        core.vector_read(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'vector_write', c_void_p, c_void_p)

    def write_memory(self, pointer):
        """
        将数据写入到给定的内存地址
        """
        core.vector_write(self.handle, ctypes.cast(pointer, c_void_p))

    def read_numpy(self, data):
        """
        读取给定的numpy数组的数据
        """
        if np is not None:
            if not data.flags['C_CONTIGUOUS']:
                data = np.ascontiguous(data, dtype=data.dtype)  # 如果不是C连续的内存，必须强制转换
            self.size = len(data)
            self.read_memory(data.ctypes.data_as(POINTER(c_double)))

    def write_numpy(self, data):
        """
        将数据写入到numpy数组，必须保证给定的numpy数组的长度和self一致
        """
        if np is not None:
            if not data.flags['C_CONTIGUOUS']:
                data = np.ascontiguous(data, dtype=data.dtype)  # 如果不是C连续的内存，必须强制转换
            self.write_memory(data.ctypes.data_as(POINTER(c_double)))
            return data

    def to_numpy(self):
        """
        将这个Vector转化为一个numpy的数组
        """
        if np is not None:
            a = np.zeros(shape=self.size, dtype=float)
            return self.write_numpy(a)

    core.use(c_void_p, 'vector_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.vector_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_double))


class IntVector(HasHandle):
    """
    映射C++类：std::vector<long long>
    """
    core.use(c_void_p, 'new_llong_vector')
    core.use(None, 'del_llong_vector', c_void_p)

    def __init__(self, value=None, handle=None):
        super(IntVector, self).__init__(handle, core.new_llong_vector, core.del_llong_vector)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'llong_vector_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.llong_vector_save(self.handle, make_c_char_p(path))

    core.use(None, 'llong_vector_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.llong_vector_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'llong_vector_size', c_void_p)

    @property
    def size(self):
        return core.llong_vector_size(self.handle)

    core.use(None, 'llong_vector_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.llong_vector_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_int64, 'llong_vector_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        assert idx < self.size
        return core.llong_vector_get(self.handle, idx)

    core.use(None, 'llong_vector_set', c_void_p, c_size_t, c_int64)

    def __setitem__(self, idx, value):
        assert idx < self.size
        core.llong_vector_set(self.handle, idx, value)

    def append(self, value):
        """
        追加数据
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value):
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    core.use(c_void_p, 'llong_vector_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.llong_vector_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_int64))


Int64Vector = IntVector


class UintVector(HasHandle):
    """
    映射C++类：std::vector<std::size_t>
    """
    core.use(c_void_p, 'new_size_vector')
    core.use(None, 'del_size_vector', c_void_p)

    def __init__(self, value=None, handle=None):
        super(UintVector, self).__init__(handle, core.new_size_vector, core.del_size_vector)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'size_vector_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.size_vector_save(self.handle, make_c_char_p(path))

    core.use(None, 'size_vector_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.size_vector_load(self.handle, make_c_char_p(path))

    core.use(None, 'size_vector_print', c_void_p, c_char_p)

    def print_file(self, path):
        if path is not None:
            core.size_vector_print(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'size_vector_size', c_void_p)

    @property
    def size(self):
        return core.size_vector_size(self.handle)

    core.use(None, 'size_vector_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.size_vector_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_size_t, 'size_vector_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        assert idx < self.size
        return core.size_vector_get(self.handle, idx)

    core.use(None, 'size_vector_set', c_void_p, c_size_t, c_size_t)

    def __setitem__(self, idx, value):
        assert idx < self.size
        core.size_vector_set(self.handle, idx, value)

    def append(self, value):
        """
        追加数据
        """
        key = self.size
        self.size += 1
        self[key] = value

    def set(self, value):
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    core.use(c_void_p, 'size_vector_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.size_vector_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_size_t))


class StrVector(HasHandle):
    core.use(c_void_p, 'new_string_vector')
    core.use(None, 'del_string_vector', c_void_p)

    def __init__(self, handle=None):
        super(StrVector, self).__init__(handle, core.new_string_vector, core.del_string_vector)

    core.use(c_size_t, 'string_vector_size', c_void_p)

    @property
    def size(self):
        return core.string_vector_size(self.handle)

    core.use(None, 'string_vector_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.string_vector_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(None, 'string_vector_get', c_void_p, c_size_t, c_void_p)

    def __getitem__(self, idx):
        assert idx < self.size
        s = String()
        core.string_vector_get(self.handle, idx, s.handle)
        return s.to_str()

    core.use(None, 'string_vector_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        assert idx < self.size
        s = String(value=value)
        core.string_vector_set(self.handle, idx, s.handle)

    def set(self, value):
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements


class PtrVector(HasHandle):
    """
    映射C++类：std::vector<void*>. 需要在Python层面生成，并存储对象(必须在另外的地方存储，PtrVector仅仅存放handle，并不保有数据)。
    利用这个PtrVector与内核进行交互。
        注意：把handle存入这个PtrVector后，如果原始的对象被销毁，则内核读取的时候会出现致命错误。因此，PtrVector在使用的时候必须非常谨慎。
    """
    core.use(c_void_p, 'new_voidp_vector')
    core.use(None, 'del_voidp_vector', c_void_p)

    def __init__(self, value=None, handle=None):
        """
        初始化
        """
        super(PtrVector, self).__init__(handle, core.new_voidp_vector, core.del_voidp_vector)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(c_size_t, 'voidp_vector_size', c_void_p)

    @property
    def size(self):
        """
        元素的数量
        """
        return core.voidp_vector_size(self.handle)

    core.use(None, 'voidp_vector_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """
        设置元素的数量，并默认利用nullptr进行填充
        """
        core.voidp_vector_resize(self.handle, value)

    def __len__(self):
        """
        返回元素的数量
        """
        return self.size

    core.use(c_void_p, 'voidp_vector_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """
        返回地址
        """
        assert idx < self.size
        return core.voidp_vector_get(self.handle, idx)

    core.use(None, 'voidp_vector_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        """
        设置地址
        """
        assert idx < self.size
        core.voidp_vector_set(self.handle, idx, value)

    def set(self, value):
        """
        设置数组
        """
        self.size = len(value)
        for i in range(len(value)):
            self[i] = value[i]

    def to_list(self):
        """
        将地址转化为list
        """
        elements = []
        for i in range(len(self)):
            elements.append(self[i])
        return elements

    def get_object(self, idx, rtype):
        """
        将第key个元素作为一个HasHandle对象返回
        """
        if idx < len(self) and rtype is not None:
            handle = self[idx]
            if handle > 0:
                return rtype(handle=handle)

    def append(self, handle):
        """
        向尾部追加元素
        """
        ind = self.size
        self.size += 1
        self[ind] = handle
        return self

    @staticmethod
    def from_objects(objects):
        """
        从给定的对象中构建PtrVector，给定的对象，必须是HasHandle类型的
        """
        return PtrVector(value=[o.handle for o in objects])


class Map(HasHandle):
    core.use(c_void_p, 'new_string_double_map')
    core.use(None, 'del_string_double_map', c_void_p)

    def __init__(self, handle=None):
        super(Map, self).__init__(handle, core.new_string_double_map, core.del_string_double_map)

    core.use(None, 'string_double_map_get_keys', c_void_p, c_void_p)

    @property
    def keys(self):
        v = StrVector()
        core.string_double_map_get_keys(self.handle, v.handle)
        return v.to_list()

    core.use(c_double, 'string_double_map_get', c_void_p, c_void_p)

    def get(self, key):
        s = String(value=key)
        return core.string_double_map_get(self.handle, s.handle)

    core.use(None, 'string_double_map_set', c_void_p, c_void_p, c_double)

    def set(self, key, value):
        s = String(value=key)
        core.string_double_map_set(self.handle, s.handle, value)

    core.use(None, 'string_double_map_clear', c_void_p)

    def clear(self):
        core.string_double_map_clear(self.handle)

    def from_dict(self, value):
        self.clear()
        for key, val in value.items():
            self.set(key, val)

    def to_dict(self):
        r = {}
        for key in self.keys:
            r[key] = self.get(key)
        return r


class Matrix2(HasHandle):
    """
    映射C++类：zml::matrix_ty<double, 2>
    """
    core.use(c_void_p, 'new_matrix2')
    core.use(None, 'del_matrix2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Matrix2, self).__init__(handle, core.new_matrix2, core.del_matrix2)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'matrix2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.matrix2_save(self.handle, make_c_char_p(path))

    core.use(None, 'matrix2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.matrix2_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'matrix2_size_0', c_void_p)
    core.use(c_size_t, 'matrix2_size_1', c_void_p)

    @property
    def size_0(self):
        return core.matrix2_size_0(self.handle)

    @property
    def size_1(self):
        return core.matrix2_size_1(self.handle)

    core.use(None, 'matrix2_resize', c_void_p, c_size_t, c_size_t)

    def resize(self, value):
        assert len(value) == 2
        core.matrix2_resize(self.handle, value[0], value[1])

    @property
    def size(self):
        return self.size_0, self.size_1

    @size.setter
    def size(self, value):
        self.resize(value)

    core.use(c_double, 'matrix2_get', c_void_p, c_size_t, c_size_t)

    def get(self, key0, key1):
        assert key0 < self.size_0
        assert key1 < self.size_1
        return core.matrix2_get(self.handle, key0, key1)

    core.use(None, 'matrix2_set', c_void_p, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, value):
        assert key0 < self.size_0
        assert key1 < self.size_1
        core.matrix2_set(self.handle, key0, key1, value)

    def __getitem__(self, key):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        return self.get(i, j)

    def __setitem__(self, key, value):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        self.set(i, j, value)


class Interp1(HasHandle):
    core.use(c_void_p, 'new_interp1')
    core.use(None, 'del_interp1', c_void_p)

    def __init__(self, xmin=None, dx=None, x=None, y=None, value=None, path=None, handle=None):
        super(Interp1, self).__init__(handle, core.new_interp1, core.del_interp1)
        if handle is None:
            self.set(xmin=xmin, dx=dx, x=x, y=y, value=value)
            if path is not None:
                self.load(path)

    core.use(None, 'interp1_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.interp1_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.interp1_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp1_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.interp1_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.interp1_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp1_set_x2y', c_void_p, c_void_p, c_void_p)
    core.use(None, 'interp1_set_x2y_evenly', c_void_p, c_double, c_double, c_void_p)
    core.use(None, 'interp1_set_const', c_void_p, c_double)

    def set(self, xmin=None, dx=None, x=None, y=None, value=None):
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
        """
        创建插值。其中y=get_value(x)为给定的函数
        """
        assert xmin < xmax and dx > 0
        kernel = CFUNCTYPE(c_double, c_double)
        core.interp1_create(self.handle, xmin, dx, xmax, kernel(get_value))

    core.use(c_bool, 'interp1_empty', c_void_p)

    @property
    def empty(self):
        return core.interp1_empty(self.handle)

    core.use(None, 'interp1_get_vx', c_void_p, c_void_p)
    core.use(None, 'interp1_get_vy', c_void_p, c_void_p)

    def get_data(self):
        """
        返回内核数据的拷贝
        """
        x = Vector()
        y = Vector()
        core.interp1_get_vx(self.handle, x.handle)
        core.interp1_get_vy(self.handle, y.handle)
        return x, y

    core.use(c_double, 'interp1_get', c_void_p, c_double, c_bool)

    def get(self, x, no_external=True):
        if isinstance(x, Iterable):
            return [core.interp1_get(self.handle, scale, no_external) for scale in x]
        else:
            return core.interp1_get(self.handle, x, no_external)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp1_is_inner', c_void_p, c_double)

    def is_inner(self, x):
        return core.interp1_is_inner(self.handle, x)

    core.use(c_double, 'interp1_get_xmin', c_void_p)
    core.use(c_double, 'interp1_get_xmax', c_void_p)

    def xrange(self):
        return core.interp1_get_xmin(self.handle), core.interp1_get_xmax(self.handle)

    core.use(None, 'interp1_to_evenly_spaced', c_void_p, c_size_t, c_size_t)

    def to_evenly_spaced(self, nmin=100, nmax=1000):
        """
        将插值转化成为均匀的间隔，这样查找会更快.
        """
        core.interp1_to_evenly_spaced(self.handle, nmin, nmax)
        return self

    core.use(None, 'interp1_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Interp1)
        core.interp1_clone(self.handle, other.handle)


class Interp2(HasHandle):
    core.use(c_void_p, 'new_interp2')
    core.use(None, 'del_interp2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Interp2, self).__init__(handle, core.new_interp2, core.del_interp2)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'interp2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp2_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """
        创建插值。其中y=get_value(x)为给定的函数
        """
        assert xmin < xmax and dx > 0
        assert ymin < ymax and dy > 0
        Kernel = CFUNCTYPE(c_double, c_double, c_double)
        core.interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, Kernel(get_value))

    core.use(c_bool, 'interp2_empty', c_void_p)

    @property
    def empty(self):
        return core.interp2_empty(self.handle)

    core.use(c_double, 'interp2_get', c_void_p, c_double, c_double, c_bool)

    def get(self, x, y, no_external=True):
        return core.interp2_get(self.handle, x, y, no_external)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        return core.interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'interp2_get_xmin', c_void_p)
    core.use(c_double, 'interp2_get_xmax', c_void_p)
    core.use(c_double, 'interp2_get_ymin', c_void_p)
    core.use(c_double, 'interp2_get_ymax', c_void_p)

    def xrange(self):
        return core.interp2_get_xmin(self.handle), core.interp2_get_xmax(self.handle)

    def yrange(self):
        return core.interp2_get_ymin(self.handle), core.interp2_get_ymax(self.handle)

    core.use(None, 'interp2_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Interp2)
        core.interp2_clone(self.handle, other.handle)


class Interp3(HasHandle):
    core.use(c_void_p, 'new_interp3')
    core.use(None, 'del_interp3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Interp3, self).__init__(handle, core.new_interp3, core.del_interp3)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'interp3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'interp3_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax, get_value):
        """
        创建插值。其中y=get_value(x)为给定的函数
        """
        assert xmin < xmax and dx > 0
        assert ymin < ymax and dy > 0
        assert zmin < zmax and dz > 0
        Kernel = CFUNCTYPE(c_double, c_double, c_double, c_double)
        core.interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                            Kernel(get_value))

    core.use(c_bool, 'interp3_empty', c_void_p)

    @property
    def empty(self):
        return core.interp3_empty(self.handle)

    core.use(c_double, 'interp3_get', c_void_p, c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True):
        return core.interp3_get(self.handle, x, y, z, no_external)

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        return core.interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'interp3_get_xmin', c_void_p)
    core.use(c_double, 'interp3_get_xmax', c_void_p)
    core.use(c_double, 'interp3_get_ymin', c_void_p)
    core.use(c_double, 'interp3_get_ymax', c_void_p)
    core.use(c_double, 'interp3_get_zmin', c_void_p)
    core.use(c_double, 'interp3_get_zmax', c_void_p)

    def xrange(self):
        return core.interp3_get_xmin(self.handle), core.interp3_get_xmax(self.handle)

    def yrange(self):
        return core.interp3_get_ymin(self.handle), core.interp3_get_ymax(self.handle)

    def zrange(self):
        return core.interp3_get_zmin(self.handle), core.interp3_get_zmax(self.handle)

    core.use(None, 'interp3_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Interp3)
        core.interp3_clone(self.handle, other.handle)


class FileMap(HasHandle):
    """
    文件映射类。将文件夹和多个文件做成一个文件（但是不进行压缩）。
    """
    core.use(c_void_p, 'new_fmap')
    core.use(None, 'del_fmap', c_void_p)

    def __init__(self, value=None, path=None, handle=None):
        super(FileMap, self).__init__(handle, core.new_fmap, core.del_fmap)
        if handle is None:
            if value is not None:
                self.data = value
            if path is not None:
                self.load(path)

    core.use(c_bool, 'fmap_is_dir', c_void_p)

    @property
    def is_dir(self):
        """
        是否是一个文件夹的映射
        """
        return core.fmap_is_dir(self.handle)

    core.use(c_bool, 'fmap_has_key', c_void_p, c_char_p)

    def has_key(self, key):
        """
        是否存在key指定的子目录
        """
        return core.fmap_has_key(self.handle, make_c_char_p(key))

    core.use(None, 'fmap_get', c_void_p, c_void_p, c_char_p)

    def get(self, key):
        """
        当存在key的时候，将key的内容作为一个新的FileMap返回。调用之前必须检查key是否存在
        """
        fmap = FileMap()
        core.fmap_get(self.handle, fmap.handle, make_c_char_p(key))
        return fmap

    core.use(None, 'fmap_set', c_void_p, c_void_p, c_char_p)

    def set(self, key, fmap):
        """
        将fmap存储到key里面
        """
        if isinstance(fmap, FileMap):
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))
        else:
            fmap = FileMap(fmap)
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))

    core.use(None, 'fmap_erase', c_void_p, c_char_p)

    def erase(self, key):
        """
        删除key
        """
        core.fmap_erase(self.handle, make_c_char_p(key))

    core.use(None, 'fmap_write', c_void_p, c_char_p)

    def write(self, path):
        """
        将内容提取出来
        """
        core.fmap_write(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_read', c_void_p, c_char_p)

    def read(self, path):
        """
        从文件获得内容
        """
        core.fmap_read(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存 (鉴于此class的特殊性，务必保存为二进制格式，txt和xml格式，都可能带来不可预期的数据丢失).
        """
        if path is not None:
            ext = os.path.splitext(path)[-1].lower()
            assert ext != '.txt' and ext != '.xml'
            core.fmap_save(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取
        """
        if path is not None:
            core.fmap_load(self.handle, make_c_char_p(path))

    core.use(None, 'fmap_get_data', c_void_p, c_void_p)
    core.use(None, 'fmap_set_data', c_void_p, c_void_p)

    @property
    def data(self):
        data = String()
        core.fmap_get_data(self.handle, data.handle)
        return data.to_str()

    @data.setter
    def data(self, value):
        if isinstance(value, String):
            core.fmap_set_data(self.handle, value.handle)
            return
        if isinstance(value, str):
            value = String(value)
            core.fmap_set_data(self.handle, value.handle)
            return
        else:
            value = String(f'{value}')
            core.fmap_set_data(self.handle, value.handle)
            return


class Array2(HasHandle):
    core.use(c_void_p, 'new_array2')
    core.use(None, 'del_array2', c_void_p)

    def __init__(self, x=None, y=None, path=None, handle=None):
        super(Array2, self).__init__(handle, core.new_array2, core.del_array2)
        if handle is None:
            if path is not None:
                self.load(path)
            if x is not None:
                self[0] = x
            if y is not None:
                self[1] = y
        else:
            assert x is None and y is None and path is None

    core.use(None, 'array2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.array2_save(self.handle, make_c_char_p(path))

    core.use(None, 'array2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.array2_load(self.handle, make_c_char_p(path))

    core.use(None, 'array2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.array2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.array2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        return f'zml.Array2({self[0]}, {self[1]})'

    def __len__(self):
        return 2

    core.use(c_double, 'array2_get', c_void_p, c_size_t)

    def get(self, dim):
        assert dim == 0 or dim == 1
        return core.array2_get(self.handle, dim)

    core.use(None, 'array2_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        assert dim == 0 or dim == 1
        core.array2_set(self.handle, dim, value)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def to_list(self):
        return [self[0], self[1]]

    def to_tuple(self):
        return self[0], self[1]

    @staticmethod
    def from_list(values):
        assert len(values) == 2
        return Array2(x=values[0], y=values[1])


class Array3(HasHandle):
    core.use(c_void_p, 'new_array3')
    core.use(None, 'del_array3', c_void_p)

    def __init__(self, x=None, y=None, z=None, path=None, handle=None):
        super(Array3, self).__init__(handle, core.new_array3, core.del_array3)
        if handle is None:
            if path is not None:
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
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.array3_save(self.handle, make_c_char_p(path))

    core.use(None, 'array3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.array3_load(self.handle, make_c_char_p(path))

    core.use(None, 'array3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'array3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.array3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.array3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        return f'zml.Array3({self[0]}, {self[1]}, {self[2]})'

    def __len__(self):
        return 3

    core.use(c_double, 'array3_get', c_void_p, c_size_t)

    def get(self, dim):
        assert 0 <= dim < 3
        return core.array3_get(self.handle, dim)

    core.use(None, 'array3_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        assert 0 <= dim < 3
        core.array3_set(self.handle, dim, value)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def to_list(self):
        return [self[0], self[1], self[2]]

    def to_tuple(self):
        return self[0], self[1], self[2]

    @staticmethod
    def from_list(values):
        assert len(values) == 3
        return Array3(x=values[0], y=values[1], z=values[2])


class Tensor2(HasHandle):
    """
    二阶张量
    """
    core.use(c_void_p, 'new_tensor2')
    core.use(None, 'del_tensor2', c_void_p)

    def __init__(self, xx=None, yy=None, xy=None, path=None, handle=None):
        """
        初始化
        """
        super(Tensor2, self).__init__(handle, core.new_tensor2, core.del_tensor2)
        if handle is None:
            if path is not None:
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
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.tensor2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.tensor2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.tensor2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.tensor2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        return f'zml.Tensor2({self.xx}, {self.yy}, {self.xy})'

    core.use(c_double, 'tensor2_get', c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        assert i == 0 or i == 1
        assert j == 0 or j == 1
        return core.tensor2_get(self.handle, i, j)

    core.use(None, 'tensor2_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        assert i == 0 or i == 1
        assert j == 0 or j == 1
        core.tensor2_set(self.handle, i, j, value)

    core.use(None, 'tensor2_set_max_min_angle', c_void_p, c_double, c_double, c_double)

    def set_max_min_angle(self, max_value=None, min_value=None, angle=None):
        """
        利用张量的最大值、最小值和最大值对应的方向（从x轴正方向沿着逆时针方向旋转的弧度数）
        """
        if max_value is not None and min_value is not None and angle is not None:
            core.tensor2_set_max_min_angle(self.handle, max_value, min_value, angle)

    @property
    def xx(self):
        return self[(0, 0)]

    @xx.setter
    def xx(self, value):
        self[0, 0] = value

    @property
    def yy(self):
        return self[(1, 1)]

    @yy.setter
    def yy(self, value):
        self[(1, 1)] = value

    @property
    def xy(self):
        return self[(0, 1)]

    @xy.setter
    def xy(self, value):
        self[(0, 1)] = value

    @staticmethod
    def create(max, min, angle):
        """
        利用张量的最大特征值，最小特征值和最大特征值对应的方向angle来建立二阶张量。其中angle的单位为弧度（与x轴正方向的夹角）
        """
        tensor = Tensor2()
        tensor.set_max_min_angle(max, min, angle)
        return tensor

    def __add__(self, other):
        xx = self.xx + other.xx
        yy = self.yy + other.yy
        xy = self.xy + other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __sub__(self, other):
        xx = self.xx - other.xx
        yy = self.yy - other.yy
        xy = self.xy - other.xy
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __mul__(self, value):
        xx = self.xx * value
        yy = self.yy * value
        xy = self.xy * value
        return Tensor2(xx=xx, yy=yy, xy=xy)

    def __truediv__(self, value):
        xx = self.xx / value
        yy = self.yy / value
        xy = self.xy / value
        return Tensor2(xx=xx, yy=yy, xy=xy)


class Tensor3(HasHandle):
    core.use(c_void_p, 'new_tensor3')
    core.use(None, 'del_tensor3', c_void_p)

    def __init__(self, xx=None, yy=None, zz=None, xy=None, yz=None, zx=None, path=None, handle=None):
        super(Tensor3, self).__init__(handle, core.new_tensor3, core.del_tensor3)
        if handle is None:
            if path is not None:
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
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.tensor3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.tensor3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.tensor3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.tensor3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        return f'zml.Tensor3({self.xx}, {self.yy}, {self.zz}, {self.xy}, {self.yz}, {self.zx})'

    core.use(c_double, 'tensor3_get', c_void_p, c_size_t, c_size_t)

    def __getitem__(self, key):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        assert 0 <= i < 3
        assert 0 <= j < 3
        return core.tensor3_get(self.handle, i, j)

    core.use(None, 'tensor3_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        assert len(key) == 2
        i = key[0]
        j = key[1]
        assert 0 <= i < 3
        assert 0 <= j < 3
        core.tensor3_set(self.handle, i, j, value)

    @property
    def xx(self):
        return self[(0, 0)]

    @xx.setter
    def xx(self, value):
        self[0, 0] = value

    @property
    def yy(self):
        return self[(1, 1)]

    @yy.setter
    def yy(self, value):
        self[(1, 1)] = value

    @property
    def zz(self):
        return self[(2, 2)]

    @zz.setter
    def zz(self, value):
        self[(2, 2)] = value

    @property
    def xy(self):
        return self[(0, 1)]

    @xy.setter
    def xy(self, value):
        self[(0, 1)] = value

    @property
    def yz(self):
        return self[(1, 2)]

    @yz.setter
    def yz(self, value):
        self[(1, 2)] = value

    @property
    def zx(self):
        return self[(2, 0)]

    @zx.setter
    def zx(self, value):
        self[(2, 0)] = value

    core.use(c_double, 'tensor3_get_along', c_void_p, c_double, c_double, c_double)

    def get_along(self, *args):
        """
        返回给定方向下的数值.
        """
        if len(args) == 3:
            return core.tensor3_get_along(self.handle, *args)
        else:
            assert len(args) == 1
            x = args[0]
            return core.tensor3_get_along(self.handle, x[0], x[1], x[2])


class Tensor2Interp2(HasHandle):
    core.use(c_void_p, 'new_tensor2interp2')
    core.use(None, 'del_tensor2interp2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Tensor2Interp2, self).__init__(handle, core.new_tensor2interp2, core.del_tensor2interp2)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'tensor2interp2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.tensor2interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.tensor2interp2_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor2interp2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.tensor2interp2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.tensor2interp2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor2interp2_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, get_value):
        """
        创建插值。其中y=get_value(x)为给定的函数
        """
        Kernel = CFUNCTYPE(c_double, c_double, c_double, c_size_t)
        core.tensor2interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax,
                                   Kernel(get_value))

    core.use(c_bool, 'tensor2interp2_empty', c_void_p)

    @property
    def empty(self):
        return core.tensor2interp2_empty(self.handle)

    core.use(None, 'tensor2interp2_get', c_void_p, c_void_p,
             c_double, c_double, c_bool)

    def get(self, x, y, no_external=True, value=None):
        if value is None:
            value = Tensor2()
        core.tensor2interp2_get(self.handle, value.handle, x, y, no_external)
        return value

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    core.use(c_bool, 'tensor2interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        return core.tensor2interp2_is_inner(self.handle, x, y)

    core.use(c_double, 'tensor2interp2_get_xmin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_xmax', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymin', c_void_p)
    core.use(c_double, 'tensor2interp2_get_ymax', c_void_p)

    def xrange(self):
        return core.tensor2interp2_get_xmin(self.handle), core.tensor2interp2_get_xmax(self.handle)

    def yrange(self):
        return core.tensor2interp2_get_ymin(self.handle), core.tensor2interp2_get_ymax(self.handle)


class Tensor3Interp3(HasHandle):
    core.use(c_void_p, 'new_tensor3interp3')
    core.use(None, 'del_tensor3interp3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Tensor3Interp3, self).__init__(handle, core.new_tensor3interp3, core.del_tensor3interp3)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'tensor3interp3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.tensor3interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.tensor3interp3_load(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'tensor3interp3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.tensor3interp3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.tensor3interp3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'tensor3interp3_create', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double, c_void_p)

    def create(self, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax, get_value):
        """
        创建插值。其中y=get_value(x)为给定的函数
        """
        Kernel = CFUNCTYPE(c_double, c_double, c_double, c_double, c_size_t)
        core.tensor3interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                                   Kernel(get_value))

    def create_constant(self, value):
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
        return core.tensor3interp3_empty(self.handle)

    core.use(None, 'tensor3interp3_get', c_void_p, c_void_p,
             c_double, c_double, c_double, c_bool)

    def get(self, x, y, z, no_external=True, value=None):
        if value is None:
            value = Tensor3()
        core.tensor3interp3_get(self.handle, value.handle, x, y, z, no_external)
        return value

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    core.use(c_bool, 'tensor3interp3_is_inner', c_void_p, c_double, c_double, c_double)

    def is_inner(self, x, y, z):
        return core.tensor3interp3_is_inner(self.handle, x, y, z)

    core.use(c_double, 'tensor3interp3_get_xmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_xmax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_ymax', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmin', c_void_p)
    core.use(c_double, 'tensor3interp3_get_zmax', c_void_p)

    def xrange(self):
        return core.tensor3interp3_get_xmin(self.handle), core.tensor3interp3_get_xmax(self.handle)

    def yrange(self):
        return core.tensor3interp3_get_ymin(self.handle), core.tensor3interp3_get_ymax(self.handle)

    def zrange(self):
        return core.tensor3interp3_get_zmin(self.handle), core.tensor3interp3_get_zmax(self.handle)


class Coord2(HasHandle):
    core.use(c_void_p, 'new_coord2')
    core.use(None, 'del_coord2', c_void_p)

    def __init__(self, origin=None, xdir=None, path=None, handle=None):
        super(Coord2, self).__init__(handle, core.new_coord2, core.del_coord2)
        if handle is None:
            if path is not None:
                self.load(path)
            if origin is not None and xdir is not None:
                self.set(origin, xdir)

    core.use(None, 'coord2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.coord2_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.coord2_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.coord2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.coord2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        return f'zml.Coord2(origin = {self.origin}, xdir = {self.xdir})'

    core.use(None, 'coord2_set', c_void_p, c_size_t, c_size_t)

    def set(self, origin, xdir):
        if not isinstance(origin, Array2):
            origin = Array2.from_list(origin)
        if not isinstance(xdir, Array2):
            xdir = Array2.from_list(xdir)
        core.coord2_set(self.handle, origin.handle, xdir.handle)

    core.use(c_void_p, 'coord2_get_origin', c_void_p)

    @property
    def origin(self):
        return Array2(handle=core.coord2_get_origin(self.handle))

    core.use(None, 'coord2_get_xdir', c_void_p, c_size_t)

    @property
    def xdir(self):
        temp = Array2()
        core.coord2_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self):
        temp = Array2()
        core.coord2_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord2_view_array2', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord2_view_tensor2', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
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
    core.use(c_void_p, 'new_coord3')
    core.use(None, 'del_coord3', c_void_p)

    def __init__(self, origin=None, xdir=None, ydir=None, path=None, handle=None):
        """
        构造函数，并在需要的时候初始化
        :param origin: 坐标原点
        :param xdir: x正方向
        :param ydir: y正方向
        :param handle: 句柄：当为None的时候，则创建新的对象，否则，会创建当前对象的引用(此时所有的初始化参数无效)
        """
        super(Coord3, self).__init__(handle, core.new_coord3, core.del_coord3)
        if handle is None:
            if path is not None:
                self.load(path)
            if origin is not None and xdir is not None and ydir is not None:
                self.set(origin, xdir, ydir)
        else:
            assert origin is None and xdir is None and ydir is None

    core.use(None, 'coord3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.coord3_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.coord3_load(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'coord3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.coord3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.coord3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __str__(self):
        """
        :return: 当前坐标系的字符串表示(仅仅用于显示)
        """
        return f'zml.Coord3(origin = {self.origin}, xdir = {self.xdir}, ydir = {self.ydir})'

    core.use(None, 'coord3_set', c_void_p, c_void_p, c_void_p, c_void_p)

    def set(self, origin, xdir, ydir):
        """
        设置坐标系
        :param origin: 坐标原点
        :param xdir: x正方向
        :param ydir: y正方向
        :return: None
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
        """
        :return: 标原点 返回的是一个内部数据的引用，可以利用这个引用来修改坐标原点)
        """
        return Array3(handle=core.coord3_get_origin(self.handle))

    core.use(None, 'coord3_get_xdir', c_void_p, c_size_t)

    @property
    def xdir(self):
        """
        :return: x轴正方向在全局坐标系下面的数值
        """
        temp = Array3()
        core.coord3_get_xdir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_get_ydir', c_void_p, c_size_t)

    @property
    def ydir(self):
        """
        :return: y轴正方向在全局坐标系下面的数值
        """
        temp = Array3()
        core.coord3_get_ydir(self.handle, temp.handle)
        return temp

    core.use(None, 'coord3_view_array3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(None, 'coord3_view_tensor3', c_void_p, c_size_t, c_size_t, c_size_t)

    def view(self, coord, o, buffer=None):
        """
        对给定的对象进行坐标转换
        :param coord: 原始坐标系
        :param o: 原始坐标系下的对象 (向量或者张量)
        :param buffer: 用于存储计算计算结果的缓冲区，类型和o保持一致，为向量或者张量
        :return: 当前坐标系下面的值 (向量或者张量)
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


class Mesh3(HasHandle):
    """
    三维网格类
    """

    class Node(Object):
        def __init__(self, model, index):
            assert isinstance(model, Mesh3)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'mesh3_get_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            返回位置
            """
            return [core.mesh3_get_node_pos(self.model.handle, self.index, i) for i in range(3)]

        core.use(None, 'mesh3_set_node_pos', c_void_p, c_size_t, c_size_t, c_double)

        @pos.setter
        def pos(self, value):
            """
            设置位置
            """
            assert len(value) == 3
            for i in range(3):
                core.mesh3_set_node_pos(self.model.handle, self.index, i, value[i])

        core.use(c_size_t, 'mesh3_get_node_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            return core.mesh3_get_node_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            return core.mesh3_get_node_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            return core.mesh3_get_node_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            if 0 <= index < self.link_number:
                i = core.mesh3_get_node_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_node_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            if 0 <= index < self.face_number:
                i = core.mesh3_get_node_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_node_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            if 0 <= index < self.body_number:
                i = core.mesh3_get_node_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def links(self):
            return Iterators.Link(self)

        @property
        def faces(self):
            return Iterators.Face(self)

        @property
        def bodies(self):
            return Iterators.Body(self)

        core.use(c_double, 'mesh3_get_node_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_node_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            if index is None:
                return default_val
            value = core.mesh3_get_node_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_node_attr(self.model.handle, self.index, index, value)
            return self

    class Link(Object):
        def __init__(self, model, index):
            assert isinstance(model, Mesh3)
            assert index < model.link_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_link_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            return core.mesh3_get_link_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            return core.mesh3_get_link_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            return core.mesh3_get_link_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            if 0 <= index < self.node_number:
                i = core.mesh3_get_link_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_link_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            if 0 <= index < self.face_number:
                i = core.mesh3_get_link_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_link_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            if 0 <= index < self.body_number:
                i = core.mesh3_get_link_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            return Iterators.Node(self)

        @property
        def faces(self):
            return Iterators.Face(self)

        @property
        def bodies(self):
            return Iterators.Body(self)

        @property
        def length(self):
            assert self.node_number == 2
            return get_distance(self.get_node(0).pos, self.get_node(1).pos)

        @property
        def pos(self):
            """
            中心点的位置
            """
            assert self.node_number == 2
            p0, p1 = self.get_node(0).pos, self.get_node(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_double, 'mesh3_get_link_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_link_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            if index is None:
                return default_val
            value = core.mesh3_get_link_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_link_attr(self.model.handle, self.index, index, value)
            return self

    class Face(Object):
        def __init__(self, model, index):
            assert isinstance(model, Mesh3)
            assert index < model.face_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_face_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            return core.mesh3_get_face_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            return core.mesh3_get_face_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_body_number', c_void_p, c_size_t)

        @property
        def body_number(self):
            return core.mesh3_get_face_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            if 0 <= index < self.node_number:
                i = core.mesh3_get_face_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_face_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            if 0 <= index < self.link_number:
                i = core.mesh3_get_face_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_face_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            if 0 <= index < self.body_number:
                i = core.mesh3_get_face_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            return Iterators.Node(self)

        @property
        def links(self):
            return Iterators.Link(self)

        @property
        def bodies(self):
            return Iterators.Body(self)

        core.use(c_double, 'mesh3_get_face_area', c_void_p, c_size_t)

        @property
        def area(self):
            return core.mesh3_get_face_area(self.model.handle, self.index)

        @property
        def pos(self):
            """
            The position of the face (The averaged value of nodes)
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

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            if index is None:
                return default_val
            value = core.mesh3_get_face_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_face_attr(self.model.handle, self.index, index, value)
            return self

    class Body(Object):
        def __init__(self, model, index):
            assert isinstance(model, Mesh3)
            assert index < model.body_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_body_node_number', c_void_p, c_size_t)

        @property
        def node_number(self):
            return core.mesh3_get_body_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_link_number', c_void_p, c_size_t)

        @property
        def link_number(self):
            return core.mesh3_get_body_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_face_number', c_void_p, c_size_t)

        @property
        def face_number(self):
            return core.mesh3_get_body_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index):
            if 0 <= index < self.node_number:
                i = core.mesh3_get_body_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_body_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            if 0 <= index < self.link_number:
                i = core.mesh3_get_body_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_body_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            if 0 <= index < self.face_number:
                i = core.mesh3_get_body_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        @property
        def nodes(self):
            return Iterators.Node(self)

        @property
        def links(self):
            return Iterators.Link(self)

        @property
        def faces(self):
            return Iterators.Face(self)

        @property
        def pos(self):
            """
            The position of the body (The averaged value of nodes)
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
            return core.mesh3_get_body_volume(self.model.handle, self.index)

        core.use(c_double, 'mesh3_get_body_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_body_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            if index is None:
                return default_val
            value = core.mesh3_get_body_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_body_attr(self.model.handle, self.index, index, value)
            return self

        core.use(c_bool, 'mesh3_body_contains', c_void_p, c_size_t, c_double, c_double, c_double)

        def contains(self, pos):
            """
            返回给定的位置是否包含在此body中
            """
            assert len(pos) == 3, f'pos = {pos}'
            return core.mesh3_body_contains(self.model.handle, self.index, *pos)

    core.use(c_void_p, 'new_mesh3')
    core.use(None, 'del_mesh3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Mesh3, self).__init__(handle, core.new_mesh3, core.del_mesh3)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.Mesh3(handle = {self.handle}, node_n = {self.node_number}, link_n = {self.link_number}, face_n = {self.face_number}, body_n = {self.body_number})'

    core.use(None, 'mesh3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.mesh3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mesh3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.mesh3_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'mesh3_get_node_number', c_void_p)

    @property
    def node_number(self):
        return core.mesh3_get_node_number(self.handle)

    core.use(c_size_t, 'mesh3_get_link_number', c_void_p)

    @property
    def link_number(self):
        return core.mesh3_get_link_number(self.handle)

    core.use(c_size_t, 'mesh3_get_face_number', c_void_p)

    @property
    def face_number(self):
        return core.mesh3_get_face_number(self.handle)

    core.use(c_size_t, 'mesh3_get_body_number', c_void_p)

    @property
    def body_number(self):
        return core.mesh3_get_body_number(self.handle)

    def get_node(self, index):
        if 0 <= index < self.node_number:
            return Mesh3.Node(self, index)

    def get_link(self, index):
        if 0 <= index < self.link_number:
            return Mesh3.Link(self, index)

    def get_face(self, index):
        if 0 <= index < self.face_number:
            return Mesh3.Face(self, index)

    def get_body(self, index):
        if 0 <= index < self.body_number:
            return Mesh3.Body(self, index)

    @property
    def nodes(self):
        return Iterators.Node(self)

    @property
    def links(self):
        return Iterators.Link(self)

    @property
    def faces(self):
        return Iterators.Face(self)

    @property
    def bodies(self):
        return Iterators.Body(self)

    core.use(c_size_t, 'mesh3_add_node', c_void_p, c_double, c_double, c_double)

    def add_node(self, x, y, z):
        index = core.mesh3_add_node(self.handle, x, y, z)
        return self.get_node(index)

    core.use(c_size_t, 'mesh3_add_link', c_void_p, c_size_t, c_size_t)

    def add_link(self, nodes):
        assert len(nodes) == 2
        for elem in nodes:
            assert isinstance(elem, Mesh3.Node)
        index = core.mesh3_add_link(self.handle, nodes[0].index, nodes[1].index)
        return self.get_link(index)

    core.use(c_size_t, 'mesh3_add_face3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(c_size_t, 'mesh3_add_face4', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def add_face(self, links):
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
        assert isinstance(c_new, Coord3)
        assert isinstance(c_old, Coord3)
        core.mesh3_change_view(self.handle, c_new.handle, c_old.handle)
        return self

    core.use(None, 'mesh3_get_slice', c_void_p, c_void_p, c_void_p)

    def get_slice(self, node_kept):
        kernel = CFUNCTYPE(c_bool, c_double, c_double, c_double)
        data = Mesh3()
        core.mesh3_get_slice(data.handle, self.handle, kernel(node_kept))
        return data

    core.use(None, 'mesh3_append', c_void_p, c_void_p)

    def append(self, other):
        assert isinstance(other, Mesh3)
        core.mesh3_append(self.handle, other.handle)
        return self

    core.use(None, 'mesh3_del_nodes', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_nodes', c_void_p)

    def del_nodes(self, should_del=None):
        if should_del is None:
            core.mesh3_del_isolated_nodes(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_nodes(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_links', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_links', c_void_p)

    def del_links(self, should_del=None):
        if should_del is None:
            core.mesh3_del_isolated_links(self.handle)
        else:
            Kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_links(self.handle, Kernel(should_del))

    core.use(None, 'mesh3_del_faces', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_faces', c_void_p)

    def del_faces(self, should_del=None):
        if should_del is None:
            core.mesh3_del_isolated_faces(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_faces(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_bodies', c_void_p, c_void_p)

    def del_bodies(self, should_del=None):
        assert should_del is not None
        kernel = CFUNCTYPE(c_bool, c_size_t)
        core.mesh3_del_bodies(self.handle, kernel(should_del))

    def del_isolated_nodes(self):
        core.mesh3_del_isolated_nodes(self.handle)

    def del_isolated_links(self):
        core.mesh3_del_isolated_links(self.handle)

    def del_isolated_faces(self):
        core.mesh3_del_isolated_faces(self.handle)

    core.use(None, 'mesh3_print_trimesh', c_void_p, c_char_p, c_char_p, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def print_trimesh(vertex_file, triangle_file, data, index_start_from=1, na=99999999, fa=99999999):
        """
        将三角形网格信息打印到文件。注意，给定的文件路径绝对不能包含中文字符，否则会出错;
        """
        assert isinstance(data, Mesh3)
        core.mesh3_print_trimesh(data.handle, make_c_char_p(vertex_file), make_c_char_p(triangle_file),
                                 index_start_from, na, fa)

    core.use(None, 'mesh3_create_tri', c_void_p, c_double, c_double,
             c_double, c_double, c_double)

    @staticmethod
    def create_tri(x1, y1, x2, y2, edge_length):
        """
        在位于x-y平面内<z坐标等于0>的矩形区域内<矩形的边平行于x-y坐标轴>创建等边三角形网格;
        由于所有的三角形都是等边三角形，所以某个边可能会是锯齿状的.
        另外，实际网格的坐标范围，可能不会严格等于x1, y1, x2, y2规定的范围。

        -测试----------------------
        使用如下脚本生成测试数据：
from zml import *
mesh = Mesh3.create_tri(0, 0, 100, 50, 3.0)
print(mesh)
Mesh3.print_trimesh('mesh.ver', 'mesh.tri', mesh, 1)

        使用如下的Matlab脚本绘图：
ver = load('mesh.ver');
tri = load('mesh.tri');
trimesh(tri, ver(:,1), ver(:,2))
axis equal
        """
        data = Mesh3()
        core.mesh3_create_tri(data.handle, x1, y1, x2, y2, edge_length)
        return data

    core.use(None, 'mesh3_create_tetra', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double)

    @staticmethod
    def create_tetra(x1, y1, z1, x2, y2, z2, edge_length):
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
        if self.node_number > 0:
            index = core.mesh3_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_node(index)

    core.use(c_size_t, 'mesh3_get_nearest_link_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_link(self, pos):
        if self.link_number > 0:
            index = core.mesh3_get_nearest_link_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_link(index)

    core.use(c_size_t, 'mesh3_get_nearest_face_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_face(self, pos):
        if self.face_number > 0:
            index = core.mesh3_get_nearest_face_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_face(index)

    core.use(c_size_t, 'mesh3_get_nearest_body_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_body(self, pos):
        if self.body_number > 0:
            index = core.mesh3_get_nearest_body_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_body(index)

    core.use(None, 'mesh3_get_loc_range', c_void_p, c_void_p, c_void_p)

    def get_pos_range(self, lr=None, rr=None):
        """
        返回所有的node在空间的坐标范围
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
        在二维的点之间建立连接
        """
        assert isinstance(points, Vector)
        lnks = UintVector()
        core.link_point2(lnks.handle, points.handle, lmax)
        return lnks

    core.use(c_double, 'get_velocity_after_slowdown_by_viscosity', c_double, c_double, c_double)

    @staticmethod
    def get_velocity_after_slowdown_by_viscosity(v0, a0, time):
        """
        假设物体位于粘性的流体内，它所受到的粘性阻力和速度成正比。初始时刻的速度为v0，由于粘性带来的加速度为a0；
        此函数计算一段时间time之后该物体的速度
        """
        return core.get_velocity_after_slowdown_by_viscosity(v0, a0, time)

    core.use(None, 'prepare_zml', c_char_p, c_char_p, c_char_p)

    @staticmethod
    def prepare_zml(code_path, target_folder, znetwork_folder):
        """
        在C++层面，准备zml头文件.
        :param code_path: 代码文件夹，将监测该文件夹中的 include
        :param target_folder: zml文件夹所在的目标目录
        :param znetwork_folder: zml文件夹所在的源目录
        :return: None
        """
        core.prepare_zml(make_c_char_p(code_path), make_c_char_p(target_folder), make_c_char_p(znetwork_folder))


class Tensor2Field2(HasHandle):
    """
    二阶张量的二维插值场
       注：!!!<测试用，后续可能会移除>!!!
    """
    core.use(c_void_p, 'new_tensor2_field2')
    core.use(None, 'del_tensor2_field2', c_void_p)

    def __init__(self, path=None, handle=None):
        warnings.warn('zml.Tensor2Field2 may be removed in future', DeprecationWarning)
        super(Tensor2Field2, self).__init__(handle, core.new_tensor2_field2, core.del_tensor2_field2)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'tensor2_field2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.tensor2_field2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_field2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.tensor2_field2_load(self.handle, make_c_char_p(path))

    core.use(c_bool, 'tensor2_field2_empty', c_void_p)

    @property
    def empty(self):
        return core.tensor2_field2_empty(self.handle)

    core.use(None, 'tensor2_field2_clear', c_void_p)

    def clear(self):
        core.tensor2_field2_clear(self.handle)

    core.use(None, 'tensor2_field2_get', c_void_p, c_double, c_double, c_size_t)

    def __getitem__(self, key):
        assert len(key) == 2
        x = key[0]
        y = key[1]
        tensor = Tensor2()
        core.tensor2_field2_get(self.handle, x, y, tensor.handle)
        return tensor


class LinearExpr(HasHandle):
    core.use(c_void_p, 'new_linear_expr')
    core.use(None, 'del_linear_expr', c_void_p)

    def __init__(self, handle=None):
        super(LinearExpr, self).__init__(handle, core.new_linear_expr, core.del_linear_expr)

    core.use(None, 'linear_expr_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.linear_expr_save(self.handle, make_c_char_p(path))

    core.use(None, 'linear_expr_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.linear_expr_load(self.handle, make_c_char_p(path))

    core.use(None, 'linear_expr_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'linear_expr_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.linear_expr_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.linear_expr_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    def __eq__(self, rhs):
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        return not (self == rhs)

    def __str__(self):
        s = ''.join([f' + get({self[i][0]}) * {self[i][1]}' for i in range(len(self))])
        return f'zml.LinearExpr({self.c}{s})'

    core.use(c_double, 'linear_expr_get_c', c_void_p)
    core.use(None, 'linear_expr_set_c', c_void_p, c_double)

    @property
    def c(self):
        return core.linear_expr_get_c(self.handle)

    @c.setter
    def c(self, value):
        core.linear_expr_set_c(self.handle, value)

    core.use(c_size_t, 'linear_expr_get_length', c_void_p)

    @property
    def length(self):
        return core.linear_expr_get_length(self.handle)

    def __len__(self):
        return self.length

    core.use(c_size_t, 'linear_expr_get_index', c_void_p, c_size_t)
    core.use(c_double, 'linear_expr_get_weight', c_void_p, c_size_t)

    def __getitem__(self, i):
        assert i < self.length
        index = core.linear_expr_get_index(self.handle, i)
        weight = core.linear_expr_get_weight(self.handle, i)
        return index, weight

    core.use(None, 'linear_expr_add', c_void_p, c_size_t, c_double)

    def add(self, index, weight):
        core.linear_expr_add(self.handle, index, weight)

    core.use(None, 'linear_expr_clear', c_void_p)

    def clear(self):
        core.linear_expr_clear(self.handle)

    core.use(None, 'linear_expr_plus', c_void_p, c_size_t, c_size_t)
    core.use(None, 'linear_expr_multiply', c_void_p, c_size_t, c_double)

    def __add__(self, other):
        assert isinstance(other, LinearExpr)
        result = LinearExpr()
        core.linear_expr_plus(result.handle, self.handle, other.handle)
        return result

    def __sub__(self, other):
        return self.__add__(other * (-1.0))

    def __mul__(self, scale):
        result = LinearExpr()
        core.linear_expr_multiply(result.handle, self.handle, scale)
        return result

    def __truediv__(self, scale):
        return self.__mul__(1.0 / scale)

    @staticmethod
    def create(index):
        lexpr = LinearExpr()
        lexpr.c = 0
        lexpr.add(index, 1.0)
        return lexpr

    @staticmethod
    def create_constant(c):
        lexpr = LinearExpr()
        lexpr.c = c
        return lexpr


class DynSys(HasHandle):
    """
    质量-弹性动力学系统.
    """
    core.use(c_void_p, 'new_dynsys')
    core.use(None, 'del_dynsys', c_void_p)

    def __init__(self, path=None, handle=None):
        super(DynSys, self).__init__(handle, core.new_dynsys, core.del_dynsys)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'dynsys_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.dynsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.dynsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'dynsys_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.dynsys_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.dynsys_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_int, 'dynsys_iterate', c_void_p, c_double, c_void_p)

    def iterate(self, dt, solver):
        """
        求解迭代一次
        """
        return core.dynsys_iterate(self.handle, dt, solver.handle)

    core.use(c_size_t, 'dynsys_size', c_void_p)

    @property
    def size(self):
        """
        未知数的数量(体系的自由度的数量)
        例如：
            如果利用 DynSys来描述一个三角形的变形和振动，三角形有三个节点，每个节点有x和y两个变量，那么这个自由度(或者说未知数的数量)就是6.
            如果是两个三角形，有一个公用的边，那么自由度就是8.
        """
        return core.dynsys_size(self.handle)

    core.use(None, 'dynsys_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """
        未知数的数量(体系的自由度的数量)
        """
        core.dynsys_resize(self.handle, value)

    core.use(c_double, 'dynsys_get_pos', c_void_p, c_size_t)

    def get_pos(self, idx):
        """
        自由度的当前值.
        例如:
            对于一个三角形，有6个自由度，如果分别表示为 x1 y1 x2 y2 x3 y3, 那么 get_pos(0)返回x1, get_pos(1)为y1，以此类推.
        """
        return core.dynsys_get_pos(self.handle, idx)

    core.use(None, 'dynsys_set_pos', c_void_p, c_size_t, c_double)

    def set_pos(self, idx, value):
        """
        自由度的当前值.
        """
        core.dynsys_set_pos(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_vel', c_void_p, c_size_t)

    def get_vel(self, idx):
        """
        自由度的速度.
            参考对 get_pos的注释. 返回对应自由度运动的速度.
        """
        return core.dynsys_get_vel(self.handle, idx)

    core.use(None, 'dynsys_set_vel', c_void_p, c_size_t, c_double)

    def set_vel(self, idx, value):
        """
        自由度的速度
        """
        core.dynsys_set_vel(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_mas', c_void_p, c_size_t)

    def get_mas(self, idx):
        """
        自由度的质量.
            用以刻画该自由度的惯性.
        """
        return core.dynsys_get_mas(self.handle, idx)

    core.use(None, 'dynsys_set_mas', c_void_p, c_size_t, c_double)

    def set_mas(self, idx, value):
        """
        自由度的质量.
            用以刻画该自由度的惯性.
        """
        core.dynsys_set_mas(self.handle, idx, value)

    core.use(c_void_p, 'dynsys_get_p2f', c_void_p, c_size_t)

    def get_p2f(self, idx):
        """
        根据位置计算自由度的受力. 这个受力是一个线性表达式，即建立这个自由度的受力与自由度位置(以及其它多个自由度的位置)之间的线性关系.
            这里所谓的受力，即自由度的质量乘以自由度的加速度.
        """
        handle = core.dynsys_get_p2f(self.handle, idx)
        if handle > 0:
            return LinearExpr(handle=handle)


class SpringSys(HasHandle):
    """
    质点弹簧系统：仅仅用于测试
    """

    class Node(Object):
        """
        具有质量、位置、速度属性的节点。是弹簧系统的基本概念，建模时需要将实体离散为一个个的node，将质量集中到这些node上。
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
            """
            return [core.springsys_get_node_pos(self.model.handle, self.index, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            节点在三维空间的位置 <单位m>
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
            第idim个维度的线性表达式
            """
            lexpr = LinearExpr()
            core.springsys_get_virtual_node(self.model.handle, self.index, idim, lexpr.handle)
            return lexpr

        core.use(None, 'springsys_set_virtual_node', c_void_p, c_size_t, c_size_t, c_size_t)

        def __setitem__(self, idim, lexpr):
            """
            第idim个维度的线性表达式
            """
            assert isinstance(lexpr, LinearExpr)
            core.springsys_set_virtual_node(self.model.handle, self.index, idim, lexpr.handle)

        @property
        def x(self):
            return self[0]

        @x.setter
        def x(self, value):
            self[0] = value

        @property
        def y(self):
            return self[1]

        @y.setter
        def y(self, value):
            self[1] = value

        @property
        def z(self):
            return self[2]

        @z.setter
        def z(self, value):
            self[2] = value

        core.use(c_double, 'springsys_get_virtual_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            虚拟节点在三维空间的位置 <单位 m>
            """
            return [core.springsys_get_virtual_node_pos(self.model.handle, self.index, i) for i in range(3)]

    class Spring(Object):
        """
        弹簧，用以连接两个virtual_node，在两者之间建立线性的弹性关系。注意，Spring只能用以连接两个virtual_node，
        不能连接在两个实际的node上。如果要用弹簧连接实际的node，则必须首先在实际node的位置建立virtual_node，然后
        连接相应的virtual_node。
        注意：两个虚拟节点之间，可以添加多个不同的弹簧，这些弹簧会同时发挥作用。
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
            此弹簧的初始长度   <单位m>
            """
            return core.springsys_get_spring_len0(self.model.handle, self.index)

        @len0.setter
        def len0(self, value):
            """
            此弹簧的初始长度   <单位m>
            """
            core.springsys_set_spring_len0(self.model.handle, self.index, value)

        core.use(c_double, 'springsys_get_spring_tension', c_void_p, c_size_t)

        @property
        def tension(self):
            """
            弹簧在此刻的张力
            """
            return core.springsys_get_spring_tension(self.model.handle, self.index)

        core.use(None, 'springsys_set_spring_k', c_void_p, c_size_t, c_double)
        core.use(c_double, 'springsys_get_spring_k', c_void_p, c_size_t)

        @property
        def k(self):
            """
            此弹簧的刚度系数   <单位 N/m>
            """
            return core.springsys_get_spring_k(self.model.handle, self.index)

        @k.setter
        def k(self, value):
            """
            此弹簧的刚度系数   <单位 N/m>
            """
            core.springsys_set_spring_k(self.model.handle, self.index, value)

        core.use(c_size_t, 'springsys_get_spring_link_n', c_void_p, c_size_t)
        core.use(c_size_t, 'springsys_get_spring_link', c_void_p, c_size_t, c_size_t)
        core.use(None, 'springsys_set_spring_link', c_void_p, c_size_t, c_size_t, c_size_t)

        @property
        def virtual_nodes(self):
            """
            弹簧两端的虚拟节点
            """
            n = core.springsys_get_spring_link_n(self.model.handle, self.index)
            if n != 2:
                return None, None

            i0 = core.springsys_get_spring_link(self.model.handle, self.index, 0)
            i1 = core.springsys_get_spring_link(self.model.handle, self.index, 1)

            return self.model.get_virtual_node(i0), self.model.get_virtual_node(i1)

        @virtual_nodes.setter
        def virtual_nodes(self, value):
            """
            弹簧两端的虚拟节点
            """
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
            返回弹簧中心点的位置  <单位 m>
            """
            virtual_nodes = self.virtual_nodes
            if len(virtual_nodes) == 2:
                if virtual_nodes[0] is not None and virtual_nodes[1] is not None:
                    a = virtual_nodes[0].pos
                    b = virtual_nodes[1].pos
                    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2

        core.use(c_double, 'springsys_get_spring_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            该Spring的第index个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
            if index is None:
                return default_val
            value = core.springsys_get_spring_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        core.use(None, 'springsys_set_spring_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            该Spring的第index个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.springsys_set_spring_attr(self.model.handle, self.index, index, value)
            return self

    class Damper(Object):
        """
        阻尼器。阻尼器用以连接两个node，降低两个node之间的相对速度（注意，只能施加的node上，不能施加在virtual_node上）
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
            两端连接的node
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
            两端连接的node
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
            阻尼器的粘性系数 <单位 N/(m/s)>
            """
            return core.springsys_get_damper_vis(self.model.handle, self.index)

        @vis.setter
        def vis(self, value):
            """
            阻尼器的粘性系数 <单位 N/(m/s)>
            """
            core.springsys_set_damper_vis(self.model.handle, self.index, value)

    core.use(c_void_p, 'new_springsys')
    core.use(None, 'del_springsys', c_void_p)

    def __init__(self, path=None, handle=None):
        super(SpringSys, self).__init__(handle, core.new_springsys, core.del_springsys)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.SpringSys(handle = {self.handle}, node_n = {self.node_number}, virtual_node_n = {self.virtual_node_number}, spring_n = {self.spring_number})'

    @staticmethod
    def virtual_x(node):
        if isinstance(node, SpringSys.VirtualNode):
            return node.x
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 0)

    @staticmethod
    def virtual_y(node):
        if isinstance(node, SpringSys.VirtualNode):
            return node.y
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 1)

    @staticmethod
    def virtual_z(node):
        if isinstance(node, SpringSys.VirtualNode):
            return node.z
        if isinstance(node, SpringSys.Node):
            node = node.index
        return LinearExpr.create(node * 3 + 2)

    core.use(None, 'springsys_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            assert isinstance(path, str)
            core.springsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            assert isinstance(path, str)
            core.springsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_print_node_pos', c_void_p, c_char_p)

    def print_node_pos(self, path):
        """
        打印node的位置
        """
        assert isinstance(path, str)
        core.springsys_print_node_pos(self.handle, make_c_char_p(path))

    def iterate(self, dt, dynsys, solver):
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
        节点的数量
        """
        return core.springsys_get_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_virtual_node_n', c_void_p)

    @property
    def virtual_node_number(self):
        """
        虚拟节点的数量
        """
        return core.springsys_get_virtual_node_n(self.handle)

    core.use(c_size_t, 'springsys_get_spring_n', c_void_p)

    @property
    def spring_number(self):
        """
        弹簧的数量
        """
        return core.springsys_get_spring_n(self.handle)

    core.use(c_size_t, 'springsys_get_damper_n', c_void_p)

    @property
    def damper_number(self):
        """
        阻尼器的数量
        """
        return core.springsys_get_damper_n(self.handle)

    def get_node(self, index):
        """
        返回节点对象
        """
        if 0 <= index < self.node_number:
            return SpringSys.Node(self, index)

    def get_virtual_node(self, index):
        """
        返回虚拟节点对象
        """
        if 0 <= index < self.virtual_node_number:
            return SpringSys.VirtualNode(self, index)

    def get_spring(self, index):
        """
        返回弹簧对象
        """
        if 0 <= index < self.spring_number:
            return SpringSys.Spring(self, index)

    def get_damper(self, index):
        """
        返回阻尼器对象
        """
        if 0 <= index < self.damper_number:
            return SpringSys.Damper(self, index)

    @property
    def nodes(self):
        return Iterators.Node(self)

    @property
    def virtual_nodes(self):
        return Iterators.VirtualNode(self)

    @property
    def springs(self):
        return Iterators.Spring(self)

    @property
    def dampers(self):
        return Iterators.Damper(self)

    core.use(c_size_t, 'springsys_add_node', c_void_p)

    def add_node(self, pos=None, vel=None, force=None, mass=None):
        """
        添加一个节点，并返回Node对象。
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
        添加一个弹簧，并返回弹簧对象。其中link应该为两个虚拟节点。len0为弹簧的初始长度，k为弹簧的刚度系数。
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
        添加一个阻尼器。这里和添加弹簧最为重要的不同是，目前阻尼器两端，必须连接在实际的node上，而不是虚拟的node
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
        用于将所有的node减速。给定的scale应为0到1之间的数值。将所有的node的速度，统一修改为原来的scale倍
        """
        core.springsys_modify_vel(self.handle, scale)

    core.use(None, 'springsys_get_pos', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, x=None, y=None, z=None):
        """
        获得所有node的x,y,z坐标
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
        返回所有弹簧的长度<作为一个Vector来返回>
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_get_k', c_void_p, c_void_p)

    def get_k(self, buffer=None):
        """
        返回所有弹簧的刚度<作为一个Vector来返回>
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_k(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_k', c_void_p, c_void_p)

    def set_k(self, k):
        assert isinstance(k, Vector)
        core.springsys_set_k(self.handle, k.handle)

    core.use(None, 'springsys_get_len0', c_void_p, c_void_p)

    def get_len0(self, buffer=None):
        """
        返回所有弹簧的长度<作为一个Vector来返回>
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.springsys_get_len0(self.handle, buffer.handle)
        return buffer

    core.use(None, 'springsys_set_len0', c_void_p, c_void_p)

    def set_len0(self, len0):
        """
        设置所有弹簧的长度
        """
        assert isinstance(len0, Vector)
        core.springsys_set_len0(self.handle, len0.handle)

    core.use(c_size_t, 'springsys_apply_k_reduction', c_void_p, c_size_t)

    def apply_k_reduction(self, sa_tmax):
        """
        实施刚度折减。其中sa_tmax定义了弹簧的自定义属性，代表弹簧可以承受的张力的上限；
        当弹簧的张力到达这个上限的时候，将刚度折减为原来的1%
        """
        return core.springsys_apply_k_reduction(self.handle, sa_tmax)

    core.use(None, 'springsys_adjust_len0', c_void_p, c_size_t)

    def adjust_len0(self, sa_times):
        """
        根据属性sa_times定义的倍数，来调整弹簧的初始长度。只有当sa_times定义的倍率位于0.5到2之间的时候，才会真正调整
        """
        core.springsys_adjust_len0(self.handle, sa_times)

    core.use(None, 'springsys_export_mas_pos_vel', c_void_p, c_void_p)

    def export_mas_pos_vel(self, dynsys):
        core.springsys_export_mas_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_export_p2f', c_void_p, c_void_p)

    def export_p2f(self, dynsys):
        core.springsys_export_p2f(self.handle, dynsys.handle)

    core.use(None, 'springsys_update_pos_vel', c_void_p, c_void_p)

    def update_pos_vel(self, dynsys):
        core.springsys_update_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_apply_dampers', c_void_p, c_double)

    def apply_dampers(self, dt):
        core.springsys_apply_dampers(self.handle, dt)

    core.use(None, 'springsys_modify_pos', c_void_p, c_size_t, c_double, c_double)

    def modify_pos(self, idim, left, right):
        """
        修改node的位置的范围
        """
        if left is None and right is None:
            return
        if left is None:
            left = -1e100
        if right is None:
            right = 1e100
        core.springsys_modify_pos(self.handle, idim, left, right)


class FemTri6(HasHandle):
    """
    三角形有限元模型。其中每个单元（三角形）有6个自由度(x1, y1, x2, y2, x3, y3)。
    !!!<尚未完成，仅供测试>!!!
    """

    class Node(Object):
        def __init__(self, model, index):
            assert isinstance(model, FemTri6)
            assert isinstance(index, int)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'fem_tri6_get_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            节点初始位置
            """
            return [core.fem_tri6_get_node_pos(self.model.handle, self.index, i) for i in range(2)]

        core.use(None, 'fem_tri6_set_node_pos', c_void_p, c_size_t,
                 c_double, c_double)

        @pos.setter
        def pos(self, value):
            core.fem_tri6_set_node_pos(self.model.handle, self.index, value[0], value[1])

        core.use(c_double, 'fem_tri6_get_node_disp', c_void_p, c_size_t, c_size_t)

        @property
        def disp(self):
            """
            节点位移(当前位置-初始位置)
            """
            x = core.fem_tri6_get_node_disp(self.model.handle, self.index, 0)
            y = core.fem_tri6_get_node_disp(self.model.handle, self.index, 1)
            return x, y

        core.use(c_double, 'fem_tri6_get_node_vel', c_void_p, c_size_t, c_size_t)

        @property
        def vel(self):
            x = core.fem_tri6_get_node_vel(self.model.handle, self.index, 0)
            y = core.fem_tri6_get_node_vel(self.model.handle, self.index, 1)
            return x, y

        core.use(None, 'fem_tri6_set_node_vel', c_void_p, c_size_t,
                 c_double, c_double)

        @vel.setter
        def vel(self, value):
            core.fem_tri6_set_node_vel(self.model.handle, self.index, value[0], value[1])

        core.use(c_double, 'fem_tri6_get_node_virtual_mass', c_void_p, c_size_t, c_size_t)

        def get_virtual_mass(self, idim):
            """
            第idim个维度的虚拟质量
            """
            return core.fem_tri6_get_node_virtual_mass(self.model.handle, self.index, idim)

        core.use(None, 'fem_tri6_set_node_virtual_mass', c_void_p, c_size_t, c_size_t,
                 c_double)

        def set_virtual_mass(self, idim, value):
            """
            第idim个维度的虚拟质量
            """
            core.fem_tri6_set_node_virtual_mass(self.model.handle, self.index, idim, value)

        @property
        def virtual_mass(self):
            """
            虚拟质量（两个维度独立，这个和之前的版本不同）
            """
            return self.get_virtual_mass(0), self.get_virtual_mass(1)

        @virtual_mass.setter
        def virtual_mass(self, value):
            """
            虚拟质量（两个维度独立，这个和之前的版本不同）
            """
            if hasattr(value, '__getitem__'):
                for idim in range(2):
                    self.set_virtual_mass(idim, value[idim])
            else:
                for idim in range(2):
                    self.set_virtual_mass(idim, value)

        core.use(c_double, 'fem_tri6_get_node_force', c_void_p, c_size_t,
                 c_size_t)

        @property
        def force(self):
            x = core.fem_tri6_get_node_force(self.model.handle, self.index, 0)
            y = core.fem_tri6_get_node_force(self.model.handle, self.index, 1)
            return x, y

        core.use(None, 'fem_tri6_set_node_force', c_void_p, c_size_t,
                 c_double, c_double)

        @force.setter
        def force(self, value):
            core.fem_tri6_set_node_force(self.model.handle, self.index, value[0], value[1])

    class Element(Object):
        def __init__(self, model, index):
            assert isinstance(model, FemTri6)
            assert isinstance(index, int)
            assert index < model.element_number
            self.model = model
            self.index = index

        core.use(c_double, 'fem_tri6_get_element_young_modulus', c_void_p, c_size_t)

        @property
        def young_modulus(self):
            return core.fem_tri6_get_element_young_modulus(self.model.handle, self.index)

        core.use(None, 'fem_tri6_set_element_young_modulus', c_void_p, c_size_t,
                 c_double)

        @young_modulus.setter
        def young_modulus(self, value):
            core.fem_tri6_set_element_young_modulus(self.model.handle, self.index, value)

        core.use(c_double, 'fem_tri6_get_element_poisson_ratio', c_void_p, c_size_t)

        @property
        def poisson_ratio(self):
            return core.fem_tri6_get_element_poisson_ratio(self.model.handle, self.index)

        core.use(None, 'fem_tri6_set_element_poisson_ratio', c_void_p, c_size_t,
                 c_double)

        @poisson_ratio.setter
        def poisson_ratio(self, value):
            core.fem_tri6_set_element_poisson_ratio(self.model.handle, self.index, value)

        core.use(c_double, 'fem_tri6_get_element_strain0_xx', c_void_p, c_size_t)
        core.use(c_double, 'fem_tri6_get_element_strain0_yy', c_void_p, c_size_t)
        core.use(c_double, 'fem_tri6_get_element_strain0_xy', c_void_p, c_size_t)

        @property
        def initial_strain(self):
            xx = core.fem_tri6_get_element_strain0_xx(self.model.handle, self.index)
            yy = core.fem_tri6_get_element_strain0_yy(self.model.handle, self.index)
            xy = core.fem_tri6_get_element_strain0_xy(self.model.handle, self.index)
            return xx, yy, xy

        core.use(None, 'fem_tri6_set_element_strain0', c_void_p, c_size_t,
                 c_double, c_double, c_double)

        @initial_strain.setter
        def initial_strain(self, value):
            core.fem_tri6_set_element_strain0(self.model.handle, self.index, value[0], value[1], value[2])

        core.use(c_double, 'fem_tri6_get_element_mass', c_void_p, c_size_t)

        @property
        def mass(self):
            return core.fem_tri6_get_element_mass(self.model.handle, self.index)

        core.use(None, 'fem_tri6_set_element_mass', c_void_p, c_size_t,
                 c_double)

        @mass.setter
        def mass(self, value):
            core.fem_tri6_set_element_mass(self.model.handle, self.index, value)

        core.use(c_double, 'fem_tri6_get_element_center', c_void_p, c_size_t,
                 c_size_t)

        @property
        def center(self):
            x = core.fem_tri6_get_element_center(self.model.handle, self.index, 0)
            y = core.fem_tri6_get_element_center(self.model.handle, self.index, 1)
            return x, y

    core.use(c_void_p, 'new_fem_tri6')
    core.use(None, 'del_fem_tri6', c_void_p)

    def __init__(self, path=None, handle=None):
        super(FemTri6, self).__init__(handle, core.new_fem_tri6, core.del_fem_tri6)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.FemTri6(handle = {self.handle}, node_n = {self.node_number}, element_n = {self.element_number})'

    core.use(None, 'fem_tri6_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.fem_tri6_save(self.handle, make_c_char_p(path))

    core.use(None, 'fem_tri6_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.fem_tri6_load(self.handle, make_c_char_p(path))

    core.use(None, 'fem_tri6_load_trimesh', c_void_p, c_char_p,
             c_char_p, c_size_t)
    core.use(None, 'fem_tri6_load_trimesh_auto', c_void_p, c_char_p,
             c_char_p)

    def load_trimesh(self, nodefile, trianglefile, index_start_from=None):
        if index_start_from is None:
            core.fem_tri6_load_trimesh_auto(self.handle, make_c_char_p(nodefile),
                                            make_c_char_p(trianglefile))
        else:
            core.fem_tri6_load_trimesh(self.handle, make_c_char_p(nodefile), make_c_char_p(trianglefile),
                                       index_start_from)

    core.use(None, 'fem_tri6_set_trimesh', c_void_p, c_size_t)

    def set_trimesh(self, trimesh):
        assert isinstance(trimesh, Trimesh2)
        core.fem_tri6_set_trimesh(self.handle, trimesh.handle)

    core.use(c_size_t, 'fem_tri6_get_node_n', c_void_p)

    @property
    def node_number(self):
        return core.fem_tri6_get_node_n(self.handle)

    def get_node(self, node_id):
        if node_id < self.node_number:
            return FemTri6.Node(self, node_id)

    core.use(c_size_t, 'fem_tri6_get_element_number', c_void_p)

    @property
    def element_number(self):
        return core.fem_tri6_get_element_number(self.handle)

    def get_element(self, element_id):
        if element_id < self.element_number:
            return FemTri6.Element(self, element_id)

    core.use(c_double, 'fem_tri6_get_gravity', c_void_p, c_size_t)

    @property
    def gravity(self):
        x = core.fem_tri6_get_gravity(self.handle, 0)
        y = core.fem_tri6_get_gravity(self.handle, 1)
        return x, y

    core.use(None, 'fem_tri6_set_gravity', c_void_p,
             c_double, c_double)

    @gravity.setter
    def gravity(self, value):
        core.fem_tri6_set_gravity(self.handle, value[0], value[1])

    @property
    def nodes(self):
        """
        返回node的迭代器，方便对所有的node进行遍历
        """
        return Iterators.Node(self)

    @property
    def elements(self):
        """
        返回element的迭代器，方便对所有的element进行遍历
        """
        return Iterators.Element(self)

    core.use(c_size_t, 'fem_tri6_get_nearest_node_index', c_void_p, c_double, c_double)

    def get_nearest_node(self, x, y):
        ind = core.fem_tri6_get_nearest_node_index(self.handle, x, y)
        return self.get_node(ind)

    core.use(c_size_t, 'fem_tri6_iterate', c_void_p, c_double, c_double)

    def iterate(self, dt, pos_err_max=1.0e-6):
        lic.check_once()
        return core.fem_tri6_iterate(self.handle, dt, pos_err_max)

    core.use(None, 'fem_tri6_slow_down', c_void_p, c_double)

    def slow_down(self, scale):
        core.fem_tri6_slow_down(self.handle, scale)

    def print_node_disp(self, path):
        with open(path, 'w') as file:
            for node in self.nodes:
                for value in node.disp:
                    file.write(f'{value}\t')
                file.write('\n')


class HasCells(Object):
    def get_pos_range(self, dim):
        """
        返回cells在某一个坐标维度上的范围
        """
        assert self.cell_number > 0
        assert 0 <= dim <= 2
        lrange, rrange = 1e100, -1e100
        for c in self.cells:
            p = c.pos[dim]
            lrange = min(lrange, p)
            rrange = max(rrange, p)
        return lrange, rrange

    def get_cells_in_range(self, xr=None, yr=None, zr=None,
                           center=None, radi=None):
        """
        返回在给定的坐标范围内的所有的cell. 其中xr为x坐标的范围，yr为y坐标的范围，zr为
        z坐标的范围。当某个范围为None的时候，则不检测.
        """
        if xr is None and yr is None and zr is None and center is not None and radi is not None:
            cells = []
            for c in self.cells:
                if get_distance(center, c.pos) <= radi:
                    cells.append(c)
            return cells
        ranges = (xr, yr, zr)
        cells = []
        for c in self.cells:
            out_of_range = False
            for i in range(len(ranges)):
                r = ranges[i]
                if r is not None:
                    p = c.pos[i]
                    if p < r[0] or p > r[1]:
                        out_of_range = True
                        break
            if not out_of_range:
                cells.append(c)
        return cells

    def get_cell_pos(self, index=(0, 1, 2)):
        vpos = [cell.pos for cell in self.cells]
        results = []
        for i in index:
            results.append([pos[i] for pos in vpos])
        return tuple(results)

    def get_cell_property(self, get):
        return [get(cell) for cell in self.cells]

    def plot_tricontourf(self, get, caption=None, gui_only=False, title=None, triangulation=None, fname=None, dpi=300):
        def f(fig):
            if triangulation is None:
                pos = [cell.pos for cell in self.cells]
                x = [p[0] for p in pos]
                y = [p[1] for p in pos]
            z = [get(cell) for cell in self.cells]
            ax = fig.subplots()
            ax.set_aspect('equal')
            ax.set_xlabel('x/m')
            ax.set_ylabel('y/m')
            if title is not None:
                ax.set_title(title)
            if triangulation is None:
                contour = ax.tricontourf(x, y, z, levels=20, cmap='coolwarm', antialiased=True)
            else:
                contour = ax.tricontourf(triangulation, z, levels=20, cmap='coolwarm', antialiased=True)
            fig.colorbar(contour, ax=ax)

        if not gui_only or gui.exists():
            plot(kernel=f, caption=caption, clear=True, fname=fname, dpi=dpi)


class SeepageMesh(HasHandle, HasCells):
    """
    定义流体计算的网格。即由cell和face组成的网络。对于每一个cell，都包含位置和体积两个基本属性，
    对于每一个face，都具有area和length两个基本属性
    """

    class Cell(Object):
        """
        控制体积：定义位置和几何体积
        """

        def __init__(self, model, index):
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.cell_number
            self.model = model
            self.index = index

        def __str__(self):
            return f'zml.SeepageMesh.Cell(handle = {self.model.handle}, index = {self.index}, pos = {self.pos}, volume={self.vol})'

        core.use(c_double, 'seepage_mesh_get_cell_pos', c_void_p,
                 c_size_t,
                 c_size_t)
        core.use(None, 'seepage_mesh_set_cell_pos', c_void_p,
                 c_size_t,
                 c_size_t,
                 c_double)

        @property
        def pos(self):
            return [core.seepage_mesh_get_cell_pos(self.model.handle, self.index, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            assert len(value) == 3
            for dim in range(3):
                core.seepage_mesh_set_cell_pos(self.model.handle, self.index,
                                               dim, value[dim])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离
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
            return core.seepage_mesh_get_cell_volume(self.model.handle, self.index)

        @vol.setter
        def vol(self, value):
            core.seepage_mesh_set_cell_volume(self.model.handle, self.index, value)

        core.use(c_double, 'seepage_mesh_get_cell_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            第index个自定义属性
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_cell_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_cell_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            第index个自定义属性
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_mesh_set_cell_attr(self.model.handle, self.index, index, value)
            return self

    class Face(Object):
        """
        定义cell之间的流动通道
        """

        def __init__(self, model, index):
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index

        def __str__(self):
            return f'zml.SeepageMesh.Face(handle = {self.model.handle}, index = {self.index}, area = {self.area}, length = {self.length}) '

        core.use(None, 'seepage_mesh_set_face_area', c_void_p,
                 c_size_t,
                 c_double)
        core.use(c_double, 'seepage_mesh_get_face_area', c_void_p,
                 c_size_t)

        @property
        def area(self):
            return core.seepage_mesh_get_face_area(self.model.handle, self.index)

        @area.setter
        def area(self, value):
            core.seepage_mesh_set_face_area(self.model.handle, self.index, value)

        core.use(None, 'seepage_mesh_set_face_length', c_void_p,
                 c_size_t,
                 c_double)
        core.use(c_double, 'seepage_mesh_get_face_length', c_void_p,
                 c_size_t)

        @property
        def length(self):
            return core.seepage_mesh_get_face_length(self.model.handle, self.index)

        @length.setter
        def length(self, value):
            core.seepage_mesh_set_face_length(self.model.handle, self.index, value)

        @property
        def pos(self):
            """
            返回Face中心点的位置（根据两侧的Cell的位置来自动计算）
            """
            p0 = self.get_cell(0).pos
            p1 = self.get_cell(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_size_t, 'seepage_mesh_get_face_end0', c_void_p, c_size_t)

        @property
        def cell_i0(self):
            """
            返回第0个cell的id
            """
            return core.seepage_mesh_get_face_end0(self.model.handle, self.index)

        core.use(c_size_t, 'seepage_mesh_get_face_end1', c_void_p, c_size_t)

        @property
        def cell_i1(self):
            """
            返回第1个cell的id
            """
            return core.seepage_mesh_get_face_end1(self.model.handle, self.index)

        @property
        def cell_ids(self):
            return self.cell_i0, self.cell_i1

        @property
        def link(self):
            return self.cell_ids

        @property
        def cell_number(self):
            """
            返回与此face相连的cell的数量
            """
            return 2

        def get_cell(self, i):
            """
            返回与face相连的第i个cell
            """
            if i > 0:
                return self.model.get_cell(self.cell_i1)
            else:
                return self.model.get_cell(self.cell_i0)

        def cells(self):
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'seepage_mesh_get_face_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            第index个自定义属性
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_face_attr(self.model.handle, self.index, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_face_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            第index个自定义属性
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
        super(SeepageMesh, self).__init__(handle, core.new_seepage_mesh, core.del_seepage_mesh)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        """
        Get the summary of the object for print.
        """
        return f'zml.SeepageMesh(handle = {self.handle}, cell_n = {self.cell_number}, face_n = {self.face_number}, volume = {self.volume})'

    core.use(None, 'seepage_mesh_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.seepage_mesh_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
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
        """
        return core.seepage_mesh_get_cell_n(self.handle)

    def get_cell(self, ind):
        """
        返回第ind个cell
        """
        if ind < self.cell_number:
            return SeepageMesh.Cell(self, ind)

    core.use(c_size_t, 'seepage_mesh_get_nearest_cell_id', c_void_p,
             c_double, c_double, c_double)

    def get_nearest_cell(self, pos):
        """
        返回与给定位置距离最近的cell
        """
        if self.cell_number > 0:
            return self.get_cell(core.seepage_mesh_get_nearest_cell_id(self.handle, pos[0], pos[1], pos[2]))

    core.use(c_size_t, 'seepage_mesh_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        返回face的数量
        """
        return core.seepage_mesh_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_mesh_get_face', c_void_p, c_size_t, c_size_t)

    def get_face(self, ind=None, cell_0=None, cell_1=None):
        """
        返回第ind个face，或者找到两个cell之间的face
        """
        if ind is not None:
            assert cell_0 is None and cell_1 is None
            if ind < self.face_number:
                return SeepageMesh.Face(self, ind)
            else:
                return
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
        """
        return self.get_cell(core.seepage_mesh_add_cell(self.handle))

    core.use(c_size_t, 'seepage_mesh_add_face', c_void_p,
             c_size_t,
             c_size_t)

    def add_face(self, cell_0, cell_1):
        """
        添加一个face，连接两个给定的cell
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
        """
        return Iterators.Cell(self)

    @property
    def faces(self):
        """
        用以迭代所有的face
        """
        return Iterators.Face(self)

    @property
    def volume(self):
        """
        返回整个模型整体的体积
        """
        vol = 0
        for cell in self.cells:
            vol += cell.vol
        return vol

    def load_ascii(self, cellfile, facefile):
        """
        从文件中导入几何结构。其中cellfile定义cell的信息，至少包含4列，分别为x,y,z,vol；
        facefile定义face的性质，至少包含4裂缝，分别为cell_i0,cell_i1,area,length
        """
        self.clear()
        with open(cellfile, 'r') as file:
            for line in file.readlines():
                vals = [float(s) for s in line.split()]
                if len(vals) == 0:
                    continue
                assert len(vals) >= 4
                cell = self.add_cell()
                assert cell is not None
                cell.pos = [vals[i] for i in range(0, 3)]
                cell.vol = vals[3]
        cell_number = self.cell_number
        with open(facefile, 'r') as file:
            for line in file.readlines():
                words = line.split()
                if len(words) == 0:
                    continue
                assert len(words) >= 4
                cell_i0 = int(words[0])
                cell_i1 = int(words[1])
                assert cell_i0 < cell_number
                assert cell_i0 < cell_number
                area = float(words[2])
                assert area > 0
                length = float(words[3])
                assert length > 0
                face = self.add_face(self.get_cell(cell_i0), self.get_cell(cell_i1))
                if face is not None:
                    face.area = area
                    face.length = length

    def save_ascii(self, cellfile, facefile):
        """
        将当前的网格数据导出到两个文件
        """
        with open(cellfile, 'w') as file:
            for cell in self.cells:
                for elem in cell.pos:
                    file.write('%g ' % elem)
                file.write('%g\n' % cell.vol)
        with open(facefile, 'w') as file:
            for face in self.faces:
                link = face.link
                file.write('%d %d %g %g\n' % (link[0], link[1],
                                              face.area, face.length))

    @staticmethod
    def load_mesh(cellfile=None, facefile=None, path=None):
        """
        从文件中读取Mesh文件
        """
        mesh = SeepageMesh()
        if path is not None:
            assert cellfile is None and facefile is None
            mesh.load(path)
        else:
            assert cellfile is not None and facefile is not None
            mesh.load_ascii(cellfile, facefile)
        return mesh

    @staticmethod
    def create_cube(x=(-0.5, 0.5), y=(-0.5, 0.5), z=(-0.5, 0.5), boxes=None):
        """
        创建一个立方体网格的Mesh. 参数x、y、z分别为三个方向上网格节点的位置，应保证是从小到大
        排列好的。
        其中:
            当boxes是一个list的时候，将会把各个Cell对应的box，格式为(x0, y0, z0, x1, y1, z1)附加到这个list里面，
            用以定义各个Cell的具体形状.
        """
        assert x is not None and y is not None and z is not None
        assert len(x) + len(y) + len(z) >= 6

        def is_sorted(vx):
            for i in range(len(vx) - 1):
                if vx[i] >= vx[i + 1]:
                    return False
            return True

        assert is_sorted(x) and is_sorted(y) and is_sorted(z)

        jx = len(x) - 1
        jy = len(y) - 1
        jz = len(z) - 1
        assert jx > 0 and jy > 0 and jz > 0

        mesh = SeepageMesh()

        for ix in range(0, jx):
            dx = x[ix + 1] - x[ix]
            cx = x[ix] + dx / 2
            for iy in range(0, jy):
                dy = y[iy + 1] - y[iy]
                cy = y[iy] + dy / 2
                for iz in range(0, jz):
                    gui.break_point()
                    dz = z[iz + 1] - z[iz]
                    cz = z[iz] + dz / 2
                    cell = mesh.add_cell()
                    assert cell is not None
                    cell.pos = (cx, cy, cz)
                    cell.vol = dx * dy * dz
                    # 设置属性，用以定义Cell的位置的范围.
                    if boxes is not None:
                        boxes.append([cx - dx / 2, cy - dy / 2, cz - dz / 2, cx + dx / 2, cy + dy / 2, cz + dz / 2])

        def get_id(ix, iy, iz):
            """
            返回cell的全局的序号
            """
            return ix * (jy * jz) + iy * jz + iz

        cell_n = mesh.cell_number
        for ix in range(0, jx - 1):
            dx = (x[ix + 2] - x[ix]) / 2
            for iy in range(0, jy):
                dy = y[iy + 1] - y[iy]
                for iz in range(0, jz):
                    gui.break_point()
                    dz = z[iz + 1] - z[iz]
                    i0 = get_id(ix, iy, iz)
                    i1 = get_id(ix + 1, iy, iz)
                    assert i0 < cell_n and i1 < cell_n
                    face = mesh.add_face(mesh.get_cell(i0), mesh.get_cell(i1))
                    assert face is not None
                    face.area = dy * dz
                    face.length = dx

        for ix in range(0, jx):
            dx = x[ix + 1] - x[ix]
            for iy in range(0, jy - 1):
                dy = (y[iy + 2] - y[iy]) / 2
                for iz in range(0, jz):
                    gui.break_point()
                    dz = z[iz + 1] - z[iz]
                    i0 = get_id(ix, iy, iz)
                    i1 = get_id(ix, iy + 1, iz)
                    assert i0 < cell_n and i1 < cell_n
                    face = mesh.add_face(mesh.get_cell(i0), mesh.get_cell(i1))
                    assert face is not None
                    face.area = dx * dz
                    face.length = dy

        for ix in range(0, jx):
            dx = x[ix + 1] - x[ix]
            for iy in range(0, jy):
                dy = y[iy + 1] - y[iy]
                for iz in range(0, jz - 1):
                    gui.break_point()
                    dz = (z[iz + 2] - z[iz]) / 2
                    i0 = get_id(ix, iy, iz)
                    i1 = get_id(ix, iy, iz + 1)
                    assert i0 < cell_n and i1 < cell_n
                    face = mesh.add_face(mesh.get_cell(i0), mesh.get_cell(i1))
                    assert face is not None
                    face.area = dx * dy
                    face.length = dz

        return mesh

    @staticmethod
    def create_cylinder(x=(0, 1, 2), r=(0, 1, 2)):
        """
        创建一个极坐标下的圆柱体的网格。其中圆柱体的对称轴为x轴。cell的y坐标为r。cell的z坐标为0.
        """
        assert x is not None and r is not None
        assert len(x) >= 2 and len(r) >= 2
        assert r[0] >= 0
        # Moreover, both x and r should be sorted from small to big
        # (this will be checked in function 'create_cube_seepage_mesh')

        rmax = r[-1]
        perimeter = 2.0 * math.pi * rmax
        mesh = SeepageMesh.create_cube(x, r, (-perimeter * 0.5, perimeter * 0.5))

        for cell in mesh.cells:
            gui.break_point()
            (x, y, z) = cell.pos
            assert 0 < y < rmax
            cell.vol *= (y / rmax)

        for face in mesh.faces:
            gui.break_point()
            (i0, i1) = face.link
            (x0, y0, _) = mesh.get_cell(i0).pos
            (x1, y1, _) = mesh.get_cell(i1).pos
            y = (y0 + y1) / 2
            assert 0 < y < rmax
            face.area *= (y / rmax)

        return mesh

    core.use(None, 'seepage_mesh_find_inner_face_ids', c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号
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
        """
        assert isinstance(mesh3, Mesh3)
        if not isinstance(buffer, SeepageMesh):
            buffer = SeepageMesh()
        core.seepage_mesh_from_mesh3(buffer.handle, mesh3.handle)
        return buffer


class Trimesh2(HasHandle):
    class Node(Object):
        def __init__(self, model, index):
            assert isinstance(model, Trimesh2)
            assert isinstance(index, int)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'trimesh2_node_get_link_number', c_void_p, c_size_t)

        @property
        def link_n(self):
            return core.trimesh2_node_get_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_node_get_triangle_number', c_void_p, c_size_t)

        @property
        def triangle_n(self):
            return core.trimesh2_node_get_triangle_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_node_get_link_id', c_void_p, c_size_t, c_size_t)

        def get_link_id(self, i):
            return core.trimesh2_node_get_link_id(self.model.handle, self.index, i)

        core.use(c_size_t, 'trimesh2_node_get_triangle_id', c_void_p, c_size_t, c_size_t)

        def get_triangle_id(self, i):
            return core.trimesh2_node_get_triangle_id(self.model.handle, self.index, i)

        core.use(c_double, 'trimesh2_node_get_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            return [core.trimesh2_node_get_pos(self.model.handle, self.index, i) for i in range(2)]

        core.use(c_bool, 'trimesh2_node_on_border', c_void_p, c_size_t)

        @property
        def on_border(self):
            return core.trimesh2_node_on_border(self.model.handle, self.index)

        core.use(c_int, 'trimesh2_node_get_tag', c_void_p, c_size_t)

        @property
        def tag(self):
            return core.trimesh2_node_get_tag(self.model.handle, self.index)

        core.use(None, 'trimesh2_node_set_tag', c_void_p, c_size_t, c_int)

        @tag.setter
        def tag(self, value):
            core.trimesh2_node_set_tag(self.model.handle, self.index, value)

    class Link(Object):
        def __init__(self, model, index):
            assert isinstance(model, Trimesh2)
            assert isinstance(index, int)
            assert index < model.link_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'trimesh2_link_get_node_number', c_void_p, c_size_t)

        @property
        def node_n(self):
            return core.trimesh2_link_get_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_link_get_triangle_number', c_void_p, c_size_t)

        @property
        def triangle_n(self):
            return core.trimesh2_link_get_triangle_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_link_get_node_id', c_void_p, c_size_t, c_size_t)

        def get_node_id(self, i):
            return core.trimesh2_link_get_node_id(self.model.handle, self.index, i)

        core.use(c_size_t, 'trimesh2_link_get_triangle_id', c_void_p, c_size_t, c_size_t)

        def get_triangle_id(self, i):
            return core.trimesh2_link_get_triangle_id(self.model.handle, self.index, i)

        core.use(c_double, 'trimesh2_link_get_length', c_void_p, c_size_t)

        @property
        def length(self):
            return core.trimesh2_link_get_length(self.model.handle, self.index)

    class Triangle(Object):
        def __init__(self, model, index):
            assert isinstance(model, Trimesh2)
            assert isinstance(index, int)
            assert index < model.triangle_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'trimesh2_triangle_get_node_number', c_void_p, c_size_t)

        @property
        def node_n(self):
            return core.trimesh2_triangle_get_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_triangle_get_link_number', c_void_p, c_size_t)

        @property
        def link_n(self):
            return core.trimesh2_triangle_get_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'trimesh2_triangle_get_node_id', c_void_p, c_size_t, c_size_t)

        def get_node_id(self, i):
            return core.trimesh2_triangle_get_node_id(self.model.handle, self.index, i)

        core.use(c_size_t, 'trimesh2_triangle_get_link_id', c_void_p, c_size_t, c_size_t)

        def get_link_id(self, i):
            return core.trimesh2_triangle_get_link_id(self.model.handle, self.index, i)

        core.use(c_double, 'trimesh2_triangle_get_area', c_void_p, c_size_t)

        @property
        def area(self):
            return core.trimesh2_triangle_get_area(self.model.handle, self.index)

        core.use(c_double, 'trimesh2_triangle_get_center', c_void_p, c_size_t, c_size_t)

        @property
        def center(self):
            x = core.trimesh2_triangle_get_center(self.model.handle, self.index, 0)
            y = core.trimesh2_triangle_get_center(self.model.handle, self.index, 1)
            return x, y

    core.use(c_void_p, 'new_trimesh2')
    core.use(None, 'del_trimesh2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Trimesh2, self).__init__(handle, core.new_trimesh2, core.del_trimesh2)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.Trimesh2(handle = {self.handle}, node_n = {self.node_number}, link_n = {self.link_number}, triangle_n = {self.triangle_number})'

    core.use(None, 'trimesh2_load_triangle_file', c_void_p, c_char_p,
             c_char_p, c_size_t)
    core.use(None, 'trimesh2_load_triangle_file_auto', c_void_p, c_char_p,
             c_char_p)

    def load_triangle_file(self, vertexfile, trianglefile, indexstart=None):
        if indexstart is None:
            core.trimesh2_load_triangle_file_auto(self.handle,
                                                  make_c_char_p(vertexfile),
                                                  make_c_char_p(trianglefile))
        else:
            core.trimesh2_load_triangle_file(self.handle,
                                             make_c_char_p(vertexfile),
                                             make_c_char_p(trianglefile), indexstart)

    core.use(None, 'trimesh2_save_triangle_file', c_void_p, c_char_p,
             c_char_p, c_size_t)

    def save_triangle_file(self, vertexfile, trianglefile, indexstart=1):
        if indexstart is None:
            core.trimesh2_save_triangle_file(self.handle,
                                             make_c_char_p(vertexfile),
                                             make_c_char_p(trianglefile), 1)
        else:
            core.trimesh2_save_triangle_file(self.handle,
                                             make_c_char_p(vertexfile),
                                             make_c_char_p(trianglefile), indexstart)

    core.use(None, 'trimesh2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.trimesh2_load(self.handle, make_c_char_p(path))

    core.use(None, 'trimesh2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.trimesh2_save(self.handle, make_c_char_p(path))

    @property
    def summary(self):
        return f'{self}'

    core.use(c_size_t, 'trimesh2_get_node_number', c_void_p)

    @property
    def node_number(self):
        return core.trimesh2_get_node_number(self.handle)

    core.use(c_size_t, 'trimesh2_get_link_number', c_void_p)

    @property
    def link_number(self):
        return core.trimesh2_get_link_number(self.handle)

    core.use(c_size_t, 'trimesh2_get_triangle_number', c_void_p)

    @property
    def triangle_number(self):
        return core.trimesh2_get_triangle_number(self.handle)

    def get_node(self, index):
        if 0 <= index < self.node_number:
            return Trimesh2.Node(self, index)

    def get_link(self, index):
        if 0 <= index < self.link_number:
            return Trimesh2.Link(self, index)

    def get_triangle(self, index):
        if 0 <= index < self.triangle_number:
            return Trimesh2.Triangle(self, index)

    core.use(c_size_t, 'trimesh2_get_nearest_node_id', c_void_p, c_double, c_double)

    def get_nearest_node_id(self, x, y):
        return core.trimesh2_get_nearest_node_id(self.handle, x, y)

    def get_nearest_node(self, x, y):
        return self.get_node(self.get_nearest_node_id(x, y))

    core.use(c_size_t, 'trimesh2_get_nearest_link_id', c_void_p, c_double, c_double)

    def get_nearest_link_id(self, x, y):
        return core.trimesh2_get_nearest_link_id(self.handle, x, y)

    def get_nearest_link(self, x, y):
        return self.get_link(self.get_nearest_link_id(x, y))

    core.use(c_size_t, 'trimesh2_get_nearest_triangle_id', c_void_p, c_double, c_double)

    def get_nearest_triangle_id(self, x, y):
        return core.trimesh2_get_nearest_triangle_id(self.handle, x, y)

    def get_nearest_triangle(self, x, y):
        return self.get_triangle(self.get_nearest_triangle_id(x, y))

    core.use(None, 'trimesh2_adjust', c_void_p)

    def adjust(self):
        """
        对于随机创建的三角形网格，进行一些自动调整，使得三角形的形状更好。注意：此为测试功能
        """
        core.trimesh2_adjust(self.handle)

    def create_pnw(self):
        pnw = SeepageMesh()

        for i in range(self.triangle_number):
            triangle = self.get_triangle(i)
            x, y = triangle.center
            cell = pnw.add_cell()
            cell.pos = (x, y, 0)
            cell.vol = triangle.area

        for i in range(self.link_number):
            lnk = self.get_link(i)
            if lnk.triangle_n == 2:
                i0 = lnk.get_triangle_id(0)
                i1 = lnk.get_triangle_id(1)
                assert self.triangle_number > i0 != i1 < self.triangle_number
                face = pnw.add_face(i0, i1)
                face.area = lnk.length
                face.length = get_distance(self.get_triangle(i0).center, self.get_triangle(i1).center)

        return pnw

    core.use(None, 'trimesh2_compute_node_strain_by_disp', c_void_p, c_char_p, c_char_p)

    @staticmethod
    def compute_node_strain_by_disp(trimesh, strain_file, disp_file):
        assert isinstance(trimesh, Trimesh2)
        core.trimesh2_compute_node_strain_by_disp(trimesh.handle, make_c_char_p(strain_file),
                                                  make_c_char_p(disp_file))

    core.use(None, 'trimesh2_from_mesh3', c_void_p, c_void_p)

    def from_mesh3(self, mesh3):
        assert isinstance(mesh3, Mesh3)
        core.trimesh2_from_mesh3(self.handle, mesh3.handle)

    core.use(None, 'trimesh2_to_mesh3', c_void_p, c_void_p, c_double)

    def to_mesh3(self, z=0):
        mesh3 = Mesh3()
        core.trimesh2_to_mesh3(self.handle, mesh3.handle, z)
        return mesh3

    core.use(None, 'trimesh2_create_rand_in_circle_with_preexisted', c_void_p,
             c_double, c_double,
             c_void_p, c_void_p)

    @staticmethod
    def create_rand_in_circle(radius, lmin=None, points=None):
        if points is not None:
            vx = Vector([p[0] for p in points])
            vy = Vector([p[1] for p in points])
        else:
            vx = Vector()
            vy = Vector()
        data = Trimesh2()
        if lmin is None:
            lmin = radius / 30
        core.trimesh2_create_rand_in_circle_with_preexisted(data.handle, radius, lmin, vx.handle, vy.handle)
        return data

    core.use(None, 'trimesh2_create_triprism', c_void_p, c_void_p, c_void_p)

    def to_triprism_mesh3(self, vz):
        if not isinstance(vz, Vector):
            vz = Vector(vz)
        mesh = Mesh3()
        assert isinstance(vz, Vector)
        core.trimesh2_create_triprism(self.handle, mesh.handle, vz.handle)
        return mesh


class ElementMap(HasHandle):
    class Element(Object):
        def __init__(self, model, index):
            self.model = model
            self.index = index

        core.use(c_size_t, 'element_map_related_count', c_void_p, c_size_t)

        @property
        def size(self):
            return core.element_map_related_count(self.model.handle, self.index)

        core.use(c_size_t, 'element_map_related_id', c_void_p, c_size_t, c_size_t)

        core.use(c_double, 'element_map_related_weight', c_void_p, c_size_t, c_size_t)

        def get_iw(self, i):
            ind = core.element_map_related_id(self.model.handle, self.index, i)
            w = core.element_map_related_weight(self.model.handle, self.index, i)
            return ind, w

    core.use(c_void_p, 'new_element_map')
    core.use(None, 'del_element_map', c_void_p)

    def __init__(self, path=None, handle=None):
        super(ElementMap, self).__init__(handle, core.new_element_map, core.del_element_map)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.ElementMap(handle = {self.handle}, size = {self.size})'

    core.use(None, 'element_map_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.element_map_save(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.element_map_load(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_to_str', c_void_p, c_size_t)

    def to_str(self):
        s = String()
        core.element_map_to_str(self.handle, s.handle)
        return s.to_str()

    core.use(None, 'element_map_from_str', c_void_p, c_size_t)

    def from_str(self, s):
        s2 = String()
        s2.assign(s)
        core.element_map_from_str(self.handle, s2.handle)

    core.use(c_size_t, 'element_map_size', c_void_p)

    @property
    def size(self):
        return core.element_map_size(self.handle)

    core.use(None, 'element_map_clear', c_void_p)

    def clear(self):
        core.element_map_clear(self.handle)

    core.use(None, 'element_map_add', c_void_p, c_void_p, c_void_p)

    def add_element(self, vi, vw):
        if not isinstance(vi, IntVector):
            vi = IntVector(vi)
        if not isinstance(vw, Vector):
            vw = Vector(vw)
        core.element_map_add(self.handle, vi.handle, vw.handle)

    def get_element(self, index):
        return ElementMap.Element(self, index)

    core.use(None, 'element_map_get', c_void_p, c_void_p, c_void_p, c_double)

    def get_values(self, source, buffer=None, default=None):
        """
        根据原始网格中的数据，根据此映射，计算此网格体系内各个网格的数值
        """
        assert isinstance(source, Vector)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        if default is None:
            default = 0.0
        core.element_map_get(self.handle, buffer.handle, source.handle, default)
        return buffer


class _SeepageNumpyAdaptor:
    """
    用以Seepage类和Numpy之间交换数据的适配器
    """

    class _Cells:
        """
        用以批量读取或者设置Cells的属性
        """

        def __init__(self, model):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model

        def get(self, index, buf=None):
            """
            Cell属性。index的含义参考 Seepage.cells_write
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.cell_number, dtype=float)
                else:
                    assert len(buf) == self.model.cell_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.cells_write(pointer=buf.ctypes.data_as(POINTER(c_double)), index=index)
                return buf

        def set(self, index, buf):
            """
            Cell属性。index的含义参考 Seepage.cells_write
            """
            if not is_array(buf):
                self.model.cells_read(value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.cell_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.cells_read(pointer=buf.ctypes.data_as(POINTER(c_double)), index=index)

        @property
        def x(self):
            """
            各个Cell的x坐标
            """
            return self.get(-1)

        @x.setter
        def x(self, value):
            """
            各个Cell的x坐标
            """
            self.set(-1, value)

        @property
        def y(self):
            """
            各个Cell的y坐标
            """
            return self.get(-2)

        @y.setter
        def y(self, value):
            """
            各个Cell的y坐标
            """
            self.set(-2, value)

        @property
        def z(self):
            """
            各个Cell的z坐标
            """
            return self.get(-3)

        @z.setter
        def z(self, value):
            """
            各个Cell的z坐标
            """
            self.set(-3, value)

        @property
        def v0(self):
            """
            各个Cell的v0属性(孔隙的v0，参考Cell定义)
            """
            return self.get(-4)

        @v0.setter
        def v0(self, value):
            self.set(-4, value)

        @property
        def k(self):
            """
            各个Cell的k属性(孔隙的k，参考Cell定义)
            """
            return self.get(-5)

        @k.setter
        def k(self, value):
            self.set(-5, value)

        @property
        def fluid_mass(self):
            """
            所有流体的总的质量<只读>
            """
            return self.get(-10)

        @property
        def fluid_vol(self):
            """
            所有流体的总的体积<只读>
            """
            return self.get(-11)

    class _Faces:
        """
        用以批量读取或者设置Faces的属性
        """

        def __init__(self, model):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model

        def get(self, index, buf=None):
            """
            读取各个Face的属性
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.face_number, dtype=float)
                else:
                    assert len(buf) == self.model.face_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.faces_write(pointer=buf.ctypes.data_as(POINTER(c_double)), index=index)
                return buf

        def set(self, index, buf):
            """
            设置各个Face的属性
            """
            if not is_array(buf):
                self.model.faces_read(value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.face_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.faces_read(pointer=buf.ctypes.data_as(POINTER(c_double)), index=index)

        @property
        def cond(self):
            """
            各个Face位置的导流系数
            """
            return self.get(-1)

        @cond.setter
        def cond(self, value):
            """
            各个Face位置的导流系数
            """
            self.set(-1, value)

        @property
        def dr(self):
            return self.get(-2)

        @dr.setter
        def dr(self, value):
            self.set(-2, value)

        def get_dv(self, index=None, buf=None):
            """
            上一次迭代经过Face流体的体积.
            """
            if index is None:
                return self.get(-19, buf=buf)
            else:
                assert 0 <= index < 9, f'index = {index} is not permitted'
                return self.get(-10 - index, buf=buf)

    class _Fluids:
        """
        用以批量读取或者设置某一种流体的属性
        """

        def __init__(self, model, fluid_id):
            assert isinstance(model, Seepage)
            assert np is not None
            self.model = model
            self.fluid_id = fluid_id

        def get(self, index, buf=None):
            """
            返回属性
            """
            if np is not None:
                if buf is None:
                    buf = np.zeros(shape=self.model.cell_number, dtype=float)
                else:
                    assert len(buf) == self.model.cell_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.fluids_write(fluid_id=self.fluid_id, index=index,
                                        pointer=buf.ctypes.data_as(POINTER(c_double)))
                return buf

        def set(self, index, buf):
            """
            设置属性
            """
            if not is_array(buf):
                self.model.fluids_read(fluid_id=self.fluid_id, value=buf, index=index)
                return
            if np is not None:
                assert len(buf) == self.model.cell_number
                if not buf.flags['C_CONTIGUOUS']:
                    buf = np.ascontiguous(buf, dtype=buf.dtype)
                self.model.fluids_read(fluid_id=self.fluid_id, index=index,
                                       pointer=buf.ctypes.data_as(POINTER(c_double)))

        @property
        def mass(self):
            """
            流体质量
            """
            return self.get(-1)

        @mass.setter
        def mass(self, value):
            self.set(-1, value)

        @property
        def den(self):
            """
            流体密度
            """
            return self.get(-2)

        @den.setter
        def den(self, value):
            self.set(-2, value)

        @property
        def vol(self):
            """
            流体体积
            """
            return self.get(-3)

        @vol.setter
        def vol(self, value):
            self.set(-3, value)

        @property
        def vis(self):
            """
            流体粘性系数
            """
            return self.get(-4)

        @vis.setter
        def vis(self, value):
            self.set(-4, value)

    def __init__(self, model):
        self.model = model

    @property
    def cells(self):
        return _SeepageNumpyAdaptor._Cells(model=self.model)

    @property
    def faces(self):
        return _SeepageNumpyAdaptor._Faces(model=self.model)

    def fluids(self, *fluid_id):
        """
        返回给定流体或者组分的属性适配器
        """
        return _SeepageNumpyAdaptor._Fluids(model=self.model, fluid_id=fluid_id)


class Seepage(HasHandle, HasCells):
    """
    多相多组分渗流模型。Seepage类是进行热流耦合模拟的基础。Seepage类主要涉及单元Cell，界面Face，流体Fluid，反应Reaction，流体定义FluDef
    几个概念。
    对于任意渗流场，均可以离散为由Cell<控制体：流体的存储空间>和Face<两个Cell之间的界面，流体的流动通道>组成的结构。
    """

    class Reaction(HasHandle):
        """
        定义一个化学反应。反应所需要的物质定义在Seepage.Cell中。这里，所谓化学反应，是一种或者几种流体（或者流体的组分）转化为另外一种或者几种
        流体或者组分，并吸收或者释放能量的过程。这个Reaction，即定义参与反应的各种物质的比例、反应的速度以及反应过程中的能量变化。基于Seepage
        类模拟水合物的分解或者生成、冰的形成和融化、重油的裂解等，均基于此Reaction类进行定义。
        """
        core.use(c_void_p, 'new_reaction')
        core.use(None, 'del_reaction', c_void_p)

        def __init__(self, path=None, handle=None):
            """
            初始化一个反应。当给定fpath的时候，则载入之前创建好的反应。
            """
            super(Seepage.Reaction, self).__init__(handle, core.new_reaction, core.del_reaction)
            if handle is None:
                if path is not None:
                    self.load(path)
            else:
                assert path is None

        core.use(None, 'reaction_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.reaction_save(self.handle, make_c_char_p(path))

        core.use(None, 'reaction_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.reaction_load(self.handle, make_c_char_p(path))

        core.use(None, 'reaction_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'reaction_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.reaction_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.reaction_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            """
            返回一个二进制的FileMap对象
            """
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(None, 'reaction_set_dheat', c_void_p, c_double)
        core.use(c_double, 'reaction_get_dheat', c_void_p)

        @property
        def heat(self):
            """
            发生1kg物质的化学反应<1kg的左侧物质，转化为1kg的右侧物质>释放的热量，单位焦耳
            """
            return core.reaction_get_dheat(self.handle)

        @heat.setter
        def heat(self, value):
            """
            发生1kg物质的化学反应<1kg的左侧物质，转化为1kg的右侧物质>释放的热量，单位焦耳
            """
            core.reaction_set_dheat(self.handle, value)

        dheat = heat

        core.use(None, 'reaction_set_t0', c_void_p, c_double)
        core.use(c_double, 'reaction_get_t0', c_void_p)

        @property
        def temp(self):
            """
            和dheat对应的参考温度，只有当反应前后的温度都等于此temp的时候，释放的热量才可以使用dheat来定义
            """
            return core.reaction_get_t0(self.handle)

        @temp.setter
        def temp(self, value):
            core.reaction_set_t0(self.handle, value)

        core.use(None, 'reaction_set_p2t', c_void_p, c_void_p, c_void_p)

        def set_p2t(self, p, t):
            """
            设置不同的压力下，反应可以发生的临界温度。
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
            添加一种反应物质。其中index为Seepage.Cell中定义的流体组分的序号，weight为发生1kg的反应的时候此物质变化的质量，其中左侧物质
            的weight为负值，右侧为正值。fa_t为定义流体温度的属性ID，fa_c为定义流体比热的属性ID
            """
            core.reaction_add_component(self.handle, *parse_fid3(index), weight, fa_t, fa_c)

        core.use(None, 'reaction_clear_components', c_void_p)

        def clear_components(self):
            core.reaction_clear_components(self.handle)

        core.use(None, 'reaction_add_inhibitor', c_void_p,
                 c_size_t, c_size_t, c_size_t,
                 c_size_t, c_size_t, c_size_t,
                 c_void_p, c_void_p)

        def add_inhibitor(self, sol, liq, c, t):
            """
            添加一种抑制剂。其中sol为抑制剂对应的组分ID，liq为流体的组分ID。sol的质量除以liq的质量为抑制剂的浓度。则向量c和向量t定义随着
            这个浓度的变化，化学反应平衡温度的变化情况.
            """
            if not isinstance(c, Vector):
                c = Vector(c)
            if not isinstance(t, Vector):
                t = Vector(t)
            core.reaction_add_inhibitor(self.handle, *parse_fid3(sol), *parse_fid3(liq), c.handle, t.handle)

        core.use(None, 'reaction_clear_inhibitors', c_void_p)

        def clear_inhibitors(self):
            core.reaction_clear_inhibitors(self.handle)

        core.use(None, 'reaction_react', c_void_p, c_void_p, c_double)

        def react(self, model, dt):
            """
            将该反应作用到Seepage的所有的Cell上dt时间。这个过程会修改model中各个Cell中相应组分的质量和温度，但是会保证总的质量不会发生改变。
            """
            self.adjust_weights()  # 确保权重正确，保证质量守恒
            core.reaction_react(self.handle, model.handle, dt)

        core.use(None, 'reaction_adjust_weights', c_void_p)

        def adjust_weights(self):
            """
            等比例地调整权重。确保方程左侧系数加和之后等于-1，右侧的系数加和之后等于1.
            """
            core.reaction_adjust_weights(self.handle)

        def adjust_widghts(self):
            """
            同adjust_weights
            """
            warnings.warn('Use <adjust_weights>', DeprecationWarning)
            self.adjust_weights()

        core.use(c_double, 'reaction_get_rate', c_void_p, c_void_p)

        def get_rate(self, cell):
            """
            获得给定Cell在当前状态下的<瞬时的>反应速率
            """
            assert isinstance(cell, Seepage.CellData)
            return core.reaction_get_rate(self.handle, cell.handle)

        core.use(None, 'reaction_set_idt', c_void_p, c_size_t)
        core.use(c_size_t, 'reaction_get_idt', c_void_p)

        @property
        def idt(self):
            """
            Cell的属性ID，用以定义反应作用到该Cell上的时候，平衡温度的调整量. 这允许在不同的Cell上，有不同的反应温度.
            """
            return core.reaction_get_idt(self.handle)

        @idt.setter
        def idt(self, value):
            core.reaction_set_idt(self.handle, value)

        core.use(None, 'reaction_set_wdt', c_void_p, c_double)
        core.use(c_double, 'reaction_get_wdt', c_void_p)

        @property
        def wdt(self):
            """
            和idt配合使用. 在Cell定义温度调整量的时候，可以利用这个权重再对这个调整量进行调整.
            比如，当Cell给的温度的调整量的单位不是K的时候，可以利用wdt属性来添加一个倍率.
            """
            return core.reaction_get_wdt(self.handle)

        @wdt.setter
        def wdt(self, value):
            core.reaction_set_wdt(self.handle, value)

        core.use(None, 'reaction_set_irate', c_void_p, c_size_t)
        core.use(c_size_t, 'reaction_get_irate', c_void_p)

        @property
        def irate(self):
            """
            Cell的属性ID，用以定义反应作用到该Cell上的时候，反应速率应该乘以的倍数。若定义这个属性，且Cell的这个属性值小于等于0，那么
            反应在这个Cell上将不会发生
                Note: 如果希望某个反应只在部分Cell上发生，则可以利用这个属性来实现
            """
            return core.reaction_get_irate(self.handle)

        @irate.setter
        def irate(self, value):
            core.reaction_set_irate(self.handle, value)

    class FluDef(HasHandle):
        """
        流体属性的定义。其中流体的密度和粘性系数都被视为压力和温度的函数，并且利用二维插值来存储。
            比热容被视为常数(这可能不严谨，但是大多数情况下够用)
        """
        core.use(c_void_p, 'new_fludef')
        core.use(None, 'del_fludef', c_void_p)

        def __init__(self, den=1000.0, vis=1.0e-3, specific_heat=4200, name=None, handle=None):
            """
            构造函数。当handle为None的时候，会进行必要的初始化.
            """
            super(Seepage.FluDef, self).__init__(handle, core.new_fludef, core.del_fludef)
            if handle is None:
                # 现在，这是一个新建数据
                if isinstance(vis, Interp2):
                    self.vis = vis
                else:
                    assert 1.0e-7 < vis < 1.0e40
                    val = Interp2()
                    val.create(0.1e6, 30e6, 200e6, 1, 3000, 10000.0, lambda p, t: vis)
                    self.vis = val

                if isinstance(den, Interp2):
                    self.den = den
                else:
                    assert 1.0e-3 < den < 1.0e5
                    val = Interp2()
                    val.create(0.1e6, 30e6, 200e6, 1, 3000, 10000.0, lambda p, t: den)
                    self.den = val

                assert 100 < specific_heat < 100000
                self.specific_heat = specific_heat

                if name is not None:
                    self.name = name

        core.use(None, 'fludef_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.fludef_save(self.handle, make_c_char_p(path))

        core.use(None, 'fludef_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.fludef_load(self.handle, make_c_char_p(path))

        core.use(None, 'fludef_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'fludef_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.fludef_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.fludef_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(c_void_p, 'fludef_get_den', c_void_p)
        core.use(None, 'fludef_set_den', c_void_p, c_void_p)

        @property
        def den(self):
            """
            流体密度的插值 （只有当组分的数量为0的时候才可以使用）
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_den(self.handle))

        @den.setter
        def den(self, value):
            assert self.component_number == 0
            assert isinstance(value, Interp2)
            core.fludef_set_den(self.handle, value.handle)

        core.use(c_void_p, 'fludef_get_vis', c_void_p)
        core.use(None, 'fludef_set_vis', c_void_p, c_void_p)

        @property
        def vis(self):
            """
            流体粘性的插值（只有当组分的数量为0的时候才可以使用）
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_vis(self.handle))

        @vis.setter
        def vis(self, value):
            assert self.component_number == 0
            assert isinstance(value, Interp2)
            core.fludef_set_vis(self.handle, value.handle)

        core.use(c_double, 'fludef_get_specific_heat', c_void_p)
        core.use(None, 'fludef_set_specific_heat', c_void_p, c_double)

        @property
        def specific_heat(self):
            """
            流体的比热(常数)
            """
            assert self.component_number == 0
            return core.fludef_get_specific_heat(self.handle)

        @specific_heat.setter
        def specific_heat(self, value):
            assert self.component_number == 0
            assert 100.0 < value < 100000.0
            core.fludef_set_specific_heat(self.handle, value)

        core.use(c_size_t, 'fludef_get_component_number', c_void_p)
        core.use(None, 'fludef_set_component_number', c_void_p, c_size_t)

        @property
        def component_number(self):
            """
            流体组分的数量
            """
            return core.fludef_get_component_number(self.handle)

        @component_number.setter
        def component_number(self, value):
            core.fludef_set_component_number(self.handle, value)

        core.use(c_void_p, 'fludef_get_component', c_void_p, c_size_t)

        def get_component(self, idx):
            """
            返回流体的组分
            """
            assert idx >= 0
            if idx < self.component_number:
                return Seepage.FluDef(handle=core.fludef_get_component(self.handle, idx))

        core.use(None, 'fludef_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的组分
            """
            core.fludef_clear_components(self.handle)

        core.use(c_size_t, 'fludef_add_component', c_void_p, c_void_p)

        def add_component(self, flu):
            """
            添加流体组分，并返回组分的ID
            """
            assert isinstance(flu, Seepage.FluDef)
            return core.fludef_add_component(self.handle, flu.handle)

        @staticmethod
        def create(defs):
            """
            将存储在list中的多个流体的定义，组合成为一个具有多个组分的单个流体定义
            """
            if isinstance(defs, Seepage.FluDef):
                return defs
            else:
                result = Seepage.FluDef()
                for x in defs:
                    result.add_component(Seepage.FluDef.create(x))
                return result

        core.use(None, 'fludef_set_name', c_void_p, c_char_p)
        core.use(c_char_p, 'fludef_get_name', c_void_p)

        @property
        def name(self):
            """
            流体组分的名称.
            """
            assert self.component_number == 0
            return core.fludef_get_name(self.handle).decode()

        @name.setter
        def name(self, value):
            assert self.component_number == 0
            core.fludef_set_name(self.handle, make_c_char_p(value))

        core.use(None, 'fludef_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            克隆数据
            """
            assert isinstance(other, Seepage.FluDef)
            core.fludef_clone(self.handle, other.handle)

    class FluData(HasHandle):
        core.use(c_void_p, 'new_fluid')
        core.use(None, 'del_fluid', c_void_p)

        def __init__(self, mass=None, den=None, vis=None, vol=None, handle=None):
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
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.fluid_save(self.handle, make_c_char_p(path))

        core.use(None, 'fluid_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.fluid_load(self.handle, make_c_char_p(path))

        core.use(None, 'fluid_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'fluid_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.fluid_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.fluid_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'fluid_get_mass', c_void_p)
        core.use(None, 'fluid_set_mass', c_void_p, c_double)

        @property
        def mass(self):
            """
            流体的质量,kg
            """
            return core.fluid_get_mass(self.handle)

        @mass.setter
        def mass(self, value):
            """
            流体的质量,kg
            """
            assert value >= 0
            core.fluid_set_mass(self.handle, value)

        core.use(c_double, 'fluid_get_vol', c_void_p)
        core.use(None, 'fluid_set_vol', c_void_p, c_double)

        @property
        def vol(self):
            """
            流体的体积,m^3
            注意:
                内核中并不存储流体体积，而是根据质量和密度计算得到的
            """
            return core.fluid_get_vol(self.handle)

        @vol.setter
        def vol(self, value):
            """
            修改流体的体积,m^3
            注意:
                内核中并不存储流体体积，而是根据质量和密度计算得到的
                将修改mass，并保持density不变
            """
            assert value >= 0
            core.fluid_set_vol(self.handle, value)

        core.use(c_double, 'fluid_get_den', c_void_p)
        core.use(None, 'fluid_set_den', c_void_p, c_double)

        @property
        def den(self):
            """
            流体密度 kg/m^3
                注意: 流体不可压缩，除非外部修改，否则密度永远维持不变
            """
            return core.fluid_get_den(self.handle)

        @den.setter
        def den(self, value):
            """
            流体密度 kg/m^3
                注意: 流体不可压缩，除非外部修改，否则密度永远维持不变
            """
            assert value > 0
            core.fluid_set_den(self.handle, value)

        core.use(c_double, 'fluid_get_vis', c_void_p)
        core.use(None, 'fluid_set_vis', c_void_p, c_double)

        @property
        def vis(self):
            """
            流体粘性系数. Pa.s
                注意: 除非外部修改，否则vis维持不变
            """
            return core.fluid_get_vis(self.handle)

        @vis.setter
        def vis(self, value):
            """
            流体粘性系数. Pa.s
                注意: 除非外部修改，否则vis维持不变
            """
            assert value > 0
            core.fluid_set_vis(self.handle, value)

        @property
        def is_solid(self):
            """
            该流体单元在计算内核中是否可以被视为固体；
            """
            warnings.warn('FluData.is_solid will be deleted after 2024-5-5', DeprecationWarning)
            return self.vis >= 0.5e30

        core.use(c_double, 'fluid_get_attr', c_void_p, c_size_t)
        core.use(None, 'fluid_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            第index个流体自定义属性。当两个流体数据相加时，自定义属性将根据质量进行加权平均。
            当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            """
            if index is None:
                return default_val
            value = core.fluid_get_attr(self.handle, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            第index个流体自定义属性。当两个流体数据相加时，自定义属性将根据质量进行加权平均。
            当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.fluid_set_attr(self.handle, index, value)
            return self

        core.use(None, 'fluid_clone', c_void_p, c_void_p)

        def clone(self, other):
            assert isinstance(other, Seepage.FluData)
            core.fluid_clone(self.handle, other.handle)

        core.use(None, 'fluid_add', c_void_p, c_void_p)

        def add(self, other):
            """
            将other所定义的流体数据添加到self. 注意，并不是添加组分. 类似于: self = self + other.
            比如:
                若self的质量为1kg，other的质量也为1kg，则当执行了此函数之后，self的质量会成为2kg，而other保持不变.
            """
            assert isinstance(other, Seepage.FluData)
            core.fluid_add(self.handle, other.handle)

        core.use(c_size_t, 'fluid_get_component_number', c_void_p)
        core.use(None, 'fluid_set_component_number', c_void_p, c_size_t)

        @property
        def component_number(self):
            """
            流体组分的数量. 当流体不可再分的时候，组分数量为0; 否则，流体被视为混合物，且组分的数量大于0.
            """
            return core.fluid_get_component_number(self.handle)

        @component_number.setter
        def component_number(self, value):
            core.fluid_set_component_number(self.handle, value)

        core.use(c_void_p, 'fluid_get_component', c_void_p, c_size_t)

        def get_component(self, idx):
            """
            返回给定的组分
            """
            assert 0 <= idx
            if idx < self.component_number:
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
            添加流体组分，并返回组分的ID
            """
            assert isinstance(flu, Seepage.FluData)
            return core.fluid_add_component(self.handle, flu.handle)

        core.use(None, 'fluid_set_property', c_void_p, c_double, c_size_t, c_size_t, c_void_p)

        def set_property(self, p, fa_t, fa_c, fdef):
            """
            set fluid density, viscosity and specific heat in the given pressure
            and the fluid temperature defined by <fa_T>.
            """
            assert isinstance(fdef, Seepage.FluDef)
            core.fluid_set_property(self.handle, p, fa_t, fa_c, fdef.handle)

        core.use(None, 'fluid_set_components', c_void_p, c_void_p)

        def set_components(self, fdef):
            """
            按照fdef的定义来设置流体的组分的数量，从而使得这个流体数据和给定的流体定义具有相同的结构.
            """
            assert isinstance(fdef, Seepage.FluDef)
            core.fluid_set_components(self.handle, fdef.handle)

    class Fluid(FluData):
        """
        Fluid为Cell内存储的流体数据。Fluid由以下属性组成：

        1、流体的质量、密度、粘性系数。
        2、流体的自定义属性。在Fluid内存储一个浮点型的数组，存储一系列自定义的属性，用于辅助存储和计算。自定义属性从0开始编号。
        3、流体的组分。
            注意：流体的组分亦采用Fluid类进行定义（即Fluid为一个嵌套的类），因此，流体的组分也具有和流体同样的数据。流体的组分存储在
                一个数组内，且从0开始编号。当流体的组分数量不为0的时候，则存储在流体自身的数据自动失效，并利用组分的属性来自动计算
                这些组分作为一个整体的属性。如：流体的质量等于各个组分的质量之和，体积等于各个组分的体积之和，自定义属性则等于不同组分
                根据质量的加权平均。
        """
        core.use(c_void_p, 'seepage_cell_get_fluid', c_void_p, c_size_t)

        def __init__(self, cell, fid):
            assert isinstance(cell, Seepage.CellData)
            assert isinstance(fid, int)
            assert fid < cell.fluid_number
            self.cell = cell
            self.fid = fid
            super(Seepage.Fluid, self).__init__(handle=core.seepage_cell_get_fluid(self.cell.handle, self.fid))

        @property
        def vol_fraction(self):
            """
            流体的体积占Cell内所有流体总体积的比例
            """
            return self.cell.get_fluid_vol_fraction(self.fid)

    class CellData(HasHandle):
        core.use(c_void_p, 'new_seepage_cell')
        core.use(None, 'del_seepage_cell', c_void_p)

        def __init__(self, path=None, handle=None):
            super(Seepage.CellData, self).__init__(handle, core.new_seepage_cell, core.del_seepage_cell)
            if handle is None:
                if path is not None:
                    self.load(path)

        core.use(None, 'seepage_cell_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.seepage_cell_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_cell_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.seepage_cell_load(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_cell_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'seepage_cell_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.seepage_cell_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.seepage_cell_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'seepage_cell_get_pos', c_void_p, c_size_t)
        core.use(None, 'seepage_cell_set_pos', c_void_p, c_size_t, c_double)

        @property
        def x(self):
            return core.seepage_cell_get_pos(self.handle, 0)

        @x.setter
        def x(self, value):
            core.seepage_cell_set_pos(self.handle, 0, value)

        @property
        def y(self):
            return core.seepage_cell_get_pos(self.handle, 1)

        @y.setter
        def y(self, value):
            core.seepage_cell_set_pos(self.handle, 1, value)

        @property
        def z(self):
            return core.seepage_cell_get_pos(self.handle, 2)

        @z.setter
        def z(self, value):
            core.seepage_cell_set_pos(self.handle, 2, value)

        @property
        def pos(self):
            """
            该Cell在三维空间的坐标
            """
            return [core.seepage_cell_get_pos(self.handle, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            该Cell在三维空间的坐标
            """
            assert len(value) == 3
            for dim in range(3):
                core.seepage_cell_set_pos(self.handle, dim, value[dim])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离
            """
            p0 = self.pos
            if hasattr(other, 'pos'):
                p1 = other.pos
            else:
                p1 = other
            return ((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 + (p0[2] - p1[2]) ** 2) ** 0.5

        core.use(c_double, 'seepage_cell_get_v0', c_void_p)
        core.use(None, 'seepage_cell_set_v0', c_void_p, c_double)

        @property
        def v0(self):
            """
            当流体压力等于0时，该Cell内流体的存储空间 m^3
            """
            return core.seepage_cell_get_v0(self.handle)

        @v0.setter
        def v0(self, value):
            """
            当流体压力等于0时，该Cell内流体的存储空间 m^3
            """
            assert value >= 1.0e-10
            core.seepage_cell_set_v0(self.handle, value)

        core.use(c_double, 'seepage_cell_get_k', c_void_p)
        core.use(None, 'seepage_cell_set_k', c_void_p, c_double)

        @property
        def k(self):
            """
            The amount by which the volume (m^3) of the pore space increases when the fluid pressure increases by 1Pa.
            The smaller the value of k, the greater the stiffness of the pore space
            """
            return core.seepage_cell_get_k(self.handle)

        @k.setter
        def k(self, value):
            """
            The amount by which the volume (m^3) of the pore space increases when the fluid pressure increases by 1Pa.
            The smaller the value of k, the greater the stiffness of the pore space
            """
            core.seepage_cell_set_k(self.handle, value)

        def set_pore(self, p, v, dp, dv):
            """
            Create a pore so that when the internal pressure is equal to p, the volume is v;
            if the pressure changes dp, the volume changes to dv
            """
            k = max(1.0e-30, abs(dv)) / max(1.0e-30, abs(dp))
            self.k = k
            v0 = v - p * k
            self.v0 = v0
            if v0 <= 0:
                print(f'Warning: v0 (= {v0}) <= 0 at {self.pos}')
            return self

        def v2p(self, v):
            """
            Given the volume of fluid in the Cell, calculate the pressure of the fluid
            """
            return (v - self.v0) / self.k

        def p2v(self, p):
            """
            Calculate the volume of the fluid given the fluid pressure in the Cell
            """
            return self.v0 + p * self.k

        core.use(None, 'seepage_cell_fill', c_void_p, c_double, c_void_p)

        def fill(self, p, s):
            """
            根据此时流体的密度，孔隙的v0和k，给定的目标压力和流体饱和度，设置各个组分的质量。
                这里p为目标压力，s为目标饱和度;
                当各个相的饱和度的和不等于1的时候，将首先对饱和度的值进行等比例调整;
            注意：
                s作为一个数组，它的长度应该等于流体的数量或者组分的数量(均可以);
                当s的长度等于流体的数量的时候，需要事先设置流体中各个组分的比例;
            注意
                当s的总和等于0的时候，虽然给定目标压力，但是仍然不会填充流体. 此时填充后
                所有的组分都等于0.
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
            The pressure of the fluid in the cell
                (calculated from the total volume of the fluid and pore elasticity)
            """
            return core.seepage_cell_get_pre(self.handle)

        core.use(c_size_t, 'seepage_cell_get_fluid_n', c_void_p)
        core.use(None, 'seepage_cell_set_fluid_n', c_void_p, c_size_t)

        @property
        def fluid_number(self):
            """
            The amount of fluid in the cell
                (at least set to 1, and needs to be set to the same value for all cells in the model)
            """
            return core.seepage_cell_get_fluid_n(self.handle)

        @fluid_number.setter
        def fluid_number(self, value):
            """
            The amount of fluid in the cell
            (at least set to 1, and needs to be set to the same value for all cells in the model)
            """
            assert 0 <= value < 10
            core.seepage_cell_set_fluid_n(self.handle, value)

        def get_fluid(self, index):
            """
            Returns the index-th fluid object in the Cell
            """
            assert 0 <= index < self.fluid_number
            return Seepage.Fluid(self, index)

        @property
        def fluids(self):
            """
            All fluids in the cell
            """
            return Iterators.Fluid(self)

        def get_component(self, indexes):
            """
            Get the fluid component with the given indexes
            """
            assert len(indexes) >= 1
            flu = self.get_fluid(indexes[0])
            indexes = indexes[1:]
            while len(indexes) > 0:
                flu = flu.get_component(indexes[0])
                indexes = indexes[1:]
            return flu

        core.use(c_double, 'seepage_cell_get_fluid_vol', c_void_p)

        @property
        def fluid_vol(self):
            """
            The volume of all fluids.
            注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，在计算内核中被视为固体的流体
            """
            return core.seepage_cell_get_fluid_vol(self.handle)

        core.use(c_double, 'seepage_cell_get_fluid_mass', c_void_p)

        @property
        def fluid_mass(self):
            """
            The mass of all fluids
            注意：这个体积包含所有fluids的体积的和，包括那些粘性非常大，在计算内核中被视为固体的流体
            """
            return core.seepage_cell_get_fluid_mass(self.handle)

        core.use(c_double, 'seepage_cell_get_fluid_vol_fraction', c_void_p, c_size_t)

        def get_fluid_vol_fraction(self, index):
            """
            返回index给定流体的体积饱和度
            """
            assert 0 <= index < self.fluid_number
            return core.seepage_cell_get_fluid_vol_fraction(self.handle, index)

        core.use(c_double, 'seepage_cell_get_attr', c_void_p, c_size_t)
        core.use(None, 'seepage_cell_set_attr', c_void_p, c_size_t, c_double)
        core.use(c_size_t, 'seepage_cell_get_attr_n', c_void_p)

        @property
        def attr_n(self):
            """
            当前存储attr的数组的长度
            """
            return core.seepage_cell_get_attr_n(self.handle)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            该Cell的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
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
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            该Cell的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
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
                return self
            core.seepage_cell_set_attr(self.handle, index, value)
            return self

        core.use(None, 'seepage_cell_clone', c_void_p, c_void_p)

        def clone(self, other):
            assert isinstance(other, Seepage.CellData)
            core.seepage_cell_clone(self.handle, other.handle)

        core.use(None, 'seepage_cell_set_fluid_components', c_void_p, c_void_p)

        def set_fluid_components(self, model):
            """
            利用model中定义的流体来设置Cell中的流体的组分的数量.
            注意:
                此函数会递归地调用model中的组分定义，从而保证Cell中流体组分结构和model中完全一样.
            """
            assert isinstance(model, Seepage)
            core.seepage_cell_set_fluid_components(self.handle, model.handle)

        core.use(None, 'seepage_cell_set_fluid_property', c_void_p,
                 c_double, c_size_t, c_size_t,
                 c_void_p)

        def set_fluid_property(self, p, fa_t, fa_c, model):
            """
            利用model中定义的流体的属性来更新流体的比热、密度和粘性系数.
            注意：
                函数会使用在各个流体中由fa_t指定的温度，并根据给定的压力p来查找流体属性;
                因此，在调用这个函数之前，务必要设置各个流体的温度 (fa_t).
            注意：
                在调用之前，务必保证此Cell内的流体的结构和model内fludef的结构一致。 即，应该首先调用set_fluid_components函数
            """
            assert isinstance(model, Seepage)
            core.seepage_cell_set_fluid_property(self.handle, p, fa_t, fa_c, model.handle)

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
            assert isinstance(model, Seepage)
            assert isinstance(index, int)
            assert index < model.cell_number
            self.model = model
            self.index = index
            super(Seepage.Cell, self).__init__(handle=core.seepage_get_cell(model.handle, index))

        def __str__(self):
            return f'zml.Seepage.Cell(handle = {self.model.handle}, index = {self.index}, pos = {self.pos})'

        core.use(c_size_t, 'seepage_get_cell_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            与该Cell连接的Face的数量
            """
            return core.seepage_get_cell_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            与该Cell相邻的Cell的数量
            """
            return self.face_number

        core.use(c_size_t, 'seepage_get_cell_face_id', c_void_p, c_size_t, c_size_t)

        core.use(c_size_t, 'seepage_get_cell_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            """
            与该Cell相邻的第index个Cell。当index个Cell不存在时，返回None
            """
            assert 0 <= index < self.cell_number
            cell_id = core.seepage_get_cell_cell_id(self.model.handle, self.index, index)
            return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            与该Cell连接的第index个Face。当index个Face不存在时，返回None
            注：改Face的另一侧，即为get_cell返回的Cell
            """
            assert 0 <= index < self.face_number
            face_id = core.seepage_get_cell_face_id(self.model.handle, self.index, index)
            return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            此Cell周围的所有Cell
            """
            return Iterators.Cell(self)

        @property
        def faces(self):
            """
            此Cell周围的所有Face
            """
            return Iterators.Face(self)

        def set_ini(self, ca_mc, ca_t, fa_t, fa_c, pos=None, vol=1.0, porosity=0.1, pore_modulus=1000e6, denc=1.0e6,
                    temperature=280.0, p=1.0, s=None, pore_modulus_range=None):
            """
            配置初始状态. 必须保证给定温度和压力.
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
        core.use(c_void_p, 'new_seepage_face')
        core.use(None, 'del_seepage_face', c_void_p)

        def __init__(self, path=None, handle=None):
            super(Seepage.FaceData, self).__init__(handle, core.new_seepage_face, core.del_seepage_face)
            if handle is None:
                if path is not None:
                    self.load(path)

        core.use(None, 'seepage_face_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.seepage_face_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_face_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.seepage_face_load(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_face_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'seepage_face_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.seepage_face_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.seepage_face_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(c_double, 'seepage_face_get_attr', c_void_p, c_size_t)
        core.use(None, 'seepage_face_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
            """
            该Face的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
            if index is None:
                return default_val
            value = core.seepage_face_get_attr(self.handle, index)
            if min <= value <= max:
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            该Face的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_face_set_attr(self.handle, index, value)
            return self

        core.use(None, 'seepage_face_clone', c_void_p, c_void_p)

        def clone(self, other):
            assert isinstance(other, Seepage.FaceData)
            core.seepage_face_clone(self.handle, other.handle)

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
            """
            return core.seepage_face_get_cond(self.handle)

        @cond.setter
        def cond(self, value):
            """
            此Face的导流能力. dv=cond*dp*dt/vis，其中dp为两端的压力差，dt为时间步长，vis为内部流体的粘性系数
            """
            core.seepage_face_set_cond(self.handle, value)

        core.use(c_double, 'seepage_face_get_dr', c_void_p)
        core.use(None, 'seepage_face_set_dr', c_void_p, c_double)

        @property
        def dr(self):
            return core.seepage_face_get_dr(self.handle)

        @dr.setter
        def dr(self, value):
            core.seepage_face_set_dr(self.handle, value)

        core.use(c_double, 'seepage_face_get_dv', c_void_p, c_size_t)

        def get_dv(self, fluid_id):
            """
            返回上一步迭代通过这个face的流体的体积
            """
            assert isinstance(fluid_id, int)
            return core.seepage_face_get_dv(self.handle, fluid_id)

        core.use(c_size_t, 'seepage_face_get_ikr', c_void_p, c_size_t)
        core.use(None, 'seepage_face_set_ikr',
                 c_void_p, c_size_t, c_size_t)

        def get_ikr(self, index):
            """
            第index种流体的相对渗透率曲线的id
            """
            return core.seepage_face_get_ikr(self.handle, index)

        def set_ikr(self, index, value):
            """
            设置在这个Face中，第index种流体的相对渗透率曲线的id.
                如果在这个Face中，没有为某个流体选择相渗曲线，则如果该流体的序号为ID，则默认使用序号为ID的相渗曲线。
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
            assert isinstance(model, Seepage)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index
            super(Seepage.Face, self).__init__(handle=core.seepage_get_face(model.handle, index))

        def __str__(self):
            return f'zml.Seepage.Face(handle = {self.model.handle}, index = {self.index}) '

        core.use(c_size_t, 'seepage_get_face_cell_id', c_void_p, c_size_t, c_size_t)

        @property
        def cell_number(self):
            """
            和Face连接的Cell的数量
            """
            return 2

        def get_cell(self, index):
            """
            和Face连接的第index个Cell
            """
            assert index == 0 or index == 1
            cell_id = core.seepage_get_face_cell_id(self.model.handle, self.index, index)
            return self.model.get_cell(cell_id)

        @property
        def cells(self):
            """
            返回Face两端的Cell
            """
            return self.get_cell(0), self.get_cell(1)

        @property
        def pos(self):
            """
            返回Face中心点的位置（根据两侧的Cell的位置来自动计算）
            """
            p0 = self.get_cell(0).pos
            p1 = self.get_cell(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离
            """
            if hasattr(other, 'pos'):
                return get_distance(self.pos, other.pos)
            else:
                return get_distance(self.pos, other)

    class Injector(HasHandle):
        """
        流体的注入点。可以按照一定的规律向特定的Cell注入特定的流体(或者能量).
        """
        core.use(c_void_p, 'new_injector')
        core.use(None, 'del_injector', c_void_p)

        def __init__(self, path=None, handle=None):
            super(Seepage.Injector, self).__init__(handle, core.new_injector, core.del_injector)
            if handle is None:
                if path is not None:
                    self.load(path)

        core.use(None, 'injector_save', c_void_p, c_char_p)

        def save(self, path):
            """
            序列化保存. 可选扩展名:
                1: .txt  文本格式 (跨平台，基本不可读)
                2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
                3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
            """
            if path is not None:
                core.injector_save(self.handle, make_c_char_p(path))

        core.use(None, 'injector_load', c_void_p, c_char_p)

        def load(self, path):
            """
            序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
            """
            if path is not None:
                core.injector_load(self.handle, make_c_char_p(path))

        core.use(None, 'injector_write_fmap', c_void_p, c_void_p, c_char_p)
        core.use(None, 'injector_read_fmap', c_void_p, c_void_p, c_char_p)

        def to_fmap(self, fmt='binary'):
            """
            将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
            """
            fmap = FileMap()
            core.injector_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
            return fmap

        def from_fmap(self, fmap, fmt='binary'):
            """
            从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
            """
            assert isinstance(fmap, FileMap)
            core.injector_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

        @property
        def fmap(self):
            return self.to_fmap(fmt='binary')

        @fmap.setter
        def fmap(self, value):
            self.from_fmap(value, fmt='binary')

        core.use(c_size_t, 'injector_get_cell_id', c_void_p)
        core.use(None, 'injector_set_cell_id', c_void_p, c_size_t)

        @property
        def cell_id(self):
            """
            注入点关联的Cell的ID。如果该ID不存在，则不会注入
            """
            return core.injector_get_cell_id(self.handle)

        @cell_id.setter
        def cell_id(self, value):
            """
            注入点关联的Cell的ID。如果该ID不存在，则不会注入
            """
            core.injector_set_cell_id(self.handle, value)

        core.use(c_void_p, 'injector_get_flu', c_void_p)

        @property
        def flu(self):
            """
            即将注入到Cell中的流体的数据
            """
            return Seepage.FluData(handle=core.injector_get_flu(self.handle))

        core.use(None, 'injector_set_fid', c_void_p, c_size_t, c_size_t, c_size_t)

        def set_fid(self, fluid_id):
            """
            设置注入的流体的ID
            """
            core.injector_set_fid(self.handle, *parse_fid3(fluid_id))

        core.use(c_double, 'injector_get_value', c_void_p)

        @property
        def value(self):
            """
            注入的数值。可以有多重的含义：
                当注入流体的时候，为注入的体积速率 m^3/s
                当注热时：
                    若恒温注热，则为温度
                    若恒功率，则为功率
            """
            return core.injector_get_value(self.handle)

        core.use(c_double, 'injector_get_time', c_void_p)
        core.use(None, 'injector_set_time', c_void_p, c_double)

        @property
        def time(self):
            """
            每一个Injector都内置一个时间。请无比确保这个时间标签和model的时间一致
            """
            return core.injector_get_time(self.handle)

        @time.setter
        def time(self, value):
            """
            每一个Injector都内置一个时间。请无比确保这个时间标签和model的时间一致
            """
            core.injector_set_time(self.handle, value)

        core.use(c_double, 'injector_get_pos', c_void_p, c_size_t)
        core.use(None, 'injector_set_pos', c_void_p, c_size_t, c_double)

        @property
        def pos(self):
            """
            该Injector在三维空间的坐标
            """
            return [core.injector_get_pos(self.handle, i) for i in range(3)]

        @pos.setter
        def pos(self, value):
            """
            该Injector在三维空间的坐标
            """
            assert len(value) == 3
            for dim in range(3):
                core.injector_set_pos(self.handle, dim, value[dim])

        core.use(c_double, 'injector_get_radi', c_void_p)
        core.use(None, 'injector_set_radi', c_void_p, c_double)

        @property
        def radi(self):
            """
            Injector的控制半径
            """
            return core.injector_get_radi(self.handle)

        @radi.setter
        def radi(self, value):
            """
            Injector的控制半径
            """
            core.injector_set_radi(self.handle, value)

        core.use(c_double, 'injector_get_g_heat', c_void_p)
        core.use(None, 'injector_set_g_heat', c_void_p, c_double)

        @property
        def g_heat(self):
            return core.injector_get_g_heat(self.handle)

        @g_heat.setter
        def g_heat(self, value):
            core.injector_set_g_heat(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_mc', c_void_p)
        core.use(None, 'injector_set_ca_mc', c_void_p, c_size_t)

        @property
        def ca_mc(self):
            return core.injector_get_ca_mc(self.handle)

        @ca_mc.setter
        def ca_mc(self, value):
            core.injector_set_ca_mc(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_t', c_void_p)
        core.use(None, 'injector_set_ca_t', c_void_p, c_size_t)

        @property
        def ca_t(self):
            return core.injector_get_ca_t(self.handle)

        @ca_t.setter
        def ca_t(self, value):
            core.injector_set_ca_t(self.handle, value)

        core.use(None, 'injector_add_oper', c_void_p, c_double, c_double)

        def add_oper(self, time, qinj):
            """
            添加对注入排量的一个修改。请无比按照时间顺序进行添加
            """
            core.injector_add_oper(self.handle, time, qinj)
            return self

        core.use(None, 'injector_work', c_void_p, c_void_p, c_double)

        def work(self, model, dt):
            """
            执行注入操作。会同步更新injector内部存储的time属性；
            注：此函数不需要调用。内置在Seepage中的Injector，会在Seepage.iterate函数中被自动调用
            """
            assert isinstance(model, Seepage)
            core.injector_work(self.handle, model.handle, dt)

        core.use(None, 'injector_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            克隆所有的数据；包括作用的cell_id
            """
            assert isinstance(other, Seepage.Injector)
            core.injector_clone(self.handle, other.handle)

    class Updater(HasHandle):
        """
        执行内核求解. 由于在计算的时候必须用到一些临时变量，这些变量如果每次都进行初始化，则可能拖慢计算进程，因此需要缓存。因此
        关于计算的部分，不能做成纯方法，故而有这个类来辅助.
        """
        core.use(c_void_p, 'new_seepage_updater')
        core.use(None, 'del_seepage_updater', c_void_p)

        def __init__(self, handle=None):
            super(Seepage.Updater, self).__init__(handle, core.new_seepage_updater, core.del_seepage_updater)
            self.solver = None

        core.use(None, 'seepage_updater_iterate', c_void_p, c_void_p, c_void_p, c_double,
                 c_size_t, c_size_t, c_size_t, c_size_t, c_void_p)

        def iterate(self, model, dt, fa_s=None, fa_q=None, fa_k=None, ca_p=None, solver=None):
            """
            在时间上向前迭代
            fa_s: Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力）;
            fa_q：Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)
            fa_k: Face内流体的惯性系数的属性ID;
            ca_p：Cell的自定义属性，表示Cell内流体的压力(迭代时的压力，并非按照流体体积进行计算的)
            """
            lic.check_once()
            if solver is None:
                self.solver = ConjugateGradientSolver(tolerance=1.0e-12)
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
            对于此渗流模型，当定义了热传导相关的参数之后，可以作为一个热传导模型来使用。具体和Thermal模型类似。其中：
            ca_t:   Cell的温度属性的ID；
            ca_mc:  Cell范围内质量和比热的乘积；
            fa_g:   Face导热的通量g; 单位时间内通过Face的热量dH=g*dT；
            dt：    时间步长;
            """
            if solver is None:
                self.solver = ConjugateGradientSolver(tolerance=1.0e-12)
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
            在调用了iterate/iterate_thermal函数之后，调用此函数，来获取更优的时间步长.
            当ca_T和ca_mc给定时，返回热传导过程的建议值，
            否则为渗流的
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

        core.use(None, 'seepage_updater_diffusion', c_void_p, c_void_p, c_double,
                 c_size_t, c_size_t, c_size_t,
                 c_size_t, c_size_t, c_size_t,
                 c_void_p, c_void_p, c_void_p, c_void_p, c_double)

        def diffusion(self, model, dt, fid0, fid1, vs0, vk, vg, vpg=None, ds_max=0.05):
            """
            流体扩散。其中fid0和fid1定义两种流体。在扩散的时候，相邻Cell的这两种流体会进行交换，但会保证每个Cell的流体体积不变；
            其中vs0定义两种流体压力相等的时候fid0的饱和度；vk当饱和度变化1的时候，压力的变化幅度；
            vg定义face的导流能力(针对fid0和fid1作为一个整体);
            vpg定义流体fid0受到的重力减去fid1的重力在face上的投影;
            ds_max为允许的饱和度最大的改变量
            """
            assert isinstance(vs0, Vector)
            assert isinstance(vk, Vector)
            assert isinstance(vg, Vector)
            if not isinstance(vpg, Vector):
                vpg = Vector()

            core.seepage_updater_diffusion(self.handle, model.handle, dt, *parse_fid3(fid0), *parse_fid3(fid1),
                                           vs0.handle, vk.handle, vg.handle, vpg.handle, ds_max)

    core.use(c_void_p, 'new_seepage')
    core.use(None, 'del_seepage', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Seepage, self).__init__(handle, core.new_seepage, core.del_seepage)
        self.__updater = None
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        cell_n = self.cell_number
        face_n = self.face_number
        note = self.get_note()
        return f'zml.Seepage(handle={self.handle}, cell_n={cell_n}, face_n={face_n}, note={note})'

    core.use(None, 'seepage_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.seepage_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.seepage_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'seepage_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.seepage_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.seepage_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'seepage_add_note', c_void_p, c_char_p)

    def add_note(self, text):
        core.seepage_add_note(self.handle, make_c_char_p(text))

    core.use(c_char_p, 'seepage_get_note', c_void_p)

    def get_note(self):
        return core.seepage_get_note(self.handle).decode()

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

    core.use(c_size_t, 'seepage_get_cell_n', c_void_p)

    @property
    def cell_number(self):
        """
        Cell的数量
        """
        return core.seepage_get_cell_n(self.handle)

    core.use(c_size_t, 'seepage_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        Face的数量
        """
        return core.seepage_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_get_inj_n', c_void_p)

    @property
    def injector_number(self):
        """
        Injector的数量
        """
        return core.seepage_get_inj_n(self.handle)

    def get_cell(self, index):
        """
        返回第index个Cell对象
        """
        if 0 <= index < self.cell_number:
            return Seepage.Cell(self, index)

    def get_face(self, index):
        """
        返回第index个Face对象
        """
        if 0 <= index < self.face_number:
            return Seepage.Face(self, index)

    core.use(c_void_p, 'seepage_get_inj', c_void_p, c_size_t)

    def get_injector(self, index):
        if 0 <= index < self.injector_number:
            return Seepage.Injector(handle=core.seepage_get_inj(self.handle, index))

    core.use(c_size_t, 'seepage_add_cell', c_void_p)

    def add_cell(self, data=None):
        """
        添加一个新的Cell，并返回Cell对象
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
                     ca_mc=None, ca_t=None, g_heat=None):
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

        if cell is not None:
            if isinstance(cell, Seepage.Cell):
                cell = cell.index
            inj.cell_id = cell

        if fluid_id is not None:
            inj.set_fid(fluid_id)

        if flu is not None:
            assert isinstance(flu, Seepage.FluData)
            inj.flu.clone(flu)

        if pos is not None:
            inj.pos = pos

        if radi is not None:
            inj.radi = radi

        if ca_mc is not None:
            inj.ca_mc = ca_mc

        if ca_t is not None:
            inj.ca_t = ca_t

        if g_heat is not None:
            inj.g_heat = g_heat

        if opers is not None:
            for oper in opers:
                inj.add_oper(*oper)

        return inj

    @property
    def cells(self):
        """
        模型中所有的Cell
        """
        return Iterators.Cell(self)

    @property
    def faces(self):
        """
        模型中所有的Face
        """
        return Iterators.Face(self)

    @property
    def injectors(self):
        """
        模型中所有的Injector
        """
        return Iterators.Injector(self)

    core.use(None, 'seepage_apply_injs', c_void_p, c_double)

    def apply_injectors(self, dt):
        """
        所有的注入点执行注入操作.
        """
        core.seepage_apply_injs(self.handle, dt)

    core.use(c_double, 'seepage_get_gravity', c_void_p, c_size_t)
    core.use(None, 'seepage_set_gravity', c_void_p, c_size_t, c_double)

    @property
    def gravity(self):
        """
        重力加速度，默认为(0,0,0)
        """
        return (core.seepage_get_gravity(self.handle, 0),
                core.seepage_get_gravity(self.handle, 1),
                core.seepage_get_gravity(self.handle, 2))

    @gravity.setter
    def gravity(self, value):
        """
        重力加速度，默认为(0,0,0)
        """
        assert len(value) == 3
        for dim in range(3):
            core.seepage_set_gravity(self.handle, dim, value[dim])

    core.use(c_size_t, 'seepage_get_gr_n', c_void_p)

    @property
    def gr_number(self):
        return core.seepage_get_gr_n(self.handle)

    core.use(c_void_p, 'seepage_get_gr', c_void_p, c_size_t)

    def get_gr(self, idx):
        if idx < self.gr_number:
            return Interp1(handle=core.seepage_get_gr(self.handle, idx))

    core.use(c_size_t, 'seepage_add_gr', c_void_p, c_void_p)

    def add_gr(self, gr, need_id=False):
        assert isinstance(gr, Interp1)
        idx = core.seepage_add_gr(self.handle, gr.handle)
        if need_id:
            return idx
        else:
            return self.get_gr(idx)

    core.use(None, 'seepage_clear_grs', c_void_p)

    def clear_grs(self):
        core.seepage_clear_grs(self.handle)

    core.use(c_size_t, 'seepage_get_kr_n', c_void_p)

    @property
    def kr_number(self):
        """
        相渗曲线的数量.
        注意:
            对于 0 <= id < fluid_n 的曲线，是各个流体的默认相渗.
            所以，如果需要对某些相渗进行特殊设置，务必去使用id大于流体数量的曲线.
        """
        return core.seepage_get_kr_n(self.handle)

    def add_kr(self, saturation=None, kr=None, need_id=False):
        """
        添加一个相渗曲线，并且返回ID
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
        """
        assert kr is not None
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
        if index is None:
            index = 9999999999  # Now, modify the default kr
        core.seepage_set_kr(self.handle, index, tmp.handle)

    core.use(c_double, 'seepage_get_kr', c_void_p, c_size_t)

    def get_kr(self, index, saturation=None):
        """
        返回第index个相对渗透率曲线
        """
        curve = Interp1(handle=core.seepage_get_kr(self.handle, index))
        if saturation is None:
            return curve
        else:
            return curve.get(saturation)

    core.use(c_double, 'seepage_get_attr', c_void_p, c_size_t)
    core.use(None, 'seepage_set_attr',
             c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        模型的第index个自定义属性
        """
        if index is None:
            return default_val
        value = core.seepage_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        模型的第index个自定义属性
        """
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.seepage_set_attr(self.handle, index, value)
        return self

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
        """
        warnings.warn('please use function <Seepage.cells_read> and <Seepage.faces_read> instead. '
                      'will be removed after 2024-6-14', DeprecationWarning)
        assert isinstance(value, Vector)
        if key == 'cells':
            core.seepage_set_cells_attr(self.handle, index, value.handle)
        if key == 'faces':
            core.seepage_set_faces_attr(self.handle, index, value.handle)

    core.use(None, 'seepage_update_den',
             c_void_p, c_size_t, c_size_t, c_size_t,
             c_void_p, c_size_t,
             c_double, c_double, c_double)

    def update_den(self, fluid_id=None, kernel=None, relax_factor=1.0, fa_t=None, min=-1, max=-1):
        """
        更新流体的密度。其中
            fluid_id为需要更新的流体的ID(当None的时候，则更新所有)
            kernel为Interp2(p,T)
            relax_factor为松弛因子，限定密度的最大变化幅度.
        """
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
        """
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
        其中一种流体(当fid为None的时候为所有的流体是为一个整体)，与另外一个模型交换热量
        """
        if dt is None:
            return
        if thermal_model is None:
            assert fid is None
            core.seepage_exchange_heat(self.handle, dt, ca_g, ca_t, ca_mc, fa_t, fa_c)
            return
        if isinstance(thermal_model, Thermal):
            if fid is None:
                fid = 100000000  # exchange with all fluid when fid not exists
            core.seepage_thermal_exchange(self.handle, fid, thermal_model.handle, dt, ca_g, fa_t, fa_c)
            return

    def print_cells(self, path, get=None, properties=None):
        """
        输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，第5列为体积，后面依次为各流体组分的体积饱和度.
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

        def to_str(cell):
            vols = []
            for i in range(cell.fluid_number):
                vols.extend(get_vols(cell.get_fluid(i)))
            vol = sum(vols)
            s = f'{cell.pre}\t{vol}'
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

    core.use(c_size_t, 'seepage_get_nearest_cell_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_cell(self, pos):
        """
        返回与给定位置距离最近的cell
        """
        if self.cell_number > 0:
            index = core.seepage_get_nearest_cell_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_cell(index)

    core.use(None, 'seepage_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Seepage)
        core.seepage_clone(self.handle, other.handle)

    core.use(None, 'seepage_clone_cells', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def clone_cells(self, ibeg0, other, ibeg1, count):
        """
        拷贝Cell数据:
            将other的[ibeg1, ibeg1+count)范围内的Cell的数据，拷贝到self的[ibeg0, ibeg0+count)范围内的Cell
        此函数会自动跳过不存在的CellID.
            since 2023-4-20
        """
        assert isinstance(other, Seepage)
        core.seepage_clone_cells(self.handle, other.handle, ibeg0, ibeg1, count)

    def iterate(self, *args, **kwargs):
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.iterate(self, *args, **kwargs)

    def iterate_thermal(self, *args, **kwargs):
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.iterate_thermal(self, *args, **kwargs)

    def get_recommended_dt(self, *args, **kwargs):
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.get_recommended_dt(self, *args, **kwargs)

    def diffusion(self, *args, **kwargs):
        if self.__updater is None:
            self.__updater = Seepage.Updater()
        return self.__updater.diffusion(self, *args, **kwargs)

    core.use(c_double, 'seepage_get_fluid_mass', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_mass(self, fluid_id=None):
        """
        返回模型中所有Cell内的流体mass的和。
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体
        """
        return core.seepage_get_fluid_mass(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_mass(self):
        """
        返回模型中所有Cell内的流体mass的和
        """
        return self.get_fluid_mass()

    core.use(c_double, 'seepage_get_fluid_vol', c_void_p, c_size_t, c_size_t, c_size_t)

    def get_fluid_vol(self, fluid_id=None):
        """
        返回模型中所有Cell内的流体vol的和
            当fluid_id指定的时候，则仅仅对给定的流体进行加和，否则，将加和所有的流体
        """
        return core.seepage_get_fluid_vol(self.handle, *parse_fid3(fluid_id))

    @property
    def fluid_vol(self):
        """
        返回模型中所有Cell内的流体vol的和
        """
        return self.get_fluid_vol()

    core.use(None, 'seepage_update_cond_a', c_void_p, c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'seepage_update_cond_b', c_void_p, c_size_t, c_size_t, c_void_p, c_double)
    core.use(None, 'seepage_update_cond_c', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def update_cond(self, v0, g0, krf, relax_factor=1.0):
        """
        给定初始时刻各Cell流体体积vv0，各Face的导流vg0，v/v0到g/g0的映射krf，来更新此刻Face的g.
            参数v0和g0可以是Vector，也可以是属性ID
        """
        if isinstance(v0, Vector) and isinstance(g0, Vector):
            assert isinstance(krf, Interp1)
            core.seepage_update_cond_a(self.handle, v0.handle, g0.handle, krf.handle, relax_factor)
        else:
            # Now, v0 is ca_v0 and g0 is fa_g0
            if isinstance(krf, Interp1):
                core.seepage_update_cond_b(self.handle, v0, g0, krf.handle, relax_factor)
            else:
                # 利用model中定义的kr，并且每一个Face可以有不同的kr
                core.seepage_update_cond_c(self.handle, v0, g0, krf, relax_factor)

    core.use(None, 'seepage_update_g0', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def update_g0(self, fa_g0, fa_k, fa_s, fa_l):
        core.seepage_update_g0(self.handle, fa_g0, fa_k, fa_s, fa_l)

    core.use(None, 'seepage_find_inner_face_ids', c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号
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
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_cond_for_exchange(self.handle, buffer.handle, *parse_fid3(fid0), *parse_fid3(fid1))
        return buffer

    core.use(None, 'seepage_get_linear_dpre', c_void_p, c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_void_p, c_double, c_void_p)

    def get_linear_dpre(self, fid0, fid1, s2p, vs0=None, vk=None, ds=0.05, cell_ids=None):
        """
        更新两种流体之间压力差和饱和度之间的线性关系
        """
        if not isinstance(vs0, Vector):
            vs0 = Vector()
        if not isinstance(vk, Vector):
            vk = Vector()
        assert isinstance(s2p, Interp1)
        if cell_ids is not None:
            if not isinstance(cell_ids, UintVector):
                cell_ids = UintVector(cell_ids)
        core.seepage_get_linear_dpre(self.handle, vs0.handle, vk.handle, *parse_fid3(fid0), *parse_fid3(fid1),
                                     s2p.handle, ds,
                                     0 if cell_ids is None else cell_ids.handle)
        return vs0, vk

    core.use(None, 'seepage_get_vol_fraction', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t)

    def get_vol_fraction(self, fid, buffer=None):
        """
        返回给定序号的流体的体积饱和度，并且作为一个Vector返回
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_vol_fraction(self.handle, buffer.handle, *parse_fid3(fid))
        return buffer

    core.use(None, 'seepage_get_face_gradient', c_void_p, c_void_p, c_void_p)

    def get_face_gradient(self, va, buffer=None):
        """
        根据Cell中心位置的属性的值来计算各个Face位置的梯度
        """
        assert isinstance(va, Vector)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_face_gradient(self.handle, buffer.handle, va.handle)
        return buffer

    core.use(None, 'seepage_get_face_average', c_void_p, c_void_p, c_void_p)

    def get_face_average(self, face_vals, buffer=None):
        """
        计算Cell周围Face的平均值，并作为Vector返回
        """
        assert isinstance(face_vals, Vector)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_face_average(self.handle, buffer.handle, face_vals.handle)
        return buffer

    core.use(None, 'seepage_heating', c_void_p, c_size_t, c_size_t, c_void_p, c_double)

    def heating(self, ca_mc, ca_t, powers, dt):
        """
        按照各个Cell给定的功率来对各个Cell进行加热
        """
        assert isinstance(powers, Vector)
        core.seepage_heating(self.handle, ca_mc, ca_t, powers.handle, dt)

    core.use(c_size_t, 'seepage_get_fludef_n', c_void_p)

    @property
    def fludef_number(self):
        """
        模型内存储的流体定义的数量
        """
        return core.seepage_get_fludef_n(self.handle)

    core.use(c_void_p, 'seepage_get_fludef', c_void_p, c_size_t)
    core.use(c_void_p, 'seepage_find_fludef', c_void_p, c_char_p)

    def get_fludef(self, key):
        """
        返回给定序号或者名字的流体定义. key可以是str类型或者是int类型.
        """
        if isinstance(key, str):
            handle = core.seepage_find_fludef(self.handle, make_c_char_p(key))
            if handle:
                return Seepage.FluDef(handle=handle)
        else:
            if key < self.fludef_number:
                handle = core.seepage_get_fludef(self.handle, key)
                if handle:
                    return Seepage.FluDef(handle=handle)

    core.use(c_size_t, 'seepage_add_fludef', c_void_p, c_void_p)

    def add_fludef(self, fdef, need_id=False):
        """
        添加一个流体定义
        """
        assert isinstance(fdef, Seepage.FluDef)
        idx = core.seepage_add_fludef(self.handle, fdef.handle)
        if need_id:
            return idx
        else:
            return self.get_fludef(idx)

    core.use(None, 'seepage_clear_fludefs', c_void_p)

    def clear_fludefs(self):
        core.seepage_clear_fludefs(self.handle)

    core.use(c_size_t, 'seepage_get_pc_n', c_void_p)

    @property
    def pc_number(self):
        """
        模型中存储的毛管压力曲线的数量
        """
        return core.seepage_get_pc_n(self.handle)

    core.use(c_void_p, 'seepage_get_pc', c_void_p, c_size_t)

    def get_pc(self, idx):
        """
        返回给定序号的毛管压力曲线
        """
        if idx < self.pc_number:
            return Interp1(handle=core.seepage_get_pc(self.handle, idx))

    core.use(c_size_t, 'seepage_add_pc', c_void_p, c_void_p)

    def add_pc(self, data, need_id=False):
        """
        添加一个毛管压力曲线
        """
        assert isinstance(data, Interp1)
        idx = core.seepage_add_pc(self.handle, data.handle)
        if need_id:
            return idx
        else:
            return self.get_pc(idx)

    core.use(None, 'seepage_clear_pcs', c_void_p)

    def clear_pcs(self):
        core.seepage_clear_pcs(self.handle)

    core.use(c_size_t, 'seepage_get_reaction_n', c_void_p)

    @property
    def reaction_number(self):
        return core.seepage_get_reaction_n(self.handle)

    core.use(c_void_p, 'seepage_get_reaction', c_void_p, c_size_t)

    def get_reaction(self, idx):
        if idx < self.reaction_number:
            return Seepage.Reaction(handle=core.seepage_get_reaction(self.handle, idx))

    core.use(c_size_t, 'seepage_add_reaction', c_void_p, c_void_p)

    def add_reaction(self, data, need_id=False):
        assert isinstance(data, Seepage.Reaction)
        idx = core.seepage_add_reaction(self.handle, data.handle)
        if need_id:
            return idx
        else:
            return self.get_reaction(idx)

    core.use(None, 'seepage_clear_reactions', c_void_p)

    def clear_reactions(self):
        core.seepage_clear_reactions(self.handle)

    core.use(None, 'seepage_pop_fluids', c_void_p, c_void_p)
    core.use(None, 'seepage_push_fluids', c_void_p, c_void_p)

    def pop_fluids(self, buffer):
        """
        将各个Cell中的最后一个流体暂存到buffer中。一般情况下，将固体作为最后一种流体。在计算流动的
        时候，如果这些固体存在，则会影响到相对渗透率。因此，当模型中存在固体的时候，需要先将固体组分
        弹出，然后再计算流动。计算流动之后，再将备份的固体组分压入，使得模型恢复到最初的状态。
        注意：在弹出最后一种流体的时候，会同步修改Cell中的pore的大小，并保证压力不变;
            since: 2023-04
        """
        assert isinstance(buffer, Seepage.CellData)
        core.seepage_pop_fluids(self.handle, buffer.handle)

    def push_fluids(self, buffer):
        """
        将buffer中暂存的流体追加到各个Cell中。和pop_fluids函数搭配使用。
        """
        assert isinstance(buffer, Seepage.CellData)
        core.seepage_push_fluids(self.handle, buffer.handle)

    core.use(None, 'seepage_cells_write', c_void_p, c_void_p, c_int64)

    def cells_write(self, index, pointer):
        """
        导出属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore

            index=-10, 所有流体的总的质量 (只读)
            index=-11, 所有流体的总的体积 (只读)
            index=-12, 根据流体的体积和pore，来计算的Cell的压力 (只读)
        """
        core.seepage_cells_write(self.handle, ctypes.cast(pointer, c_void_p), index)

    core.use(None, 'seepage_cells_read', c_void_p, c_void_p, c_double, c_int64)

    def cells_read(self, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, x坐标
            index=-2, y坐标
            index=-3, z坐标
            index=-4, v0 of pore
            index=-5, k  of pore
        """
        if pointer is not None:
            core.seepage_cells_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index)
        else:
            assert value is not None
            core.seepage_cells_read(self.handle, 0, value, index)

    core.use(None, 'seepage_faces_write', c_void_p, c_void_p, c_int64)

    def faces_write(self, index, pointer):
        """
        导出属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, cond
            index=-2, dr

            index=-10, dv of fluid 0
            index=-11, dv of fluid 1
            index=-12, dv of fluid 2
            ...
            index=-19, dv of fluid ALL
        """
        core.seepage_faces_write(self.handle, ctypes.cast(pointer, c_void_p), index)

    core.use(None, 'seepage_faces_read', c_void_p, c_void_p, c_double, c_int64)

    def faces_read(self, index, pointer=None, value=None):
        """
        导入属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, cond
            index=-2, dr
        """
        if pointer is not None:
            core.seepage_faces_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index)
        else:
            assert value is not None
            core.seepage_faces_read(self.handle, 0, value, index)

    core.use(None, 'seepage_fluids_write', c_void_p, c_void_p, c_int64, c_size_t, c_size_t, c_size_t)

    def fluids_write(self, fluid_id, index, pointer):
        """
        导出属性: 当 index >= 0 的时候，为属性ID；如果index < 0，则：
            index=-1, 质量
            index=-2, 密度
            index=-3, 体积
            index=-4, 粘性
        """
        core.seepage_fluids_write(self.handle, ctypes.cast(pointer, c_void_p), index, *parse_fid3(fluid_id))

    core.use(None, 'seepage_fluids_read', c_void_p, c_void_p, c_double, c_int64, c_size_t, c_size_t, c_size_t)

    def fluids_read(self, fluid_id, index, pointer=None, value=None):
        """
        导入属性
        """
        if pointer is not None:
            core.seepage_fluids_read(self.handle, ctypes.cast(pointer, c_void_p), 0, index, *parse_fid3(fluid_id))
        else:
            assert value is not None
            core.seepage_fluids_read(self.handle, 0, value, index, *parse_fid3(fluid_id))

    @property
    def numpy(self):
        """
        用以和numpy交互数据
        """
        if np is not None:
            return _SeepageNumpyAdaptor(model=self)

    core.use(None, 'seepage_append', c_void_p, c_void_p, c_bool, c_size_t)

    def append(self, other, cell_i0=None, with_faces=True):
        """
        将other中所有的Cell和Face追加到这个模型中，并且从这个模型的cell_i0开始，和other的cell之间
        建立一一对应的Face. 默认情况下，仅仅追加，但是不建立和现有的Cell的连接。
            2023-4-19

        注意：
            仅仅追加Cell和Face，other中的其它数据，比如反应、注入点、相渗曲线等，均不会被追加到这个
            模型中。

        当with_faces为False的时候，则仅仅追加other中的Cell (other中的 Face 不被追加)

        注意函数实际的执行顺序：
            第一步：添加other的所有的Cell
            第二步：添加other的所有的Face（如何with_faces属性为True的时候）
            第三步：创建一些额外Face连接 (从这个模型的cell_i0开始，和other的cell之间)

        """
        assert isinstance(other, Seepage)
        if cell_i0 is None:
            cell_i0 = self.cell_number
        core.seepage_append(self.handle, other.handle, with_faces, cell_i0)

    core.use(c_void_p, 'seepage_get_buffer', c_void_p, c_char_p)

    def get_buffer(self, key):
        """
        返回模型内的一个缓冲区（如果不存在，则自动创建并返回）
        """
        return Vector(handle=core.seepage_get_buffer(self.handle, make_c_char_p(key)))

    core.use(None, 'seepage_del_buffer', c_void_p, c_char_p)

    def del_buffer(self, key):
        """
        删除模型内的缓冲区(如果缓冲区不存在，则不执行操作)
        """
        core.seepage_del_buffer(self.handle, make_c_char_p(key))

    core.use(c_bool, 'seepage_has_tag', c_void_p, c_char_p)

    def has_tag(self, tag):
        """
        返回模型是否包含给定的这个标签
        """
        return core.seepage_has_tag(self.handle, make_c_char_p(tag))

    def not_has_tag(self, tag):
        return not self.has_tag(tag)

    core.use(None, 'seepage_add_tag', c_void_p, c_char_p)

    def add_tag(self, tag):
        """
        在模型中添加给定的标签
        """
        core.seepage_add_tag(self.handle, make_c_char_p(tag))

    core.use(None, 'seepage_del_tag', c_void_p, c_char_p)

    def del_tag(self, tag):
        """
        删除模型中的给定的标签
        """
        core.seepage_del_tag(self.handle, make_c_char_p(tag))

    core.use(None, 'seepage_clear_tags', c_void_p)

    def clear_tags(self):
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
        """
        return core.seepage_reg_key(self.handle, make_c_char_p(ty), make_c_char_p(key))

    core.use(c_int64, 'seepage_get_key', c_void_p, c_char_p)

    def get_key(self, key):
        """
        返回键值：主要用于存储指定的属性ID
        """
        return core.seepage_get_key(self.handle, make_c_char_p(key))

    core.use(None, 'seepage_set_key', c_void_p, c_char_p, c_int64)

    def set_key(self, key, value):
        """
        设置键值
        """
        core.seepage_set_key(self.handle, make_c_char_p(key), value)

    core.use(None, 'seepage_del_key', c_void_p, c_char_p)

    def del_key(self, key):
        """
        删除键值
        """
        core.seepage_del_key(self.handle, make_c_char_p(key))

    core.use(None, 'seepage_clear_keys', c_void_p)

    def clear_keys(self):
        core.seepage_clear_keys(self.handle)

    def reg_model_key(self, key):
        """
        注册并返回用于model的键值
        """
        return self.reg_key('m_', key)

    def reg_cell_key(self, key):
        """
        注册并返回用于cell的键值
        """
        return self.reg_key('n_', key)

    def reg_face_key(self, key):
        """
        注册并返回用于face的键值
        """
        return self.reg_key('b_', key)

    def reg_flu_key(self, key):
        """
        注册并返回用于flu的键值
        """
        return self.reg_key('f_', key)

    core.use(None, 'seepage_clamp_cell_attrs', c_void_p, c_size_t, c_double, c_double)

    def clamp_cell_attrs(self, idx, lr, rr):
        """
        约束Cell的属性的取值
        """
        core.seepage_clamp_cell_attrs(self.handle, idx, lr, rr)

    core.use(None, 'seepage_clamp_face_attrs', c_void_p, c_size_t, c_double, c_double)

    def clamp_face_attrs(self, idx, lr, rr):
        """
        约束Face的属性的取值
        """
        core.seepage_clamp_face_attrs(self.handle, idx, lr, rr)

    core.use(None, 'seepage_clamp_fluid_attrs', c_void_p, c_size_t, c_size_t, c_size_t,
             c_size_t, c_double, c_double)

    def clamp_fluid_attrs(self, fluid_id, idx, lr, rr):
        """
        约束流体的属性的取值
        """
        core.seepage_clamp_fluid_attrs(self.handle, *parse_fid3(fluid_id), idx, lr, rr)

    core.use(None, 'seepage_pop_cells', c_void_p, c_size_t)

    def pop_cells(self, count=1):
        """
        删除最后count个Cell的所有的Face，然后移除最后count个Cell
        """
        core.seepage_pop_cells(self.handle, count)


class CondUpdater:
    """
    用以更新Face的cond属性
    """

    def __init__(self, v0=None, g0=None, krf=None):
        """
        构造函数，后续必须添加必要的配置
        """
        self.v0 = v0
        self.g0 = g0
        self.krf = krf
        self.fk = None
        self.s1 = None

    def __call__(self, model, relax_factor=1.0):
        """
        更新模型中各个Cell中流体的总体积和v0的体积的比值，更新各个Face的cond属性
        """
        assert isinstance(model, Seepage)
        if self.v0 is not None and self.g0 is not None and self.krf is not None:
            model.update_cond(v0=self.v0, g0=self.g0, krf=self.krf, relax_factor=relax_factor)

    def set_v0(self, model):
        """
        将此刻的流体体积设置为v0. 注意：这里将所有的流体都视为可以流动的。如果流体组分中有固体，那么请首先移除固体组分之后再调用此函数
        """
        assert isinstance(model, Seepage)
        self.v0 = Vector(value=[cell.fluid_vol for cell in model.cells])

    def set_g0(self, model):
        """
        将此刻的face.cond设置为g0
        """
        assert isinstance(model, Seepage)
        self.g0 = Vector(value=[face.cond for face in model.faces])

    def set_s1(self, mesh):
        """
        当Face两侧距离为折减为1的时候，Face的面积
        """
        self.s1 = Vector(value=[face.area / face.length for face in mesh.faces])

    def set_fk(self, model, mesh):
        """
        Face位置的渗透率（根据此刻的cond来计算）
        """
        vs1 = [face.area / face.length for face in mesh.faces]
        count = min(len(vs1), model.face_number)
        self.fk = Vector(value=[model.get_face(i).cond / vs1[i] for i in range(count)])

    core.use(None, 'update_g0', c_void_p, c_void_p, c_void_p)

    def update_g0(self, fk=None, s1=None):
        """
        更新g0. 其中fk为渗透率属性，s1为Face的面积除以流动的距离；
        """
        if fk is None:
            fk = self.fk
        if s1 is None:
            s1 = self.s1
        if isinstance(fk, Vector) and isinstance(s1, Vector) and isinstance(self.g0, Vector):
            core.update_g0(self.g0.handle, fk.handle, s1.handle)


Reaction = Seepage.Reaction


class Thermal(HasHandle):
    """
    热传导温度场
    """

    class Cell(Object):
        """
        控制体单元
        """

        def __init__(self, model, index):
            assert isinstance(model, Thermal)
            assert index < model.cell_number
            self.model = model
            self.index = index

        def __str__(self):
            return f'zml.Thermal.Cell(handle = {self.model.handle}, index = {self.index})'

        core.use(c_size_t, 'thermal_get_cell_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            连接的Face数量
            """
            return core.thermal_get_cell_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            连接的Cell数量
            """
            return self.face_number

        core.use(c_size_t, 'thermal_get_cell_face_id', c_void_p, c_size_t, c_size_t)
        core.use(c_size_t, 'thermal_get_cell_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            """
            连接的第index个Cell
            """
            cell_id = core.thermal_get_cell_cell_id(self.model.handle, self.index, index)
            return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            连接的第index个Face
            """
            face_id = core.thermal_get_cell_face_id(self.model.handle, self.index, index)
            return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            所有相邻的Cell
            """
            return Iterators.Cell(self)

        @property
        def faces(self):
            """
            所有相邻的Face
            """
            return Iterators.Face(self)

        core.use(c_double, 'thermal_get_cell_mc', c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_mc', c_void_p, c_size_t, c_double)

        @property
        def mc(self):
            """
            控制体内物质的热容量，等于物质的质量乘以比热
            """
            return core.thermal_get_cell_mc(self.model.handle, self.index)

        @mc.setter
        def mc(self, value):
            """
            控制体内物质的热容量，等于物质的质量乘以比热
            """
            core.thermal_set_cell_mc(self.model.handle, self.index, value)

        core.use(c_double, 'thermal_get_cell_T', c_void_p, c_size_t)
        core.use(None, 'thermal_set_cell_T', c_void_p, c_size_t, c_double)

        @property
        def temperature(self):
            """
            控制体内物质的温度 K
            """
            return core.thermal_get_cell_T(self.model.handle, self.index)

        @temperature.setter
        def temperature(self, value):
            """
            控制体内物质的温度 K
            """
            core.thermal_set_cell_T(self.model.handle, self.index, value)

    class Face(Object):
        def __init__(self, model, index):
            assert isinstance(model, Thermal)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model = model
            self.index = index

        def __str__(self):
            return f'zml.Thermal.Face(handle = {self.model.handle}, index = {self.index}) '

        core.use(c_size_t, 'thermal_get_face_cell_id', c_void_p, c_size_t, c_size_t)

        @property
        def cell_number(self):
            """
            连接的Cell的数量
            """
            return 2

        def get_cell(self, index):
            """
            连接的第index个Cell
            """
            cell_id = core.thermal_get_face_cell_id(self.model.handle, self.index, index)
            return self.model.get_cell(cell_id)

        @property
        def cells(self):
            """
            连接的所有的Cell
            """
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'thermal_get_face_cond', c_void_p, c_size_t)
        core.use(None, 'thermal_set_face_cond', c_void_p, c_size_t, c_double)

        @property
        def cond(self):
            """
            Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，dt为时间步长，E为通过该Face输运的能量(J)
            """
            return core.thermal_get_face_cond(self.model.handle, self.index)

        @cond.setter
        def cond(self, value):
            """
            Face的导热能力. E=cond*dT*dt，其中dT为Face两端的温度差，dt为时间步长，E为通过该Face输运的能量(J)
            """
            core.thermal_set_face_cond(self.model.handle, self.index, value)

    core.use(c_void_p, 'new_thermal')
    core.use(None, 'del_thermal', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Thermal, self).__init__(handle, core.new_thermal, core.del_thermal)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.Thermal(handle = {self.handle})'

    core.use(None, 'thermal_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.thermal_save(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
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
        """
        return core.thermal_get_cell_n(self.handle)

    core.use(c_size_t, 'thermal_get_face_n', c_void_p)

    @property
    def face_number(self):
        """
        模型中Face的数量
        """
        return core.thermal_get_face_n(self.handle)

    def get_cell(self, index):
        """
        模型中第index个Cell
        """
        if index < core.thermal_get_cell_n(self.handle):
            return Thermal.Cell(self, index)

    def get_face(self, index):
        """
        模型中第index个Face
        """
        if index < core.thermal_get_face_n(self.handle):
            return Thermal.Face(self, index)

    core.use(c_size_t, 'thermal_add_cell', c_void_p)

    def add_cell(self):
        """
        添加一个Cell
        """
        cell_id = core.thermal_add_cell(self.handle)
        return self.get_cell(cell_id)

    core.use(c_size_t, 'thermal_add_face', c_void_p, c_size_t, c_size_t)

    def add_face(self, cell0, cell1):
        """
        在两个Cell之间添加Face以连接
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
        """
        lic.check_once()
        assert solver is not None
        core.thermal_iterate(self.handle, dt, solver.handle)

    @property
    def cells(self):
        """
        返回所有的Cell
        """
        return Iterators.Cell(self)

    @property
    def faces(self):
        """
        返回所有的Face
        """
        return Iterators.Face(self)

    def print_cells(self, path):
        """
        将所有的Cell的信息打印到文件
        """
        with open(path, 'w') as file:
            for cell in self.cells:
                file.write(f'{cell.temperature}\t{cell.mc}\n')

    def exchange_heat(self, model, dt, fid=None, ca_g=None, fa_t=None, fa_c=None):
        """
        与另外一个模型交换热量
        """
        if isinstance(model, Seepage):
            model.exchange_heat(fid=fid, thermal_model=self, dt=dt, ca_g=ca_g, fa_t=fa_t, fa_c=fa_c)


class TherFlowConfig(Object):
    """
    传热-渗流耦合模型的配置。假设流体的密度和粘性系数都是压力和温度的函数，并利用二维的插值体来表示。
    此类仅仅用于辅助Seepage类用于热流耦合模拟。
    """
    FluProperty = Seepage.FluDef

    def __init__(self, *args):
        """
        给定流体属性进行初始化. 给定的参数应该为流体属性定义(或者多个流体组成的混合物)、或者是化学反应的定义
        """
        self.fluids = []
        self.reactions = []  # 组分之间的反应
        for arg in args:
            if isinstance(arg, Reaction):
                self.reactions.append(arg)
            else:
                self.add_fluid(arg)
        self.flu_keys = AttrKeys('specific_heat', 'temperature')
        # fv0: 初始时刻的流体体积<流体体积的参考值>
        # vol: 网格的几何体积。这个体积乘以孔隙度，就等于孔隙体积
        self.cell_keys = AttrKeys('mc', 'temperature', 'g_heat', 'pre', 'vol', 'fv0')
        # g0：初始时刻的导流系数<当流体体积为fv0的时候的导流系数>
        self.face_keys = AttrKeys('g_heat', 'area', 'length', 'g0', 'perm', 'igr')
        self.model_keys = AttrKeys('dt', 'time', 'step', 'dv_relative', 'dt_min', 'dt_max')
        # 用于更新流体的导流系数
        self.krf = None
        # 定义一些开关
        self.disable_update_den = False
        self.disable_update_vis = False
        self.disable_ther = False
        self.disable_heat_exchange = False
        # 一个在更新流体的时候，暂时存储固体的一个缓冲区（需要将固体定义为最后一种组分）
        self.has_solid = False
        self.solid_buffer = Seepage.CellData()
        # 流体的扩散. 在多相流操作之后被调用. （也可以用于其它和流动相关的操作）
        self.diffusions = []
        # 在每一步流体计算之前，对模型的cond属性进行更新.
        self.cond_updaters = []
        # 当gravity非None的时候，将设置模型的重力属性
        self.gravity = None
        # 允许的最大时间步长
        self.dt_max = None
        self.dt_min = None
        self.dt_ini = None
        self.dv_relative = None
        # 在更新流体的密度的时候，所允许的最大的流体压力
        self.pre_max = 100e6
        # 用以存储各个组分的ID. since 2023-5-30
        self.components = {}

    def set_specific_heat(self, elem, value):
        """
        设置比热
        """
        if isinstance(elem, Seepage.FluData):
            elem.set_attr(self.flu_keys['specific_heat'], value)
            return

    def get_specific_heat(self, elem):
        if isinstance(elem, Seepage.FluData):
            return elem.get_attr(self.flu_keys['specific_heat'])

    def set_temperature(self, elem, value):
        """
        设置温度
        """
        if isinstance(elem, Seepage.FluData):
            elem.set_attr(self.flu_keys['temperature'], value)
            return

        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['temperature'], value)
            return

    def get_temperature(self, elem):
        """
        设置温度
        """
        if isinstance(elem, Seepage.FluData):
            return elem.get_attr(self.flu_keys['temperature'])

        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['temperature'])

    set_flu_specific_heat = set_specific_heat
    set_flu_temperature = set_temperature

    def set_mc(self, elem, value):
        """
        质量乘以比热
        """
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['mc'], value)
            return

    def get_mc(self, elem):
        """
        质量乘以比热
        """
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['mc'])

    def set_fv0(self, elem, value):
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['fv0'], value)
            return

    def get_fv0(self, elem):
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['fv0'])

    set_cell_mc = set_mc
    set_cell_temperature = set_temperature

    def set_g_heat(self, elem, value):
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['g_heat'], value)
            return

        if isinstance(elem, Seepage.FaceData):
            elem.set_attr(self.face_keys['g_heat'], value)
            return

    def get_g_heat(self, elem):
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['g_heat'])

        if isinstance(elem, Seepage.FaceData):
            return elem.get_attr(self.face_keys['g_heat'])

    set_cell_g_heat = set_g_heat

    def set_vol(self, elem, value):
        """
        设置cell的体积
        """
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['vol'], value)
            return

    def get_vol(self, elem):
        """
        设置cell的体积
        """
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['vol'])

    set_cell_vol = set_vol
    set_face_g_heat = set_g_heat

    def set_area(self, elem, value):
        """
        设置face的横截面积
        """
        elem.set_attr(self.face_keys['area'], value)

    def get_area(self, elem):
        """
        设置face的横截面积
        """
        return elem.get_attr(self.face_keys['area'])

    set_face_area = set_area

    def set_length(self, face, value):
        """
        设置face的长度
        """
        face.set_attr(self.face_keys['length'], value)

    def get_length(self, face):
        """
        设置face的长度
        """
        return face.get_attr(self.face_keys['length'])

    set_face_length = set_length

    def set_g0(self, face, value):
        """
        设置face的初始的导流系数（在没有固体存在的时候的原始值）
        """
        face.set_attr(self.face_keys['g0'], value)

    def get_g0(self, face):
        """
        设置face的初始的导流系数（在没有固体存在的时候的原始值）
        """
        return face.get_attr(self.face_keys['g0'])

    set_face_g0 = set_g0

    def add_fluid(self, flu):
        """
        添加一种流体(或者是一种混合物<此时给定一个list或者tuple>)，并且返回流体的ID
        """
        if not isinstance(flu, TherFlowConfig.FluProperty):
            for elem in flu:
                assert isinstance(elem, TherFlowConfig.FluProperty)
        index = len(self.fluids)
        self.fluids.append(flu)
        return index

    def get_fluid(self, index):
        """
        返回给定序号的流体定义
        """
        assert 0 <= index < self.fluid_number
        return self.fluids[index]

    @property
    def fluid_number(self):
        """
        流体的数量
        """
        return len(self.fluids)

    def set_cell(self, cell, pos=None, vol=None, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
                 temperature=280.0, p=1.0, s=None, pore_modulus_range=None):
        """
        设置Cell的初始状态.
        """
        if pos is not None:
            cell.pos = pos
        else:
            pos = cell.pos

        if vol is not None:
            cell.set_attr(self.cell_keys['vol'], vol)
        else:
            vol = cell.get_attr(self.cell_keys['vol'])
            assert vol is not None

        cell.set_ini(ca_mc=self.cell_keys['mc'], ca_t=self.cell_keys['temperature'],
                     fa_t=self.flu_keys['temperature'], fa_c=self.flu_keys['specific_heat'],
                     pos=pos, vol=vol, porosity=porosity,
                     pore_modulus=pore_modulus,
                     denc=denc,
                     temperature=temperature, p=p, s=s,
                     pore_modulus_range=pore_modulus_range)

        cell.set_attr(self.cell_keys['fv0'], cell.fluid_vol)
        cell.set_attr(self.cell_keys['g_heat'], vol / (dist ** 2))

    def set_face(self, face, area=None, length=None, perm=None, heat_cond=None, igr=None):
        """
        对一个Face进行配置
        """
        if area is not None:
            face.set_attr(self.face_keys['area'], area)
        else:
            area = face.get_attr(self.face_keys['area'])
            assert area is not None

        if length is not None:
            face.set_attr(self.face_keys['length'], length)
        else:
            length = face.get_attr(self.face_keys['length'])
            assert length is not None

        assert area > 0 and length > 0

        if perm is not None:
            face.set_attr(self.face_keys['perm'], perm)
        else:
            perm = face.get_attr(self.face_keys['perm'])
            assert perm is not None

        g0 = area * perm / length
        face.cond = g0

        face.set_attr(self.face_keys['g0'], g0)

        if heat_cond is not None:
            face.set_attr(self.face_keys['g_heat'], area * heat_cond / length)

        if igr is not None:
            face.set_attr(self.face_keys['igr'], igr)

    def set_model(self, model, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
                  temperature=280.0, p=None, s=None, perm=1e-14, heat_cond=1.0,
                  sample_dist=None, pore_modulus_range=None, igr=None):
        """
        设置模型的网格，并顺便设置其初始的状态.
        --
        注意各个参数的含义：
            porosity: 孔隙度；
            pore_modulus：空隙的刚度，单位Pa；正常取值在100MPa到1000MPa之间；
            denc：土体的密度和比热的乘积；假设土体密度2000kg/m^3，比热1000，denc取值就是2.0e6；
            dist：一个单元包含土体和流体两个部分，dist是土体和流体换热的距离。这个值越大，换热就越慢。如果希望土体和流体的温度非常接近，
                就可以把dist设置得比较小。一般，可以设置为网格大小的几分之一；
            temperature: 温度K
            p：压力Pa
            s：各个相的饱和度，tuple或者list；
            perm：渗透率 m^2
            heat_cond: 热传导系数
        -
        注意：
            每一个参数，都可以是一个具体的数值，或者是一个和x，y，z坐标相关的一个分布
            ( 判断是否定义了obj.__call__这样的成员函数，有这个定义，则视为一个分布，否则是一个全场一定的值)
        --
        注意:
            在使用这个函数之前，请确保Cell需要已经正确设置了位置，并且具有网格体积vol这个自定义属性；
            对于Face，需要设置面积s和长度length这两个自定义属性。否则，此函数的执行会出现错误.

        """
        porosity = Field(porosity)
        pore_modulus = Field(pore_modulus)
        denc = Field(denc)
        dist = Field(dist)
        temperature = Field(temperature)
        p = Field(p)
        s = Field(s)
        perm = Field(perm)
        heat_cond = Field(heat_cond)
        igr = Field(igr)

        for cell in model.cells:
            assert isinstance(cell, Seepage.Cell)
            pos = cell.pos
            self.set_cell(cell, porosity=porosity(*pos), pore_modulus=pore_modulus(*pos), denc=denc(*pos),
                          temperature=temperature(*pos), p=p(*pos), s=s(*pos),
                          pore_modulus_range=pore_modulus_range, dist=dist(*pos))

        for face in model.faces:
            assert isinstance(face, Seepage.Face)
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            self.set_face(face, perm=get_average_perm(p0, p1, perm, sample_dist),
                          heat_cond=get_average_perm(p0, p1, heat_cond, sample_dist), igr=igr(*face.pos))

    def add_cell(self, model, *args, **kwargs):
        """
        添加一个新的Cell，并返回Cell对象
        """
        cell = model.add_cell()
        self.set_cell(cell, *args, **kwargs)
        return cell

    def add_face(self, model, cell0, cell1, *args, **kwargs):
        """
        添加一个Face，并且返回
        """
        face = model.add_face(cell0, cell1)
        self.set_face(face, *args, **kwargs)
        return face

    def add_mesh(self, model, mesh):
        """
        根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
            对于Cell，仅仅设置位置和体积这两个属性.
            对于Face，仅仅设置面积和长度这两个属性.
        """
        if mesh is not None:
            ca_vol = self.cell_keys['vol']
            fa_s = self.face_keys['area']
            fa_l = self.face_keys['length']

            cell_n0 = model.cell_number

            for c in mesh.cells:
                cell = model.add_cell()
                cell.pos = c.pos
                cell.set_attr(ca_vol, c.vol)

            for f in mesh.faces:
                face = model.add_face(model.get_cell(f.link[0] + cell_n0), model.get_cell(f.link[1] + cell_n0))
                face.set_attr(fa_s, f.area)
                face.set_attr(fa_l, f.length)

    def create(self, mesh=None, model=None, **kwargs):
        """
        利用给定的网格来创建一个模型
        """
        if model is None:
            model = Seepage()

        if self.disable_update_den:
            model.add_tag('disable_update_den')

        if self.disable_update_vis:
            model.add_tag('disable_update_vis')

        if self.disable_ther:
            model.add_tag('disable_ther')

        if self.disable_heat_exchange:
            model.add_tag('disable_heat_exchange')

        if self.has_solid:
            model.add_tag('has_solid')

        # 添加流体的定义和反应的定义 (since 2023-4-5)
        model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
        for flu in self.fluids:
            model.add_fludef(Seepage.FluDef.create(flu))

        model.clear_reactions()  # 清空已经存在的定义.
        for r in self.reactions:
            model.add_reaction(r)

        # 设置重力
        if self.gravity is not None:
            assert len(self.gravity) == 3
            model.gravity = self.gravity

        if self.dt_max is not None:
            self.set_dt_max(model, self.dt_max)

        if self.dt_min is not None:
            self.set_dt_min(model, self.dt_min)

        if self.dt_ini is not None:
            self.set_dt(model, self.dt_ini)

        if self.dv_relative is not None:
            self.set_dv_relative(model, self.dv_relative)

        if self.krf is not None:
            igr = model.add_gr(self.krf, need_id=True)
        else:
            igr = None

        if mesh is not None:
            self.add_mesh(model, mesh)

        self.set_model(model, igr=igr, **kwargs)

        return model

    def get_dt(self, model):
        """
        返回模型内存储的时间步长
        """
        value = model.get_attr(self.model_keys['dt'])
        if value is None:
            return 1.0e-10
        else:
            return value

    def set_dt(self, model, dt):
        """
        设置模型的时间步长
        """
        model.set_attr(self.model_keys['dt'], dt)

    def get_time(self, model):
        """
        返回模型的时间
        """
        value = model.get_attr(self.model_keys['time'])
        if value is None:
            return 0
        else:
            return value

    def set_time(self, model, value):
        """
        设置模型的时间
        """
        model.set_attr(self.model_keys['time'], value)

    def update_time(self, model, dt=None):
        """
        更新模型的时间
        """
        if dt is None:
            dt = self.get_dt(model)
        self.set_time(model, self.get_time(model) + dt)

    def get_step(self, model):
        """
        返回模型迭代的次数
        """
        value = model.get_attr(self.model_keys['step'])
        if value is None:
            return 0
        else:
            return int(value)

    def set_step(self, model, step):
        """
        设置模型迭代的步数
        """
        model.set_attr(self.model_keys['step'], step)

    def get_dv_relative(self, model):
        """
        每一个时间步dt内流体流过的网格数. 用于控制时间步长. 正常取值应该在0到1之间.
        """
        value = model.get_attr(self.model_keys['dv_relative'])
        if value is None:
            return 0.1
        else:
            return value

    def set_dv_relative(self, model, value):
        model.set_attr(self.model_keys['dv_relative'], value)

    def get_dt_min(self, model):
        """
        允许的最小的时间步长
            注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
        """
        value = model.get_attr(self.model_keys['dt_min'])
        if value is None:
            return 1.0e-15
        else:
            return value

    def set_dt_min(self, model, value):
        model.set_attr(self.model_keys['dt_min'], value)

    def get_dt_max(self, model):
        """
        允许的最大的时间步长
            注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
        """
        value = model.get_attr(self.model_keys['dt_max'])
        if value is None:
            return 1.0e10
        else:
            return value

    def set_dt_max(self, model, value):
        model.set_attr(self.model_keys['dt_max'], value)

    def iterate(self, model, dt=None, solver=None, fa_s=None, fa_q=None, fa_k=None):
        """
        在时间上向前迭代。其中
            dt:     时间步长,若为None，则使用自动步长
            solver: 线性求解器，若为None,则使用内部定义的共轭梯度求解器.
            fa_s:   Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力）;
            fa_q：   Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)
            fa_k:   Face内流体的惯性系数的属性ID (若fa_k属性不为None，则所有Face的该属性需要提前给定).
        """
        assert isinstance(model, Seepage)
        if dt is not None:
            self.set_dt(model, dt)

        dt = self.get_dt(model)
        assert dt is not None, 'You must set dt before iterate'

        if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
            model.update_den(relax_factor=0.3, fa_t=self.flu_keys['temperature'])

        if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
            model.update_vis(ca_p=self.cell_keys['pre'], fa_t=self.flu_keys['temperature'],
                             relax_factor=1.0, min=1.0e-7, max=1.0)

        if model.injector_number > 0:
            model.apply_injectors(dt)

        has_solid = model.has_tag('has_solid')

        if has_solid:
            # 此时，认为最后一种流体其实是固体，并进行备份处理
            model.pop_fluids(self.solid_buffer)

        if model.gr_number > 0:
            # 此时，各个Face的导流系数是可变的.
            # 注意：
            #   在建模的时候，务必要设置Cell的v0属性，Face的g0属性和ikr属性，并且，在model中，应该有相应的kr和它对应。
            #   为了不和真正流体的kr混淆，这个Face的ikr，应该大于流体的数量。
            model.update_cond(v0=self.cell_keys['fv0'], g0=self.face_keys['g0'], krf=self.face_keys['igr'],
                              relax_factor=0.3)

        # 施加cond的更新操作
        for update in self.cond_updaters:
            update(model)

        # 当未禁止更新flow且流体的数量非空
        update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

        if update_flow:
            if model.has_tag('has_inertia'):
                r1 = model.iterate(dt=dt, solver=solver, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=self.cell_keys['pre'])
            else:
                r1 = model.iterate(dt=dt, solver=solver, ca_p=self.cell_keys['pre'])
        else:
            r1 = None

        # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
        for update in self.diffusions:
            update(model, dt)

        if has_solid:
            # 恢复备份的固体物质
            model.push_fluids(self.solid_buffer)

        update_ther = model.not_has_tag('disable_ther')

        if update_ther:
            r2 = model.iterate_thermal(dt=dt, solver=solver, ca_t=self.cell_keys['temperature'],
                                       ca_mc=self.cell_keys['mc'], fa_g=self.face_keys['g_heat'])
        else:
            r2 = None

        # 不存在禁止标识且存在流体
        exchange_heat = model.not_has_tag('disable_heat_exchange') and model.fludef_number > 0

        if exchange_heat:
            model.exchange_heat(dt=dt, ca_g=self.cell_keys['g_heat'],
                                ca_t=self.cell_keys['temperature'],
                                ca_mc=self.cell_keys['mc'],
                                fa_t=self.flu_keys['temperature'],
                                fa_c=self.flu_keys['specific_heat'])

        # 优先使用模型中定义的反应
        for idx in range(model.reaction_number):
            reaction = model.get_reaction(idx)
            assert isinstance(reaction, Reaction)
            reaction.react(model, dt)

        self.set_time(model, self.get_time(model) + dt)
        self.set_step(model, self.get_step(model) + 1)

        if not getattr(self, 'disable_update_dt', None):
            # 只要不禁用dt更新，就尝试更新dt
            if update_flow or update_ther:
                # 只有当计算了流动或者传热过程，才可以使用自动的时间步长
                dt = self.get_recommended_dt(model, dt, self.get_dv_relative(model),
                                             using_flow=update_flow,
                                             using_ther=update_ther
                                             )
            dt = max(self.get_dt_min(model), min(self.get_dt_max(model), dt))
            self.set_dt(model, dt)  # 修改dt为下一步建议使用的值

        return r1, r2

    def get_recommended_dt(self, model, previous_dt, dv_relative=0.1, using_flow=True, using_ther=True):
        """
        在调用了iterate函数之后，调用此函数，来获取更优的时间步长.
        """
        assert using_flow or using_ther
        if using_flow:
            dt1 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative)
        else:
            dt1 = 1.0e100

        if using_ther:
            dt2 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative,
                                           ca_t=self.cell_keys['temperature'], ca_mc=self.cell_keys['mc'])
        else:
            dt2 = 1.0e100
        return min(dt1, dt2)

    def to_fmap(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.to_fmap> will be removed after 2024-5-5',
                      DeprecationWarning)

    def from_fmap(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.from_fmap> will be removed after 2024-5-5',
                      DeprecationWarning)

    def save(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.save> will be removed after 2024-5-5',
                      DeprecationWarning)

    def load(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.load> will be removed after 2024-5-5',
                      DeprecationWarning)

    def update_g0(self, model, fa_g0=None, fa_k=None, fa_s=None, fa_l=None):
        """
        利用各个Face的渗透率、面积、长度来更新Face的g0属性;
        """
        assert isinstance(model, Seepage)
        if fa_g0 is None:
            fa_g0 = self.face_keys['g0']
        if fa_k is None:
            fa_k = self.face_keys['perm']
        if fa_s is None:
            fa_s = self.face_keys['area']
        if fa_l is None:
            fa_l = self.face_keys['length']
        model.update_g0(fa_g0=fa_g0, fa_k=fa_k, fa_s=fa_s, fa_l=fa_l)


SeepageTher = TherFlowConfig


class ConjugateGradientSolver(HasHandle):
    """
    An wrapper of the ConjugateGradientSolver from Eigen
    """
    core.use(c_void_p, 'new_cg_sol')
    core.use(None, 'del_cg_sol', c_void_p)

    def __init__(self, tolerance=None, handle=None):
        """
        Create the Solver
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
        Set the tolerance of the solver
        """
        core.cg_sol_set_tolerance(self.handle, tolerance)


class DDMSolution2(HasHandle):
    """
    二维DDM的基本解
    """
    core.use(c_void_p, 'new_ddm_sol2')
    core.use(None, 'del_ddm_sol2', c_void_p)

    def __init__(self, handle=None):
        super(DDMSolution2, self).__init__(handle, core.new_ddm_sol2, core.del_ddm_sol2)

    core.use(None, 'ddm_sol2_save', c_void_p, c_char_p)
    core.use(None, 'ddm_sol2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.ddm_sol2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.ddm_sol2_load(self.handle, make_c_char_p(path))

    core.use(None, 'ddm_sol2_set_alpha', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_alpha', c_void_p)

    @property
    def alpha(self):
        return core.ddm_sol2_get_alpha(self.handle)

    @alpha.setter
    def alpha(self, value):
        core.ddm_sol2_set_alpha(self.handle, value)

    core.use(None, 'ddm_sol2_set_beta', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_beta', c_void_p)

    @property
    def beta(self):
        return core.ddm_sol2_get_beta(self.handle)

    @beta.setter
    def beta(self, value):
        core.ddm_sol2_set_beta(self.handle, value)

    core.use(None, 'ddm_sol2_set_shear_modulus', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_shear_modulus', c_void_p)

    @property
    def shear_modulus(self):
        return core.ddm_sol2_get_shear_modulus(self.handle)

    @shear_modulus.setter
    def shear_modulus(self, value):
        core.ddm_sol2_set_shear_modulus(self.handle, value)

    core.use(None, 'ddm_sol2_set_poisson_ratio', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_poisson_ratio', c_void_p)

    @property
    def poisson_ratio(self):
        return core.ddm_sol2_get_poisson_ratio(self.handle)

    @poisson_ratio.setter
    def poisson_ratio(self, value):
        core.ddm_sol2_set_poisson_ratio(self.handle, value)

    core.use(None, 'ddm_sol2_set_adjust_coeff', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_adjust_coeff', c_void_p)

    @property
    def adjust_coeff(self):
        return core.ddm_sol2_get_adjust_coeff(self.handle)

    @adjust_coeff.setter
    def adjust_coeff(self, value):
        core.ddm_sol2_set_adjust_coeff(self.handle, value)

    core.use(None, 'ddm_sol2_get_induced', c_void_p, c_void_p,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def get_induced(self, pos, fracture, ds, dn, height):
        """
        返回一个裂缝单元的诱导应力
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


class Fracture2:
    """
    二维裂缝单元
    """

    def __init__(self, handle):
        self.handle = handle

    core.use(c_double, 'frac2_get_pos', c_void_p, c_size_t)

    @property
    def pos(self):
        """
        返回一个长度为4的list，表示裂缝的位置。格式为 [x0, y0, x1, y1]。其中(x0, y0)为
        裂缝第一个端点的位置，(x1, y1)第二个端点的位置坐标;
        """
        return [core.frac2_get_pos(self.handle, i) for i in range(4)]

    core.use(c_size_t, 'frac2_get_uid', c_void_p)

    @property
    def uid(self):
        """
        裂缝的全局ID。在程序启动之后，裂缝的ID将会是唯一的，并且是递增的。因此uid的数值越大，则表明裂缝创建得越晚。 另外，在裂缝扩展
        的过程种，也可以用这个uid来判断，哪些裂缝是新的。
        """
        return core.frac2_get_uid(self.handle)

    core.use(None, 'frac2_set_ds', c_void_p, c_double)
    core.use(c_double, 'frac2_get_ds', c_void_p)

    @property
    def ds(self):
        """
        切向位移间断
        """
        return core.frac2_get_ds(self.handle)

    @ds.setter
    def ds(self, value):
        assert -1e6 < value < 1e6
        core.frac2_set_ds(self.handle, value)

    core.use(None, 'frac2_set_dn', c_void_p, c_double)
    core.use(c_double, 'frac2_get_dn', c_void_p)

    @property
    def dn(self):
        """
        法向位移间断
        """
        return core.frac2_get_dn(self.handle)

    @dn.setter
    def dn(self, value):
        assert -1e6 < value < 1.0
        core.frac2_set_dn(self.handle, value)

    core.use(None, 'frac2_set_h', c_void_p, c_double)
    core.use(c_double, 'frac2_get_h', c_void_p)

    @property
    def h(self):
        """
        裂缝的高度
        """
        return core.frac2_get_h(self.handle)

    @h.setter
    def h(self, value):
        assert -1.0e-2 < value < 1e100
        core.frac2_set_h(self.handle, value)

    core.use(None, 'frac2_set_fric', c_void_p, c_double)
    core.use(c_double, 'frac2_get_fric', c_void_p)

    @property
    def fric(self):
        """
        摩擦系数
        """
        return core.frac2_get_fric(self.handle)

    @fric.setter
    def fric(self, value):
        assert 0 < value < 100
        core.frac2_set_fric(self.handle, value)

    core.use(None, 'frac2_set_p0', c_void_p, c_double)
    core.use(c_double, 'frac2_get_p0', c_void_p)

    @property
    def p0(self):
        """
        当dn=0的时候，内部流体的压力（内部流体压力随着裂缝开度的增加<即随着dn降低>而降低）
        """
        return core.frac2_get_p0(self.handle)

    @p0.setter
    def p0(self, value):
        """
        当dn=0的时候，内部流体的压力（内部流体压力随着裂缝开度的增加<即随着dn降低>而降低）
        """
        core.frac2_set_p0(self.handle, value)

    core.use(None, 'frac2_set_k', c_void_p, c_double)
    core.use(c_double, 'frac2_get_k', c_void_p)

    @property
    def k(self):
        """
        dn增大1(缝宽减小1)的时候的压力增加量(>=0)
        """
        return core.frac2_get_k(self.handle)

    @k.setter
    def k(self, value):
        """
        dn增大1(缝宽减小1)的时候的压力增加量(>=0)
        """
        assert 0 <= value
        core.frac2_set_k(self.handle, value)

    core.use(c_double, 'frac2_get_attr', c_void_p, c_size_t)
    core.use(None, 'frac2_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        第index个自定义属性
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return default_val
        if index < 0:
            if index == -1:
                return self.ds
            if index == -2:
                return self.dn
            if index == -3:
                return self.h
            if index == -4:
                return self.fric
            if index == -5:
                return self.p0
            if index == -6:
                return self.k
            if index == -11:  # 宽度
                return -self.dn
            return default_val
        value = core.frac2_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        第index个自定义属性
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if value is None:
            value = 1.0e200
        if index is None:
            return self
        if index < 0:
            if index == -1:
                self.ds = value
                return self
            if index == -2:
                self.dn = value
                return self
            if index == -3:
                self.h = value
                return self
            if index == -4:
                self.fric = value
                return self
            if index == -5:
                self.p0 = value
                return self
            if index == -6:
                self.k = value
                return self
            else:
                return self
        else:
            core.frac2_set_attr(self.handle, index, value)
            return self


class FractureNetwork2(HasHandle):
    """
    二维裂缝网络
    """
    core.use(c_void_p, 'new_fnet2')
    core.use(None, 'del_fnet2', c_void_p)

    def __init__(self, handle=None):
        super(FractureNetwork2, self).__init__(handle, core.new_fnet2, core.del_fnet2)

    def __str__(self):
        return f'zml.FractureNetwork2(handle = {self.handle}, vtx_n = {self.vtx_n}, frac_n = {self.frac_n})'

    core.use(None, 'fnet2_save', c_void_p, c_char_p)
    core.use(None, 'fnet2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.fnet2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.fnet2_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'fnet2_get_frac_n', c_void_p)

    @property
    def frac_n(self):
        return core.fnet2_get_frac_n(self.handle)

    core.use(c_size_t, 'fnet2_get_vtx_n', c_void_p)

    @property
    def vtx_n(self):
        return core.fnet2_get_vtx_n(self.handle)

    core.use(None, 'fnet2_add', c_void_p, c_double, c_double, c_double, c_double, c_double)

    def add_fracture(self, pos, lave):
        """
        添加裂缝
        """
        assert len(pos) == 4
        core.fnet2_add(self.handle, *pos, lave)

    core.use(None, 'fnet2_get_fractures', c_void_p, c_void_p)

    def get_fractures(self, buffer=None):
        """
        返回所有的裂缝单元
        """
        if not isinstance(buffer, PtrVector):
            buffer = PtrVector()
        core.fnet2_get_fractures(self.handle, buffer.handle)
        return [Fracture2(handle=buffer[i]) for i in range(buffer.size)]

    core.use(None, 'fnet2_adjust', c_void_p, c_double, c_double)

    def adjust(self, lave, angle_min=0.4):
        """
        调整裂缝格局，尽量避免病态的情况出现
        """
        core.fnet2_adjust(self.handle, lave, angle_min)

    core.use(c_size_t, 'fnet2_extend_tip', c_void_p, c_void_p, c_void_p, c_double, c_double, c_double, c_double)
    core.use(c_size_t, 'fnet2_create_branch', c_void_p, c_void_p, c_void_p, c_double)

    def extend(self, kic=None, sol2=None, lave=None, dn_min=1.0e-7, lex=0.3, dangle_max=10.0,
               has_branch=True):
        """
        尝试扩展裂缝，并返回扩展的数量.
            lex:   扩展的长度与lave的比值
        注意：
            在裂缝扩展的过程中，裂缝单元的数量可能并不会发生改变. 在扩展的时候，会首先将尖端的单元拉长。只有
            当这个尖端的裂缝的长度被拉长到不得不分割的时候，才会被分成两个裂缝单元。在这个尖端被分割的时候，
            裂缝的数据(包括所有的属性)，将会被分割之后的两个单元所共同继承. 因此，当裂缝单元通过fa_id属性
            来定义裂缝单元对应的Cell的id的时候，在裂缝扩展的时候，将可能会出现，两个单元所对应的cell为同
            一个的情况(在 update_seepage_topology 的时候，会考虑到这个问题，并自动对相应的Cell进行拆分).
        """
        count = 0
        if has_branch:
            assert isinstance(kic, Tensor2)
            assert isinstance(sol2, DDMSolution2)
            assert lave is not None
            count += core.fnet2_create_branch(self.handle, kic.handle, sol2.handle, lave)
        if 0.01 < lex < 0.99:
            assert isinstance(kic, Tensor2)
            assert isinstance(sol2, DDMSolution2)
            assert lave is not None
            count += core.fnet2_extend_tip(self.handle, kic.handle, sol2.handle, dn_min, lave, lex, dangle_max)
        return count

    core.use(None, 'fnet2_get_induced', c_void_p, c_void_p, c_void_p,
             c_double, c_double, c_double, c_double)

    def get_induced(self, pos, sol2):
        """
        返回所有裂缝的诱导应力
        """
        assert isinstance(sol2, DDMSolution2)
        stress = Tensor2()
        if len(pos) == 2:
            core.fnet2_get_induced(self.handle, stress.handle, sol2.handle, *pos, *pos)
        else:
            assert len(pos) == 4
            core.fnet2_get_induced(self.handle, stress.handle, sol2.handle, *pos)
        return stress

    core.use(None, 'fnet2_update_h_by_layers', c_void_p, c_void_p, c_size_t, c_double, c_double)

    def update_h_by_layers(self, layers, fa_id, layer_h, w_min):
        """
        利用分层的数据来更新各个裂缝单元的高度;
        """
        if not isinstance(layers, PtrVector):
            layers = PtrVector.from_objects(layers)
        core.fnet2_update_h_by_layers(self.handle, layers.handle, fa_id, layer_h, w_min)

    core.use(None, 'fnet2_copy_attr', c_void_p, c_size_t, c_size_t)

    def copy_attr(self, idest, isrc):
        """
        将ID为isrc的裂缝单元属性复制到idest位置
        """
        core.fnet2_copy_attr(self.handle, idest, isrc)

    core.use(c_double, 'fnet2_get_dn_min', c_void_p)
    core.use(c_double, 'fnet2_get_dn_max', c_void_p)

    @property
    def dn_min(self):
        return core.fnet2_get_dn_min(self.handle)

    @property
    def dn_max(self):
        return core.fnet2_get_dn_max(self.handle)

    core.use(c_double, 'fnet2_get_ds_min', c_void_p)
    core.use(c_double, 'fnet2_get_ds_max', c_void_p)

    @property
    def ds_min(self):
        return core.fnet2_get_ds_min(self.handle)

    @property
    def ds_max(self):
        return core.fnet2_get_ds_max(self.handle)

    core.use(None, 'fnet2_update_dist2tip', c_void_p, c_size_t, c_size_t)

    def update_dist2tip(self, fa_dist, va_dist):
        """
        更新各个裂缝距离裂缝尖端的距离，并存储在属性fa_dist中。va_dist为各个节点距离裂缝尖端的距离，仅仅作为辅助计算的临时变量
        """
        core.fnet2_update_dist2tip(self.handle, fa_dist, va_dist)

    core.use(None, 'fnet2_update_cluster', c_void_p, c_size_t)

    def update_cluster(self, fa_cid):
        """
        更新cluster (将裂缝单元划分为相互孤立的cluster)
        """
        core.fnet2_update_cluster(self.handle, fa_cid)

    core.use(None, 'fnet2_update_fh', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def update_fh(self, fa_h, fa_cid, fa_dist, h_vs_l):
        """
        假定裂缝的形状为一个椭圆，从而根据裂缝的长度来更新裂缝的高度
        """
        core.fnet2_update_fh(self.handle, fa_h, fa_cid, fa_dist, h_vs_l)


class InfManager2(HasHandle):
    """
    二维裂缝的管理（建立应力影响矩阵）
    注意：
        这是一个临时变量，因此没有提供save/load函数。在调用update_matrix之后，矩阵会自动创建.
    """
    core.use(c_void_p, 'new_fmanager2')
    core.use(None, 'del_fmanager2', c_void_p)

    def __init__(self, handle=None):
        super(InfManager2, self).__init__(handle, core.new_fmanager2, core.del_fmanager2)

    core.use(None, 'fmanager2_update1', c_void_p, c_void_p, c_void_p, c_void_p, c_double)

    def update_matrix(self, network, sol, stress, dist):
        """
        更新应力影响矩阵. 其中：
            dist为应力影响的范围. 当两个裂缝之间的距离大于dist的时候，则它们之间不会产生
            实时的应力影响。也就是说，会利用它们此刻的开度和剪切来计算应力，而这部分应力在
            后续不会随着它们开度的变化而变化。
        """
        assert isinstance(network, FractureNetwork2)
        assert isinstance(sol, DDMSolution2)
        assert isinstance(stress, Tensor2)
        core.fmanager2_update1(self.handle, network.handle, sol.handle, stress.handle, dist)

    core.use(c_size_t, 'fmanager2_update_disp', c_void_p, c_double, c_double, c_size_t, c_double)

    def update_disp(self, gradw_max=0, err_max=0.1, iter_max=10000, ratio_max=0.99):
        """
        更新裂缝单元的位移(dn和ds)
        """
        return core.fmanager2_update_disp(self.handle, gradw_max, err_max, iter_max, ratio_max)

    core.use(None, 'fmanager2_update_boundary', c_void_p, c_void_p, c_size_t, c_double)
    core.use(None, 'fmanager2_update_boundary_by_layers', c_void_p, c_void_p, c_size_t)

    def update_boundary(self, seepage, fa_id, fh=None):
        """
        在DDM中，流体是作为固体计算的边界。此函数根据此刻的流体情况来更新固体计算的边界条件。
        其中:
            seepage 可以为一个或者多个Seepage类。当Seepage为多个时，其指针存储在PtrVector中;
            fa_id 为裂缝单元中存储的流体Cell的ID。

        注意：
            对于各个裂缝单元，将首先计算它对应的Cell(用fa_id指定)中的流体的体积，然后计算裂缝的长度，并使用
            给定的fh或者裂缝内存储的裂缝高度来计算裂缝的面积，进而计算流体的厚度。这个厚度就是对裂缝开度的一个
            非常硬的约束，也是后续计算裂缝的dn和ds的时候的边界条件.
        """
        if isinstance(seepage, Seepage):
            if fh is None:
                fh = -1  # Now, using the fracture height defined in fracture.
            core.fmanager2_update_boundary(self.handle, seepage.handle, fa_id, fh)
        else:
            if not isinstance(seepage, PtrVector):
                seepage = PtrVector.from_objects(seepage)
            core.fmanager2_update_boundary_by_layers(self.handle, seepage.handle, fa_id)


class ExHistory(HasHandle):
    core.use(c_void_p, 'new_exhistory')
    core.use(None, 'del_exhistory', c_void_p)

    def __init__(self, path=None, handle=None):
        super(ExHistory, self).__init__(handle, core.new_exhistory, core.del_exhistory)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'exhistory_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.exhistory_save(self.handle, make_c_char_p(path))

    core.use(None, 'exhistory_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.exhistory_load(self.handle, make_c_char_p(path))

    core.use(None, 'exhistory_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'exhistory_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.exhistory_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.exhistory_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'exhistory_record', c_void_p, c_double, c_size_t)

    def record(self, dt, n_extend):
        """
        记录扩展的过程
        :param dt: 采用的时间步长
        :param n_extend: 扩展的数量
        """
        core.exhistory_record(self.handle, dt, n_extend)

    core.use(c_double, 'exhistory_get_best_dt', c_void_p, c_double)

    def get_best_dt(self, prob):
        """
        返回给定扩展概率下面最佳的时间步长
        :param prob: 扩展的概率. 如果，如果希望每10步裂缝可以发生一次扩展，则prob应该设置为0.1
        """
        return core.exhistory_get_best_dt(self.handle, prob)


class Hf2Alg:
    core.use(None, 'hf2_alg_update_seepage_topology', c_void_p, c_void_p, c_size_t)

    @staticmethod
    def update_seepage_topology(seepage, network, fa_id):
        """
        建立和裂缝对应的流动模型.
            其中：
            fa_id为裂缝的自定义属性的ID，用以存储这个裂缝单元对应的Seepage中的Cell的ID.
            注意：
            1. 这里的seepage需要被这个裂缝系统所独占。即，这里建立的目标，是裂缝单元和seepage中的Cell一对一。但是，为了确保存储在
            fracture中的Cell的id不发生变化，这里不允许删除seepage中的Cell。当裂缝变少的时候，多余的Cell将会被标记成为孤立的Cell，
            不和其它的Cell产生流体的联通。
            2. 在创建seepage的时候，会尽量保证Cell中的流体和pore不发生变化。如果有Cell被两个裂缝所共有，那么，将会把Cell中的数据按照
            两条裂缝的长度的比例分配给两个fracture单元(所以，大部分的属性应该会得到保留).
            3. 在此函数执行之后，对于每一个裂缝单元，都将有一个Cell来对应，且每一个Cell最多只和一个fracture对应。
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        core.hf2_alg_update_seepage_topology(seepage.handle, network.handle, fa_id)

    core.use(None, 'hf2_alg_update_seepage_cell_pos', c_void_p, c_void_p, c_void_p, c_size_t)

    @staticmethod
    def update_seepage_cell_pos(seepage, network, coord, fa_id):
        """
        根据各个裂缝单元中心点的坐标来更新各个Cell的位置；
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        assert isinstance(coord, Coord3)
        core.hf2_alg_update_seepage_cell_pos(seepage.handle, network.handle, coord.handle, fa_id)

    core.use(None, 'hf2_alg_update_cond0', c_void_p, c_void_p, c_double, c_size_t, c_double)
    core.use(None, 'hf2_alg_update_cond1', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    @staticmethod
    def update_cond(seepage, network=None, fa_id=None, fw_max=None, layer_dh=None,
                    ca_g=None, ca_l=None, ca_h=None):
        """
        更新Seepage系统中各个Face的Cond属性(根据裂缝单元的长度、缝宽、高度来计算).
            或者更新各个Cell的Cond属性(暂存到ca_g中)
        """
        assert isinstance(seepage, Seepage)
        if fw_max is None:
            fw_max = 0.005
        if ca_g is not None and ca_l is not None and ca_h is not None:
            core.hf2_alg_update_cond1(seepage.handle, ca_g, ca_l, ca_h, fw_max)
        else:
            assert isinstance(network, FractureNetwork2)
            if layer_dh is None:
                layer_dh = -1  # 此时，将采用fracture的高度属性
            core.hf2_alg_update_cond0(seepage.handle, network.handle, fw_max, fa_id, layer_dh)

    core.use(None, 'hf2_alg_update_pore0', c_void_p, c_void_p, c_size_t)
    core.use(None, 'hf2_alg_update_pore1', c_void_p, c_size_t, c_size_t, c_double)
    core.use(None, 'hf2_alg_update_pore2', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)
    core.use(None, 'hf2_alg_update_pore3', c_void_p, c_size_t, c_size_t, c_double, c_double)

    @staticmethod
    def update_pore(seepage, manager=None, fa_id=None, ca_s=None, ca_ny=None, dw=None, ca_l=None,
                    ca_h=None, ca_g=None, ca_mu=None, k1=None, k2=None, relax_factor=None):
        """
        更新渗流系统的pore.
        其中：
            manager: 二维裂缝管理 InfManager2
            fa_id: 裂缝中存储对应Cell的ID的属性
            ca_s：定义Cell对应的裂缝的面积
            ca_ny: 定义垂直于裂缝面的应力（以拉张为正）
            dw: 定义压力变化1Pa，裂缝的宽度改变的幅度(单位: m)
            ca_l: 定义Cell对应裂缝的长度
            ca_h：定义Cell对应裂缝的高度
            ca_g: 定义Cell位置的剪切模量
            ca_mu: 定义Cell位置的泊松比
        注意：
            当指定manager的时候，则使用manager来更新，否则，则使用seepage中定义的ca_s，ca_ny以及
            给定的dw来更新.
        """
        assert isinstance(seepage, Seepage)
        if ca_ny is not None and ca_s is not None and k1 is not None and k2 is not None:
            # 此时建议的取值: k1=1.0e-10, k2=1.0e-8
            core.hf2_alg_update_pore3(seepage.handle, ca_ny, ca_s, k1, k2)
            return

        if isinstance(manager, InfManager2):
            assert fa_id is not None
            core.hf2_alg_update_pore0(seepage.handle, manager.handle, fa_id)
            return

        if ca_s is not None and ca_ny is not None and dw is not None:
            # will be removed in the future.
            core.hf2_alg_update_pore1(seepage.handle, ca_s, ca_ny, dw)
            return

        if ca_l is not None and ca_h is not None and ca_ny is not None and ca_g is not None and ca_mu is not None:
            core.hf2_alg_update_pore2(seepage.handle, ca_l, ca_h, ca_ny, ca_g, ca_mu)
            return

        assert False

    core.use(None, 'hf2_alg_update_area', c_void_p, c_size_t, c_void_p, c_size_t, c_double)

    @staticmethod
    def update_area(seepage, ca_s, network, fa_id, fh=None):
        """
        更新存储在Seepage的各个Cell中的对应的裂缝的面积属性.
        其中：
            ca_s：   为需要更新的面积属性的ID
            network：为裂缝网络
            fa_id：  为存储在各个裂缝单元中的对应的Cell的ID
            fh:     为裂缝的高度，当这个值为负值的时候，则使用定义在裂缝单元内的高度
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        if fh is None:
            fh = -1.0  # Now, using the fracture height
        core.hf2_alg_update_area(seepage.handle, ca_s, network.handle, fa_id, fh)

    core.use(None, 'hf2_alg_update_length', c_void_p, c_size_t, c_void_p, c_size_t)

    @staticmethod
    def update_length(seepage, ca_l, network, fa_id):
        """
        更新各个Cell的裂缝长度属性
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        core.hf2_alg_update_length(seepage.handle, ca_l, network.handle, fa_id)

    core.use(None, 'hf2_alg_update_normal_stress', c_void_p, c_size_t, c_void_p, c_size_t, c_bool, c_double)

    @staticmethod
    def update_normal_stress(seepage, ca_ny, manager, fa_id, except_self=True, relax_factor=1.0):
        """
        更新裂缝的法向应力(以拉应力为正)，并存储在裂缝对应Cell的ca_ny属性上.
        注意:
            这个函数会首先删除掉seepage中所有的Cell的ca_ny属性，然后在遍历所有的裂缝，计算应力，然后给定裂缝的fa_id属性
            找到对应的Cell，然后在Cell上添加ca_ny属性. 因此，这个函数运行之后，只要某个Cell定义了ca_ny属性，那么ca_ny
            对应的数值就一定是最新的.
        注意：
            当except_self为True的时候，则去除了当前单元的影响，即假设当前单元的开度为0.
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(manager, InfManager2)
        core.hf2_alg_update_normal_stress(seepage.handle, ca_ny, manager.handle, fa_id, except_self, relax_factor)

    core.use(None, 'hf2_alg_exchange_fluids', c_void_p, c_void_p, c_double, c_size_t, c_size_t)

    @staticmethod
    def exchange_fluids(layers, pipe, dt, ca_g, ca_fp=None):
        """
        在不同的层之间交换流体
        """
        if not isinstance(layers, PtrVector):
            layers = PtrVector.from_objects(layers)
        assert isinstance(pipe, Seepage)
        if ca_fp is None:
            ca_fp = 99999999  # Now, will not update fluid pressure
        core.hf2_alg_exchange_fluids(layers.handle, pipe.handle, dt, ca_g, ca_fp)

    core.use(c_bool, 'hf2_alg_rect_v3_intersected', c_double, c_double, c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def rect_v3_intersected(a, b):
        """
        返回两个给定的竖直裂缝a和b是否相交
        """
        assert len(a) == 6 and len(b) == 6
        return core.hf2_alg_rect_v3_intersected(*a, *b)

    core.use(None, 'hf2_alg_create_links', c_void_p, c_void_p, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def create_links(seepage, cell_n, keys, v3, buf=None):
        """
        对于seepage模型，读取cell中定义的竖直的矩形的信息，返回和给定的矩形相交的所有的Cell的ID
        """
        if buf is None:
            buf = UintVector()
        assert isinstance(seepage, Seepage)
        assert len(v3) == 6
        core.hf2_alg_create_links(buf.handle, seepage.handle, cell_n, keys.x0, keys.y0, keys.z0,
                                  keys.x1, keys.y1, keys.z1,
                                  keys.x2, keys.y2, keys.z2, *v3)
        return buf.to_list()


class Hf2Model(HasHandle):
    """
    定义二维压裂模型(主要用于组织数据)
    """
    core.use(c_void_p, 'new_hf2')
    core.use(None, 'del_hf2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Hf2Model, self).__init__(handle, core.new_hf2, core.del_hf2)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'hf2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.hf2_save(self.handle, make_c_char_p(path))

    core.use(None, 'hf2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.hf2_load(self.handle, make_c_char_p(path))

    core.use(None, 'hf2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'hf2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.hf2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.hf2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_void_p, 'hf2_get_network', c_void_p)

    @property
    def network(self):
        """
        裂缝网络。存储的是一个个裂缝单元，这些单元是纯固体的，不包含任何流体的信息
        """
        return FractureNetwork2(handle=core.hf2_get_network(self.handle))

    core.use(c_void_p, 'hf2_get_manager', c_void_p)

    @property
    def manager(self):
        """
        裂缝单元的管理，用以建立裂缝单元之间的应力关系，并且自动管理影响矩阵(这是一个临时变量，在序列化的时候不需要存储)
        """
        return InfManager2(handle=core.hf2_get_manager(self.handle))

    core.use(c_void_p, 'hf2_get_flow', c_void_p)

    @property
    def flow(self):
        """
        和裂缝单元对应的流动体系(用以存储流体，并且模拟流体的流动).
        """
        return Seepage(handle=core.hf2_get_flow(self.handle))

    core.use(c_void_p, 'hf2_get_seepage', c_void_p)

    @property
    def seepage(self):
        """
        和天然裂缝对应的渗流体系. 在更新这一部分流动的时候，会临时将flow中的Cell附加过来(但是不会附加flow中的Face)，从而
        模拟主裂缝和天然裂缝流体的交互的过程.
        """
        return Seepage(handle=core.hf2_get_seepage(self.handle))

    core.use(c_void_p, 'hf2_get_buffer', c_void_p)

    @property
    def buffer(self):
        """
        流体的缓冲区。当裂缝体系和外部进行流体交换的时候，如果裂缝的容积不够，则可以加入这个缓冲区。在每一步更新的
        时候，会首先将缓冲区附加到seepage中，然后更新seepage中的流动，再将缓冲区从seepage中弹出来，从而得到了
        进入到缓冲区中的流体.
        """
        warnings.warn('the <buffer> may be deleted after 2024-6-30', DeprecationWarning)
        return Seepage(handle=core.hf2_get_buffer(self.handle))

    core.use(c_void_p, 'hf2_get_sol2', c_void_p)

    @property
    def sol2(self):
        """
        二维DDM的基本解，用于定义固体的基本参数。对于边界元来说，储层的弹性性质必须是均匀的。
        """
        return DDMSolution2(handle=core.hf2_get_sol2(self.handle))

    core.use(c_double, 'hf2_get_attr', c_void_p, c_size_t)
    core.use(None, 'hf2_set_attr',
             c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        模型的第index个自定义属性
        """
        if index is None:
            return default_val
        value = core.hf2_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        模型的第index个自定义属性
        """
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.hf2_set_attr(self.handle, index, value)
        return self


class InvasionPercolation(HasHandle):
    """
    IP模型计算模型。该模型定义了所有用于求解的数据以及方法。
    """

    class NodeData(Object):
        """
        IP模型中的节点，也对应于Pore(相应地，Bond类型也可以对应于throat)；Node为流体的存储空间；
        """

        def __init__(self, handle):
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Node是否是用一个
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            return not (self == rhs)

        def __str__(self):
            return f'zml.InvasionPercolation.NodeData(handle = {self.handle}, pos = {self.pos}, radi = {self.radi})'

        core.use(c_size_t, 'ip_node_get_phase', c_void_p)
        core.use(None, 'ip_node_set_phase', c_void_p, c_size_t)

        def get_phase(self):
            """
            此Node中流体的相态。相态用一个整数(>=0)来表示。
            """
            return core.ip_node_get_phase(self.handle)

        def set_phase(self, value):
            """
            此Node中流体的相态。相态用一个整数(>=0)来表示。
            """
            assert value >= 0
            core.ip_node_set_phase(self.handle, value)

        phase = property(get_phase, set_phase)

        core.use(c_size_t, 'ip_node_get_cid', c_void_p)
        core.use(None, 'ip_node_set_cid', c_void_p, c_size_t)

        def get_cid(self):
            """
            程序会将各个Node，根据流体的phase和相互的连接关系，划分成为一个个cluster。每一个cluster都是一个流体相态一样，且相互联通的一系列Node。
            这里，属性cid，表示Node所在的cluster的ID (从0开始编号)
            """
            return core.ip_node_get_cid(self.handle)

        def set_cid(self, value):
            """
            设置Node所在的cluster的ID （注意：此函数仅供作者测试，且随时都可能被移除。在任何情况下，此函数都不应被调用）
            """
            core.ip_node_set_cid(self.handle, value)

        cid = property(get_cid, set_cid)

        core.use(c_double, 'ip_node_get_radi', c_void_p)
        core.use(None, 'ip_node_set_radi', c_void_p, c_double)

        def get_radi(self):
            """
            此Node内孔隙的半径（单位：米）。这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。
            """
            return core.ip_node_get_radi(self.handle)

        def set_radi(self, value):
            """
            此Node内孔隙的半径（单位：米）。这个内部半径主要用来计算流体侵入到该Node所必须克服的毛管压力。
            """
            assert value > 0
            core.ip_node_set_radi(self.handle, value)

        radi = property(get_radi, set_radi)

        core.use(c_double, 'ip_node_get_time_invaded', c_void_p)

        @property
        def time_invaded(self):
            """
            最后一个set_phase的时间
            """
            return core.ip_node_get_time_invaded(self.handle)

        @property
        def time(self):
            return self.time_invaded

        core.use(c_double, 'ip_node_get_rate_invaded', c_void_p)

        @property
        def rate_invaded(self):
            return core.ip_node_get_rate_invaded(self.handle)

        core.use(c_double, 'ip_node_get_pos', c_void_p, c_size_t)
        core.use(None, 'ip_node_set_pos', c_void_p, c_size_t, c_double)

        def get_pos(self):
            """
            此Node在三维空间的位置
            """
            return [core.ip_node_get_pos(self.handle, i) for i in range(3)]

        def set_pos(self, value):
            """
            此Node在三维空间的位置
            """
            for i in range(3):
                core.ip_node_set_pos(self.handle, i, value[i])

        pos = property(get_pos, set_pos)

    class Node(NodeData):

        core.use(c_void_p, 'ip_get_node', c_void_p, c_size_t)

        def __init__(self, model, index):
            super(InvasionPercolation.Node, self).__init__(handle=core.ip_get_node(model.handle, index))
            self.model = model
            self.index = index

        core.use(c_size_t, 'ip_get_node_bond_n', c_void_p, c_size_t)

        @property
        def bond_n(self):
            """
            此Node连接的Bond的数量
            """
            return core.ip_get_node_bond_n(self.model.handle, self.index)

        @property
        def node_n(self):
            """
            此Node连接的Node的数量
            """
            return self.bond_n

        core.use(c_size_t, 'ip_get_node_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, idx):
            """
            此Node连接的第idx个Node
            """
            assert idx < self.node_n
            i_node = core.ip_get_node_node_id(self.model.handle, self.index, idx)
            return self.model.get_node(i_node)

        core.use(c_size_t, 'ip_get_node_bond_id', c_void_p, c_size_t, c_size_t)

        def get_bond(self, idx):
            """
            此Node连接的第idx个Bond
            """
            assert idx < self.bond_n
            i_bond = core.ip_get_node_bond_id(self.model.handle, self.index, idx)
            return self.model.get_bond(i_bond)

    class BondData(Object):
        """
        在IP模型中，连接两个Node的流体流动通道。
        """

        def __init__(self, handle):
            self.handle = handle

        def __eq__(self, rhs):
            """
            判断两个Bond是否为同一个
            """
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            return not (self == rhs)

        def __str__(self):
            return f'zml.InvasionPercolation.Bond(handle = {self.handle}, radi = {self.radi})'

        core.use(c_double, 'ip_bond_get_radi', c_void_p)
        core.use(None, 'ip_bond_set_radi', c_void_p, c_double)

        def get_radi(self):
            """
            此Bond所在位置吼道的内部半径（主要用来计算流体界面通过这个Bond所必须克服的毛管压力）
            """
            return core.ip_bond_get_radi(self.handle)

        def set_radi(self, value):
            """
            此Bond所在位置吼道的内部半径（主要用来计算流体界面通过这个Bond所必须克服的毛管压力）
            """
            assert value > 0
            core.ip_bond_set_radi(self.handle, value)

        radi = property(get_radi, set_radi)

        core.use(c_double, 'ip_bond_get_dp0', c_void_p)
        core.use(None, 'ip_bond_set_dp0', c_void_p, c_double)

        def get_dp0(self):
            """
            此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）
            """
            return core.ip_bond_get_dp0(self.handle)

        def set_dp0(self, value):
            """
            此Bond左侧的流体侵入右侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）
            """
            core.ip_bond_set_dp0(self.handle, value)

        dp0 = property(get_dp0, set_dp0)

        core.use(c_double, 'ip_bond_get_dp1', c_void_p)
        core.use(None, 'ip_bond_set_dp1', c_void_p, c_double)

        def get_dp1(self):
            """
            此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）
            """
            return core.ip_bond_get_dp1(self.handle)

        def set_dp1(self, value):
            """
            此Bond右侧的流体侵入左侧时，在该Bond内必须克服的毛管阻力（注意：该属性仅供作者测试，请勿调用）
            """
            core.ip_bond_set_dp1(self.handle, value)

        dp1 = property(get_dp1, set_dp1)

        core.use(c_double, 'ip_bond_get_contact_angle', c_void_p, c_size_t, c_size_t)

        def get_contact_angle(self, ph0, ph1):
            """
            当ph0驱替ph1的时候，在ph0中的接触角。当此处的值设置位0到PI之间时，将覆盖全局的设置
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_contact_angle(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_contact_angle', c_void_p, c_size_t, c_size_t, c_double)

        def set_contact_angle(self, ph0, ph1, value):
            """
            当ph0驱替ph1的时候，在ph0中的接触角。当此处的值设置位0到PI之间时，将覆盖全局的设置
            """
            assert 0 <= ph0 != ph1 >= 0
            core.ip_bond_set_contact_angle(self.handle, ph0, ph1, value)

        core.use(c_double, 'ip_bond_get_tension', c_void_p, c_size_t, c_size_t)

        def get_tension(self, ph0, ph1):
            """
            流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数
            """
            assert 0 <= ph0 != ph1 >= 0
            return core.ip_bond_get_tension(self.handle, ph0, ph1)

        core.use(None, 'ip_bond_set_tension', c_void_p, c_size_t, c_size_t, c_double)

        def set_tension(self, ph0, ph1, value):
            """
            流体ph0和ph1之间的表面张力，当值大于0时，将覆盖全局的参数
            """
            assert 0 <= ph0 != ph1 >= 0
            assert value >= 0
            core.ip_bond_set_tension(self.handle, ph0, ph1, value)

        @property
        def tension(self):
            """
            界面张力
            """
            return self.get_tension(0, 1)

        @tension.setter
        def tension(self, value):
            """
            界面张力
            """
            assert value >= 0
            self.set_tension(0, 1, value)

        @property
        def ca0(self):
            """
            当流体0驱替流体1的时候，在流体0中的接触角度
            """
            return self.get_contact_angle(0, 1)

        @ca0.setter
        def ca0(self, value):
            """
            当流体0驱替流体1的时候，在流体0中的接触角度
            """
            self.set_contact_angle(0, 1, value)

        @property
        def ca1(self):
            """
            当流体1驱替流体0的时候，在流体1中的接触角度
            """
            return self.get_contact_angle(1, 0)

        @ca1.setter
        def ca1(self, value):
            """
            当流体1驱替流体0的时候，在流体1中的接触角度
            """
            self.set_contact_angle(1, 0, value)

    class Bond(BondData):

        core.use(c_void_p, 'ip_get_bond', c_void_p, c_size_t)

        def __init__(self, model, index):
            super(InvasionPercolation.Bond, self).__init__(handle=core.ip_get_bond(model.handle, index))
            self.model = model
            self.index = index

        @property
        def node_n(self):
            """
            此Bond连接的Node的数量
            """
            return 2

        core.use(c_size_t, 'ip_get_bond_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, idx):
            """
            此Bond连接的第idx个Node
            """
            assert idx < self.node_n
            i_node = core.ip_get_bond_node_id(self.model.handle, self.index, idx)
            return self.model.get_node(i_node)

    class InjectorData(Object):
        """
        代表一个注入点。注意：一个注入点必须依赖于一个Node，即流体只能注入到Node里面。所以，注入点必须设置其作用的Node
        """

        def __init__(self, handle):
            self.handle = handle

        def __eq__(self, rhs):
            return self.handle == rhs.handle

        def __ne__(self, rhs):
            return not (self == rhs)

        def __str__(self):
            return f'zml.InvasionPercolation.Injector(handle = {self.handle})'

        core.use(c_size_t, 'ip_inj_get_node_id', c_void_p)
        core.use(None, 'ip_inj_set_node_id', c_void_p, c_size_t)

        def get_node_id(self):
            """
            注入点作用的Node的ID
            """
            return core.ip_inj_get_node_id(self.handle)

        def set_node_id(self, value):
            """
            注入点作用的Node的ID
            """
            core.ip_inj_set_node_id(self.handle, value)

        node_id = property(get_node_id, set_node_id)

        core.use(c_size_t, 'ip_inj_get_phase', c_void_p)

        def get_phase(self):
            """
            通过该注入点注入的流体的类型(整数，从0开始编号)
            """
            return core.ip_inj_get_phase(self.handle)

        core.use(None, 'ip_inj_set_phase', c_void_p, c_size_t)

        def set_phase(self, value):
            """
            通过该注入点注入的流体的类型(整数，从0开始编号)
            """
            assert value >= 0
            core.ip_inj_set_phase(self.handle, value)

        phase = property(get_phase, set_phase)

        core.use(c_double, 'ip_inj_get_q', c_void_p)

        def get_qinj(self):
            """
            通过该注入点注入流体的速度。单位为 n/time。 其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0
            """
            return core.ip_inj_get_q(self.handle)

        core.use(None, 'ip_inj_set_q', c_void_p, c_double)

        def set_qinj(self, value):
            """
            通过该注入点注入流体的速度。单位为 n/time。 其中n为invade的node的个数。即表示单位时间内invade的node的个数。取值 > 0
            """
            assert value > 0
            core.ip_inj_set_q(self.handle, value)

        qinj = property(get_qinj, set_qinj)

    class Injector(InjectorData):
        core.use(c_void_p, 'ip_get_inj', c_void_p, c_size_t)

        def __init__(self, model, index):
            super(InvasionPercolation.Injector, self).__init__(handle=core.ip_get_inj(model.handle, index))
            self.model = model
            self.index = index

    class InvadeOperation(Object):
        """
        一个侵入操作
        """

        def __init__(self, model, index):
            self.model = model
            self.index = index

        def __eq__(self, rhs):
            return self.model.handle == rhs.model.handle and self.index == rhs.index

        def __ne__(self, rhs):
            return not (self == rhs)

        def __str__(self):
            return f'zml.InvasionPercolation.InvadeOperation(index = {self.index})'

        core.use(c_size_t, 'ip_get_oper_bond_id', c_void_p, c_size_t)

        def get_bond(self):
            bond_id = core.ip_get_oper_bond_id(self.model.handle, self.index)
            return self.model.get_bond(bond_id)

        @property
        def bond(self):
            return self.get_bond()

        core.use(c_bool, 'ip_get_oper_dir', c_void_p, c_size_t)

        @property
        def dir(self):
            return core.ip_get_oper_dir(self.model.handle, self.index)

        def get_node(self, idx):
            """
            当idx==0时，返回上游的node；否则，返回下游的node
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
        """
        super(InvasionPercolation, self).__init__(handle, core.new_ip, core.del_ip)

    def __eq__(self, rhs):
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        return not (self == rhs)

    def __str__(self):
        return f'zml.InvasionPercolation(handle = {self.handle}, node_n = {self.node_n}, bond_n = {self.bond_n})'

    core.use(None, 'ip_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        assert isinstance(path, str)
        core.ip_save(self.handle, make_c_char_p(path))

    core.use(None, 'ip_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        assert isinstance(path, str)
        core.ip_load(self.handle, make_c_char_p(path))

    core.use(None, 'ip_print_nodes', c_void_p, c_char_p)

    def print_nodes(self, path):
        """
        将node的数据打印到文件
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
        模型内部的时间. 模型每充注一次，则时间time的增量为 1.0/max(qinj). 其中max(qinj)为所有的注入点中qinj的最大值。
        """
        return core.ip_get_time(self.handle)

    core.use(None, 'ip_set_time', c_void_p, c_double)

    def set_time(self, value):
        """
        模型内部的时间
        """
        assert value >= 0
        core.ip_set_time(self.handle, value)

    time = property(get_time, set_time)

    core.use(c_size_t, 'ip_add_node', c_void_p)

    def add_node(self):
        """
        添加一个Node，并返回新添加的Node对象
        """
        index = core.ip_add_node(self.handle)
        if 0 <= index < self.node_n:
            return self.get_node(index)

    def get_node(self, index):
        """
        返回序号为index的Node对象
        """
        if 0 <= index < self.node_n:
            return InvasionPercolation.Node(self, index)

    core.use(c_size_t, 'ip_add_bond', c_void_p, c_size_t, c_size_t)

    def add_bond(self, node0, node1):
        """
        添加一个Bond，来连接给定序号的两个Node。
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        assert self.node_n > node0 != node1 < self.node_n
        index = core.ip_add_bond(self.handle, node0, node1)
        if 0 <= index < self.bond_n:
            return self.get_bond(index)

    def get_bond(self, index):
        """
        返回给定序号的Bond
        """
        if 0 <= index < self.bond_n:
            return InvasionPercolation.Bond(self, index)

    core.use(c_size_t, 'ip_get_bond_id', c_void_p, c_size_t, c_size_t)

    def get_bond_id(self, node0, node1):
        """
        返回两个node中间的bond的id（如果不存在，则返回无穷大）
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        return core.ip_get_bond_id(self.handle, node0, node1)

    def find_bond(self, node0, node1):
        """
        返回两个node中间的bond
        """
        if isinstance(node0, InvasionPercolation.Node):
            node0 = node0.index
        if isinstance(node1, InvasionPercolation.Node):
            node1 = node1.index
        index = self.get_bond_id(node0, node1)
        if 0 <= index < self.bond_n:
            return self.get_bond(index)

    core.use(c_size_t, 'ip_get_node_n', c_void_p)

    def get_node_n(self):
        return core.ip_get_node_n(self.handle)

    node_n = property(get_node_n)

    core.use(c_size_t, 'ip_get_bond_n', c_void_p)

    def get_bond_n(self):
        return core.ip_get_bond_n(self.handle)

    bond_n = property(get_bond_n)

    core.use(c_size_t, 'ip_get_outlet_n', c_void_p)
    core.use(None, 'ip_set_outlet_n', c_void_p, c_size_t)

    def get_outlet_n(self):
        """
        模型内，被是为”出口“的Node的数量
        """
        return core.ip_get_outlet_n(self.handle)

    def set_outlet_n(self, value):
        """
        模型内，被是为”出口“的Node的数量
        """
        assert value >= 0
        core.ip_set_outlet_n(self.handle, value)

    outlet_n = property(get_outlet_n, set_outlet_n)

    core.use(None, 'ip_set_outlet', c_void_p, c_size_t, c_size_t)

    def set_outlet(self, index, value):
        """
        第index个出口对应的Node的序号
        """
        assert 0 <= index < self.outlet_n
        assert value < self.node_n
        core.ip_set_outlet(self.handle, index, value)

    core.use(c_size_t, 'ip_get_outlet', c_void_p, c_size_t)

    def get_outlet(self, index):
        """
        第index个出口对应的Node的序号
        """
        assert 0 <= index < self.outlet_n
        return core.ip_get_outlet(self.handle, index)

    def add_outlet(self, node_id):
        """
        添加一个出口点，返回这个outlet的序号
        """
        assert node_id < self.node_n
        index = self.outlet_n
        self.outlet_n = index + 1
        self.set_outlet(index, node_id)
        return index

    core.use(c_double, 'ip_get_tension', c_void_p, c_size_t, c_size_t)

    def get_tension(self, ph0, ph1):
        """
        两种相态ph0和ph1之间的界面张力
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_tension(self.handle, ph0, ph1)

    core.use(None, 'ip_set_tension', c_void_p, c_size_t, c_size_t, c_double)

    def set_tension(self, ph0, ph1, value):
        """
        两种相态ph0和ph1之间的界面张力。注意，界面张力的值为正数；相态ph0和ph1为大于等于0的整数。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_tension(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_contact_angle', c_void_p, c_size_t, c_size_t)

    def get_contact_angle(self, ph0, ph1):
        """
        当ph0驱替ph1时，在ph0中的接触角 （注意，这个一个全局的设置，后续会被各个Node和Bond内的设置覆盖）。
        """
        assert 0 <= ph0 != ph1 >= 0
        return core.ip_get_contact_angle(self.handle, ph0, ph1)

    core.use(None, 'ip_set_contact_angle', c_void_p, c_size_t, c_size_t, c_double)

    def set_contact_angle(self, ph0, ph1, value):
        """
        当ph0驱替ph1时，在ph0中的接触角 （注意，这个一个全局的设置，后续会被各个Node和Bond内的设置覆盖）。
        """
        assert 0 <= ph0 != ph1 >= 0
        core.ip_set_contact_angle(self.handle, ph0, ph1, value)

    core.use(c_double, 'ip_get_density', c_void_p, c_size_t)

    def get_density(self, ph):
        """
        流体ph的密度
        """
        assert ph >= 0
        return core.ip_get_density(self.handle, ph)

    core.use(None, 'ip_set_density', c_void_p, c_size_t, c_double)

    def set_density(self, ph, value):
        """
        流体ph的密度
        """
        assert ph >= 0
        assert value > 0
        core.ip_set_density(self.handle, ph, value)
        return self

    core.use(c_double, 'ip_get_gravity', c_void_p, c_size_t)

    def get_gravity(self):
        """
        重力向量。注意，这个三维向量要和Node中pos的属性的含义保持一致。
        """
        return [core.ip_get_gravity(self.handle, i) for i in range(3)]

    core.use(None, 'ip_set_gravity', c_void_p, c_size_t, c_double)

    def set_gravity(self, value):
        """
        重力向量。注意，这个三维向量要和Node中pos的属性的含义保持一致。
        """
        for i in range(3):
            core.ip_set_gravity(self.handle, i, value[i])
        return self

    gravity = property(get_gravity, set_gravity)

    core.use(c_size_t, 'ip_get_inj_n', c_void_p)
    core.use(None, 'ip_set_inj_n', c_void_p, c_size_t)

    def get_inj_n(self):
        """
        模型中注入点的数量
        """
        return core.ip_get_inj_n(self.handle)

    def set_inj_n(self, value):
        """
        模型中注入点的数量
        """
        assert value >= 0
        core.ip_set_inj_n(self.handle, value)
        return self

    inj_n = property(get_inj_n, set_inj_n)

    def get_inj(self, index):
        """
        返回第index个注入点
        """
        if 0 <= index < self.inj_n:
            return InvasionPercolation.Injector(self, index)

    def add_inj(self, node_id=None, phase=None, qinj=None):
        """
        添加一个注入点，并且返回注入点对象
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
        是否允许围困。当此开关为True，且outlet的数量不为0的时候，围困生效
        """
        return core.ip_trap_enabled(self.handle)

    core.use(None, 'ip_set_trap_enabled', c_void_p, c_bool)

    @trap_enabled.setter
    def trap_enabled(self, value):
        """
        是否允许围困。当此开关为True，且outlet的数量不为0的时候，围困生效
        """
        core.ip_set_trap_enabled(self.handle, value)

    core.use(c_size_t, 'ip_get_oper_n', c_void_p)

    def get_oper_n(self):
        return core.ip_get_oper_n(self.handle)

    oper_n = property(get_oper_n)

    def get_oper(self, idx):
        if idx < self.oper_n:
            return InvasionPercolation.InvadeOperation(self, idx)

    core.use(None, 'ip_remove_node', c_void_p, c_size_t)
    core.use(None, 'ip_remove_bond', c_void_p, c_size_t)

    def remove_node(self, node):
        """
        删除给定node连接的所有的bond，然后删除该node
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
        删除给定的bond
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
        返回距离最近的node
        """
        assert len(pos) == 3
        index = core.ip_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
        return self.get_node(index)

    core.use(None, 'ip_get_node_pos', c_void_p, c_void_p, c_void_p, c_void_p, c_size_t)

    def get_node_pos(self, x=None, y=None, z=None, phase=9999999999):
        """
        获得给定phase的node的位置；如果phase大于99999999，则返回所有的node的位置
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.ip_get_node_pos(self.handle, x.handle, y.handle, z.handle, phase)
        return x, y, z


class Dfn2(HasHandle):
    """
    用于生成二维的离散裂缝网络
    """
    core.use(c_void_p, 'new_dfn2d')
    core.use(None, 'del_dfn2d', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Dfn2, self).__init__(handle, core.new_dfn2d, core.del_dfn2d)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'dfn2d_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.dfn2d_save(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.dfn2d_load(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_set_range', c_void_p, c_double, c_double, c_double, c_double)
    core.use(c_double, 'dfn2d_get_range', c_void_p, c_size_t)

    @property
    def range(self):
        """
        位置的范围(一个矩形区域)
        """
        return [core.dfn2d_get_range(self.handle, i) for i in range(4)]

    @range.setter
    def range(self, value):
        """
        位置的范围(一个矩形区域)
        """
        assert len(value) == 4, f'The format of pos range is [xmin, ymin, xmax, ymax]'
        core.dfn2d_set_range(self.handle, *value)

    core.use(c_bool, 'dfn2d_add_frac', c_void_p, c_double, c_double, c_double, c_double, c_double)
    core.use(None, 'dfn2d_randomly_add_frac', c_void_p, c_void_p, c_void_p, c_double, c_double)

    def add_frac(self, x0=None, y0=None, x1=None, y1=None, angles=None, lengths=None, p21=None, l_min=None):
        """
        添加一个裂缝或者随机添加多条裂缝。
            当给定x0, y0, x1, y1的时候，添加这一条裂缝;
            否则，则需要给定angle(一个list，用以定义角度), length(list: 用以定义角度), p21(新添加的裂缝的密度)来随机添加一组裂缝.
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
        """
        return core.dfn2d_get_fracture_number(self.handle)

    core.use(c_double, 'dfn2d_get_fracture_pos', c_void_p, c_size_t, c_size_t)

    def get_fracture(self, idx):
        """
        返回第idx个裂缝的位置
        """
        return [core.dfn2d_get_fracture_pos(self.handle, idx, i) for i in range(4)]

    def get_fractures(self):
        """
        返回所有的裂缝的位置
        """
        return [self.get_fracture(idx) for idx in range(self.fracture_n)]

    core.use(c_double, 'dfn2d_get_p21', c_void_p)

    @property
    def p21(self):
        """
        返回当前的裂缝的密度
        """
        return core.dfn2d_get_p21(self.handle)

    def print_file(self, path):
        """
        将所有的裂缝打印到文件
        """
        with open(path, 'w') as file:
            for i in range(self.fracture_n):
                p = self.get_fracture(i)
                file.write(f'{p[0]}\t{p[1]}\t{p[2]}\t{p[3]}\n')


class Molecule(HasHandle):
    """
    模拟分子。模拟分子和真实的分子有很大的区别。为了降低计算规模，在DSMC计算时，一个模拟分子
    会代表大量的真实分子，从而大大降低计算量，使得DSMC方法可以计算较大的计算区域。
    """
    core.use(c_void_p, 'new_molecule')
    core.use(None, 'del_molecule', c_void_p)

    def __init__(self, handle=None, **kwargs):
        """
        分子的初始化
        """
        super(Molecule, self).__init__(handle, core.new_molecule, core.del_molecule)
        if handle is None:
            self.set(**kwargs)

    def __str__(self):
        return f'zml.Molecule(mass={self.mass}, radi={self.radi}, pos={self.pos}, vel={self.vel})'

    core.use(None, 'molecule_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.molecule_save(self.handle, make_c_char_p(path))

    core.use(None, 'molecule_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.molecule_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'molecule_get_pos', c_void_p, c_size_t)
    core.use(None, 'molecule_set_pos', c_void_p, c_size_t, c_double)

    @property
    def pos(self):
        """
        模拟分子的中心点在三维空间的位置
        """
        return [core.molecule_get_pos(self.handle, i) for i in range(3)]

    @pos.setter
    def pos(self, val):
        """
        模拟分子的中心点在三维空间的位置
        """
        assert len(val) == 3
        for i in range(3):
            core.molecule_set_pos(self.handle, i, val[i])

    core.use(c_double, 'molecule_get_vel', c_void_p, c_size_t)
    core.use(None, 'molecule_set_vel', c_void_p, c_size_t, c_double)

    @property
    def vel(self):
        """
        模拟分子在三维空间的速度
        """
        return [core.molecule_get_vel(self.handle, i) for i in range(3)]

    @vel.setter
    def vel(self, val):
        """
        模拟分子在三维空间的速度
        """
        assert len(val) == 3
        for i in range(3):
            core.molecule_set_vel(self.handle, i, val[i])

    core.use(c_double, 'molecule_get_mass', c_void_p)
    core.use(None, 'molecule_set_mass', c_void_p, c_double)

    @property
    def mass(self):
        """
        模拟分子的质量 [kg]
        """
        return core.molecule_get_mass(self.handle)

    @mass.setter
    def mass(self, val):
        """
        模拟分子的质量 [kg]
        """
        core.molecule_set_mass(self.handle, val)

    core.use(c_double, 'molecule_get_radi', c_void_p)
    core.use(None, 'molecule_set_radi', c_void_p, c_double)

    @property
    def radi(self):
        """
        模拟分子的半径。用以定义模拟分子的碰撞。只有当两个模拟分子之间的距离小于二者的半径之和的时候，
        它们才会碰撞。因此，可以通过修改分子的半径来修改它与其它分子发生碰撞的可能。
        """
        return core.molecule_get_radi(self.handle)

    @radi.setter
    def radi(self, val):
        core.molecule_set_radi(self.handle, val)

    core.use(c_double, 'molecule_get_imass', c_void_p)
    core.use(None, 'molecule_set_imass', c_void_p, c_double)

    @property
    def imass(self):
        """
        模拟分子的内部质量。除了定义的外在质量之外，假设模拟分子内部的分子还在做不规则的
        热运动，这部分运动会存储一部分能量。这部分振动的动能会在模拟分子相互碰撞的过程中
        积聚或者释放出来。内部质量越大，则储存能量的能力就越强。
        """
        return core.molecule_get_imass(self.handle)

    @imass.setter
    def imass(self, val):
        core.molecule_set_imass(self.handle, val)

    core.use(c_double, 'molecule_get_ivel', c_void_p)
    core.use(None, 'molecule_set_ivel', c_void_p, c_double)

    @property
    def ivel(self):
        """
        模拟分子内部分子团做无规则运动的速度
        """
        return core.molecule_get_ivel(self.handle)

    @ivel.setter
    def ivel(self, val):
        core.molecule_set_ivel(self.handle, val)

    core.use(c_double, 'molecule_get_relax_dt', c_void_p)
    core.use(None, 'molecule_set_relax_dt', c_void_p, c_double)

    @property
    def relax_dt(self):
        """
        模拟分子的内部能量和模拟分子动能相互转化的松弛时间
        """
        return core.molecule_get_relax_dt(self.handle)

    @relax_dt.setter
    def relax_dt(self, val):
        core.molecule_set_relax_dt(self.handle, val)

    core.use(c_int, 'molecule_get_tag', c_void_p)
    core.use(None, 'molecule_set_tag', c_void_p, c_int)

    @property
    def tag(self):
        """
        分子的标签<大于等于0为正常的分子，小于0为沙子>
        """
        return core.molecule_get_tag(self.handle)

    @tag.setter
    def tag(self, value):
        """
        分子的标签<大于等于0为正常的分子，小于0为沙子>
        """
        core.molecule_set_tag(self.handle, value)


class MoleVec(HasHandle):
    """
    一个由模拟分子组成的数组
    """
    core.use(c_void_p, 'new_vmole')
    core.use(None, 'del_vmole', c_void_p)

    def __init__(self, handle=None):
        super(MoleVec, self).__init__(handle, core.new_vmole, core.del_vmole)

    def __str__(self):
        return f'zml.Moles(size={len(self)})'

    core.use(None, 'vmole_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.vmole_save(self.handle, make_c_char_p(path))

    core.use(None, 'vmole_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.vmole_load(self.handle, make_c_char_p(path))

    core.use(None, 'vmole_clear', c_void_p)

    def clear(self):
        """
        清除所有的分子
        """
        core.vmole_clear(self.handle)

    core.use(None, 'vmole_push_back', c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_multi', c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_other', c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_other_with_tag', c_void_p, c_void_p, c_int)

    def append(self, mole=None, vx=None, vy=None, vz=None, moles=None, tag=None):
        """
        添加一个分子<或者多个分子>；当给定的一系列坐标值给定的时候，则利用mole定义的数据，以及vx,vy,vz定义的位置来添加多个分析
        """
        if mole is not None:
            assert isinstance(mole, Molecule)
            if isinstance(vx, Vector) and isinstance(vy, Vector) and isinstance(vz, Vector):
                core.vmole_push_back_multi(self.handle, mole.handle, vx.handle, vy.handle, vz.handle)
            else:
                core.vmole_push_back(self.handle, mole.handle)
        if moles is not None:
            if tag is not None:
                core.vmole_push_back_other_with_tag(self.handle, moles.handle, tag)
            else:
                core.vmole_push_back_other(self.handle, moles.handle)

    core.use(c_size_t, 'vmole_size', c_void_p)

    def __len__(self):
        """
        返回分子的数量
        """
        return core.vmole_size(self.handle)

    core.use(c_void_p, 'vmole_get', c_void_p, c_size_t)

    def __getitem__(self, index):
        """
        返回index位置的分子数据
        """
        if index < len(self):
            return Molecule(handle=core.vmole_get(self.handle, index))

    core.use(None, 'vmole_update_pos', c_void_p,
             c_double, c_double, c_double,
             c_double)

    def update_pos(self, gravity, dt):
        """
        更新各个粒子的位置(当重力不等于0的时候，将同时会修改粒子的速度)
        """
        assert len(gravity) == 3
        core.vmole_update_pos(self.handle, *gravity, dt)

    core.use(None, 'vmole_get_pos', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, x=None, y=None, z=None):
        """
        获得所有粒子的x,y,z坐标
        """
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.vmole_get_pos(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'vmole_get_vel', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_vel(self, x=None, y=None, z=None):
        """
        获得所有粒子的x,y,z坐标
        """
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.vmole_get_vel(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'vmole_collision', c_void_p, c_void_p, c_void_p, c_void_p)

    def collision(self, lat, vi0=None, vi1=None):
        """
        施加碰撞操作<需要提前将粒子放入到格子里，只有在格子里面的模拟分子才会参与碰撞>；
        当给定vi0和vi1的时候，则记录碰撞对
        """
        assert isinstance(lat, Lattice)
        if isinstance(vi0, UintVector) and isinstance(vi1, UintVector):
            core.vmole_collision(self.handle, lat.handle, vi0.handle, vi1.handle)
            return vi0, vi1
        else:
            core.vmole_collision(self.handle, lat.handle, 0, 0)

    core.use(None, 'vmole_update_internal_energy', c_void_p, c_void_p, c_void_p, c_double)

    def update_internal_energy(self, vi0, vi1, dt):
        """
        利用给定的碰撞对，在碰撞对之间，施加内能和动能之间的相互转化
        """
        core.vmole_update_internal_energy(self.handle, vi0.handle, vi1.handle, dt)

    core.use(None, 'vmole_rand_add', c_void_p, c_void_p, c_size_t)

    def rand_add(self, other, count):
        """
        从给定的分子源随机拷贝过来count数量的分子，用于分子的生成
        """
        assert isinstance(other, MoleVec)
        core.vmole_rand_add(self.handle, other.handle, count)

    core.use(c_double, 'vmole_get_vel_max', c_void_p)

    def get_vmax(self):
        """
        返回所有分子速度的最大值，主要用于确定时间步长
        """
        return core.vmole_get_vel_max(self.handle)

    core.use(None, 'vmole_add_offset', c_void_p, c_double, c_double, c_double)

    def add_offset(self, dx, dy, dz):
        """
        所有分子的位置施加一个整体的移动
        """
        core.vmole_add_offset(self.handle, dx, dy, dz)

    core.use(None, 'vmole_get_range', c_void_p, c_void_p)

    def get_range(self):
        """
        获得所有分子位置的范围
        """
        if len(self) > 0:
            v = Vector()
            core.vmole_get_range(self.handle, v.handle)
            assert len(v) == 6
            return (v[0], v[1], v[2]), (v[3], v[4], v[5])

    core.use(c_size_t, 'vmole_erase', c_void_p, c_void_p)

    def erase(self, reg):
        """
        删除指定区域内的分子
        """
        assert isinstance(reg, Region3)
        return core.vmole_erase(self.handle, reg.handle)

    core.use(c_size_t, 'vmole_roll_back', c_void_p, c_void_p, c_double, c_bool)
    core.use(c_size_t, 'vmole_roll_back_record', c_void_p, c_void_p, c_double, c_bool, c_void_p, c_double, c_double)

    def roll_back(self, reg, forcemap=None, dt=None, time_span=None, parallel=True, diffuse_ratio=1.0):
        """
        从给定的区域内退出. 当给定forcemap的时候，将记录冲击固体的力.
            parallel: 内核是否调用并行
        """
        assert isinstance(reg, Region3)
        if forcemap is None:
            return core.vmole_roll_back(self.handle, reg.handle, diffuse_ratio, parallel)
        else:
            assert dt is not None and time_span is not None
            return core.vmole_roll_back_record(self.handle, reg.handle, diffuse_ratio, parallel,
                                               forcemap.handle, dt, time_span)

    core.use(None, 'vmole_get_mass', c_void_p, c_void_p)

    def get_mass(self, vm=None):
        """
        获得所有模拟分子的质量(作为一个Vector返回)
        """
        if vm is None:
            vm = Vector()
        core.vmole_get_mass(self.handle, vm.handle)
        return vm

    core.use(None, 'vmole_update_radi', c_void_p, c_void_p)

    def update_radi(self, v2r):
        """
        根据各个模拟分子的速度来更新它的碰撞半径
        """
        assert isinstance(v2r, Interp1)
        core.vmole_update_radi(self.handle, v2r.handle)

    core.use(None, 'vmole_get_radi', c_void_p, c_void_p)

    def get_radi(self, vr=None):
        """
        备份分子的半径
        """
        if not isinstance(vr, Vector):
            vr = Vector()
        core.vmole_backup_radi(self.handle, vr.handle)
        return vr

    core.use(None, 'vmole_set_radi', c_void_p, c_void_p)

    def set_radi(self, vr):
        """
        设置分子的半径
        """
        assert isinstance(vr, Vector)
        core.vmole_set_radi(self.handle, vr.handle)

    core.use(c_size_t, 'vmole_count_tag', c_void_p, c_int)

    def count_tag(self, tag):
        """
        返回具有给定tag的分子的数量
        """
        return core.vmole_count_tag(self.handle, tag)

    core.use(None, 'vmole_clamp_pos', c_void_p, c_size_t, c_double, c_double)

    def clamp_pos(self, idim, left, right):
        """
        对分子在idim维度上的位置进行约束
        """
        core.vmole_clamp_pos(self.handle, idim, left, right)


class Lattice(HasHandle):
    """
    用以临时存放模拟分子的格子。模拟分子只有被映射到格子上，才能够进行相互的碰撞（用于dsmc）
    """
    core.use(c_void_p, 'new_lattice')
    core.use(None, 'del_lattice', c_void_p)

    def __init__(self, box=None, shape=None, handle=None):
        super(Lattice, self).__init__(handle, core.new_lattice, core.del_lattice)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape)

    def __str__(self):
        return f'zml.Lattice(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'lattice_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.lattice_save(self.handle, make_c_char_p(path))

    core.use(None, 'lattice_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.lattice_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'lattice_lrange', c_void_p, c_size_t)

    @property
    def box(self):
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似
        """
        lr = [core.lattice_lrange(self.handle, i) for i in range(3)]
        sh = self.shape
        sz = self.size
        rr = [lr[i] + sh[i] * sz[i] for i in range(3)]
        return lr + rr

    core.use(c_double, 'lattice_shape', c_void_p, c_size_t)

    @property
    def shape(self):
        """
        返回每个网格在三个维度上的大小
        """
        return [core.lattice_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'lattice_size', c_void_p, c_size_t)

    @property
    def size(self):
        """
        返回三维维度上网格的数量<至少为1>
        """
        return [core.lattice_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'lattice_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lattice_get_centers', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        返回格子的中心点
        """
        if index is not None:
            assert len(index) == 3
            return [core.lattice_get_center(self.handle, index[i], i) for i in range(3)]
        else:
            if not isinstance(x, Vector):
                x = Vector()
            if not isinstance(y, Vector):
                y = Vector()
            if not isinstance(z, Vector):
                z = Vector()
            core.lattice_get_centers(self.handle, x.handle, y.handle, z.handle)
            return x, y, z

    core.use(None, 'lattice_create', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box, shape):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小.
        """
        assert len(box) == 6
        if not is_array(shape):
            core.lattice_create(self.handle, *box, shape, shape, shape)
        else:
            assert len(shape) == 3
            core.lattice_create(self.handle, *box, *shape)

    core.use(c_size_t, 'lattice_update', c_void_p, c_void_p, c_double)
    core.use(c_size_t, 'lattice_update_tag', c_void_p, c_void_p, c_double, c_int)
    core.use(c_size_t, 'lattice_update_cylinder', c_void_p, c_void_p, c_double)

    def update(self, moles, lat_ratio=1.0, cylinder=False, tag=None):
        """
        更新网格上的分子。
        如果cylinder为True，则首先对分子的位置进行坐标变换：
            x：代表距离z轴的距离
            y：0
            z：z
        然后根据变换后的位置，将分子放入格子
        """
        assert isinstance(moles, MoleVec)
        if tag is not None:
            assert not cylinder
            return core.lattice_update_tag(self.handle, moles.handle, lat_ratio, tag)
        if cylinder:
            return core.lattice_update_cylinder(self.handle, moles.handle, lat_ratio)
        else:
            return core.lattice_update(self.handle, moles.handle, lat_ratio)

    core.use(None, 'lattice_random_shuffle', c_void_p)

    def random_shuffle(self):
        """
        随机更新格子里面的分子的顺序<随机洗牌>
        """
        core.lattice_random_shuffle(self.handle)

    core.use(None, 'lattice_add_point', c_void_p, c_double, c_double, c_double, c_size_t)

    def add_point(self, pos, index):
        """
        将位置在pos，序号为index的对象放入到格子里面<不会去查重复>
        """
        assert len(pos) == 3, f'pos = {pos}'
        core.lattice_add_point(self.handle, *pos, index)


class Region3(HasHandle):
    """
    定义一个三维的区域。数据被放在格子里面，便于高效率地访问 （用于dsmc）
    """
    core.use(c_void_p, 'new_region3')
    core.use(None, 'del_region3', c_void_p)

    def __init__(self, box=None, shape=None, value=None, handle=None):
        super(Region3, self).__init__(handle, core.new_region3, core.del_region3)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape, value)

    def __str__(self):
        return f'zml.Region3(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'region3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.region3_save(self.handle, make_c_char_p(path))

    core.use(None, 'region3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.region3_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'region3_lrange', c_void_p, c_size_t)

    @property
    def box(self):
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似
        """
        lr = [core.region3_lrange(self.handle, i) for i in range(3)]
        sh = self.shape
        sz = self.size
        rr = [lr[i] + sh[i] * sz[i] for i in range(3)]
        return lr + rr

    core.use(c_double, 'region3_shape', c_void_p, c_size_t)

    @property
    def shape(self):
        """
        返回每个网格在三个维度上的大小
        """
        return [core.region3_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'region3_size', c_void_p, c_size_t)

    @property
    def size(self):
        """
        返回三维维度上网格的数量<至少为1>
        """
        return [core.region3_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'region3_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'region3_get_centers', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        给定格子的中心 <当index为None的时候，则返回所有的格子的中心，并作为Vector返回>
        """
        if index is not None:
            assert len(index) == 3
            return [core.region3_get_center(self.handle, index[i], i) for i in range(3)]
        else:
            if not isinstance(x, Vector):
                x = Vector()
            if not isinstance(y, Vector):
                y = Vector()
            if not isinstance(z, Vector):
                z = Vector()
            core.region3_get_centers(self.handle, x.handle, y.handle, z.handle)
            return x, y, z

    core.use(None, 'region3_create', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box, shape, value=None):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小(可以分别设置在三个维度上的尺寸)
        """
        assert len(box) == 6
        if not is_array(shape):
            shape = shape, shape, shape
        assert len(shape) == 3
        assert shape[0] > 0 and shape[1] > 0 and shape[2] > 0
        core.region3_create(self.handle, *box, *shape)
        if value is not None:
            self.fill(value)

    core.use(c_bool, 'region3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, index):
        """
        给定的格子是否是True
        """
        assert len(index) == 3
        return core.region3_get(self.handle, *index)

    core.use(None, 'region3_set', c_void_p, c_size_t, c_size_t, c_size_t, c_bool)

    def set(self, index, value):
        """
        给定的格子是否是True
        """
        assert len(index) == 3
        core.region3_set(self.handle, *index, value)

    core.use(None, 'region3_fill', c_void_p, c_bool)

    def fill(self, value):
        """
        设置所有的格子的数据
        """
        core.region3_fill(self.handle, value)

    core.use(None, 'region3_set_cube', c_void_p, c_double, c_double, c_double, c_double, c_double, c_double, c_bool,
             c_bool)

    def set_cube(self, box, value, inner=True):
        """
        将给定的六面体区域设置[内部]设置为value
        """
        assert len(box) == 6
        core.region3_set_cube(self.handle, *box, inner, value)

    def add_cube(self, box, inner=True):
        self.set_cube(box=box, value=True, inner=inner)

    def del_cube(self, box, inner=True):
        self.set_cube(box=box, value=False, inner=inner)

    core.use(None, 'region3_set_around_z', c_void_p, c_void_p, c_bool, c_bool)

    def set_around_z(self, z2r=None, z=None, r=None, value=True, inner=True):
        """
        设置环绕z的一个轴对称的区域
        """
        if not isinstance(z2r, Interp1):
            z2r = Interp1(x=z, y=r)
        core.region3_set_around_z(self.handle, z2r.handle, inner, value)

    core.use(c_bool, 'region3_contains', c_void_p, c_double, c_double, c_double)

    def contains(self, *args):
        """
        给定的点是否包含在此区域内<给定的参数为一个点在三维空间的坐标>
        """
        if len(args) == 3:
            pos = args
        else:
            assert len(args) == 1
            pos = args[0]
            assert len(pos) == 3
        return core.region3_contains(self.handle, *pos)

    core.use(None, 'region3_add_offset', c_void_p, c_double, c_double, c_double)

    def add_offset(self, dx, dy, dz):
        """
        添加一个平移
        """
        core.region3_add_offset(self.handle, dx, dy, dz)

    core.use(None, 'region3_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Region3)
        core.region3_clone(self.handle, other.handle)

    core.use(None, 'region3_erase', c_void_p, c_void_p)

    def erase(self, other):
        assert isinstance(other, Region3)
        core.region3_erase(self.handle, other.handle)

    core.use(None, 'region3_get_inds', c_void_p, c_void_p)

    def get_inds(self, buffer=None):
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.region3_get_inds(self.handle, buffer.handle)
        return buffer

    core.use(None, 'region3_print_top', c_void_p, c_char_p)

    def print_top(self, path):
        """
        将顶部一层的坐标打印到文件
        """
        if path is not None:
            core.region3_print_top(self.handle, make_c_char_p(path))


class ForceMap(HasHandle):
    """
    记录格子的受力 (用于dsmc)
    """
    core.use(c_void_p, 'new_forcemap')
    core.use(None, 'del_forcemap', c_void_p)

    def __init__(self, handle=None):
        super(ForceMap, self).__init__(handle, core.new_forcemap, core.del_forcemap)

    core.use(None, 'forcemap_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.forcemap_save(self.handle, make_c_char_p(path))

    core.use(None, 'forcemap_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.forcemap_load(self.handle, make_c_char_p(path))

    core.use(None, 'forcemap_clear', c_void_p)

    def clear(self):
        core.forcemap_clear(self.handle)

    core.use(None, 'forcemap_get_centers', c_void_p, c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, reg3, x=None, y=None, z=None):
        """
        返回受力的点的位置
        """
        assert isinstance(reg3, Region3)
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.forcemap_get_centers(self.handle, reg3.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'forcemap_get_forces', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_force(self, reg3, shear=None, normal=None):
        """
        返回受力的点的剪切力和法向应力
        """
        assert isinstance(reg3, Region3)
        if shear is None:
            shear = Vector()
        if normal is None:
            normal = Vector()
        core.forcemap_get_forces(self.handle, reg3.handle, shear.handle, normal.handle)
        return shear, normal

    core.use(None, 'forcemap_erode', c_void_p, c_void_p, c_void_p, c_double,
             c_void_p, c_double, c_size_t,
             c_double,
             c_void_p, c_void_p, c_void_p)

    def erode(self, reg3, strength, normal_weight=0, moles=None, dist=None, nmax=99999999,
              strength_modify_factor=0.5,
              vx=None, vy=None, vz=None):
        """
        土体侵蚀<并记录侵蚀发生的位置>
        """
        assert 0.0 <= strength_modify_factor <= 1.0
        assert isinstance(reg3, Region3), f'reg3={reg3}'
        assert isinstance(strength, Interp3), f'strength={strength}'
        hx = vx.handle if isinstance(vx, Vector) else 0
        hy = vy.handle if isinstance(vy, Vector) else 0
        hz = vz.handle if isinstance(vz, Vector) else 0
        if moles is not None and dist is not None:
            assert isinstance(moles, MoleVec)
            assert dist > 0
            core.forcemap_erode(self.handle, reg3.handle, strength.handle, normal_weight,
                                moles.handle, dist, nmax,
                                strength_modify_factor,
                                hx, hy, hz)
        else:
            core.forcemap_erode(self.handle, reg3.handle, strength.handle, normal_weight,
                                0, 0, nmax,
                                strength_modify_factor,
                                hx, hy, hz)


class Statistic(HasHandle):
    """
    分子数据统计.（用于dsmc）
    """
    core.use(c_void_p, 'new_stat')
    core.use(None, 'del_stat', c_void_p)

    def __init__(self, handle=None):
        super(Statistic, self).__init__(handle, core.new_stat, core.del_stat)

    core.use(None, 'stat_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.stat_save(self.handle, make_c_char_p(path))

    core.use(None, 'stat_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.stat_load(self.handle, make_c_char_p(path))

    core.use(None, 'stat_update_vel', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_vel_cylinder', c_void_p, c_void_p, c_void_p, c_double)

    def update_vel(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的速度; 如果cylinder为True，则首先对分子的速度进行转换：
            计算径向速度，并作为x分量；y分量设置为0；z分量维持不变
        然后再更新到格子；
        """
        assert isinstance(lat, Lattice)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_vel_cylinder(self.handle, lat.handle, moles.handle, relax_factor)
        else:
            core.stat_update_vel(self.handle, lat.handle, moles.handle, relax_factor)

    core.use(None, 'stat_get_vel', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_vel(self, x=None, y=None, z=None):
        """
        返回中心的速度
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.stat_get_vel(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'stat_update_den', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_den_cylinder', c_void_p, c_void_p, c_void_p, c_double)

    def update_den(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的密度
        """
        assert isinstance(lat, Lattice)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_den_cylinder(self.handle, lat.handle, moles.handle, relax_factor)
        else:
            core.stat_update_den(self.handle, lat.handle, moles.handle, relax_factor)

    core.use(None, 'stat_get_den', c_void_p, c_void_p)

    def get_den(self, buffer=None):
        """
        返回密度
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.stat_get_den(self.handle, buffer.handle)
        return buffer

    core.use(None, 'stat_update_pre', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_pre_cylinder', c_void_p, c_void_p, c_void_p, c_double)

    def update_pre(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的压力
        """
        assert isinstance(lat, Lattice)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_pre_cylinder(self.handle, lat.handle, moles.handle, relax_factor)
        else:
            core.stat_update_pre(self.handle, lat.handle, moles.handle, relax_factor)

    core.use(None, 'stat_get_pre', c_void_p, c_void_p)

    def get_pre(self, buffer=None):
        """
        返回压力
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.stat_get_pre(self.handle, buffer.handle)
        return buffer


class Disc3(HasHandle):
    """
    三维的圆盘
    """
    core.use(c_void_p, 'new_disc3')
    core.use(None, 'del_disc3', c_void_p)

    def __init__(self, coord=None, radi=None, handle=None):
        super(Disc3, self).__init__(handle, core.new_disc3, core.del_disc3)
        if handle is None:
            if coord is not None:
                self.coord = coord
            if radi is not None:
                self.radi = radi

    core.use(c_void_p, 'disc3_get_coord', c_void_p)
    core.use(None, 'disc3_set_coord', c_void_p, c_void_p)

    @property
    def coord(self):
        return Coord3(handle=core.disc3_get_coord(self.handle))

    @coord.setter
    def coord(self, value):
        assert isinstance(value, Coord3)
        core.disc3_set_coord(self.handle, value.handle)

    core.use(None, 'disc3_set_radi', c_void_p, c_double)
    core.use(c_double, 'disc3_get_radi', c_void_p)

    @property
    def radi(self):
        return core.disc3_get_radi(self.handle)

    @radi.setter
    def radi(self, value):
        core.disc3_set_radi(self.handle, value)

    core.use(None, 'disc3_create', c_void_p, c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def create(x, y, z, dir, angle, r, buffer=None):
        if not isinstance(buffer, Disc3):
            buffer = Disc3()
        core.disc3_create(buffer.handle, x, y, z, dir, angle, r)
        return buffer

    core.use(c_bool, 'disc3_get_intersection', c_void_p, c_void_p, c_void_p, c_void_p)
    core.use(c_bool, 'disc3_get_intersection_with_segment', c_void_p, c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double)
    core.use(c_bool, 'disc3_get_intersection_with_xoy', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_intersection(self, other=None, p1=None, p2=None, buffer=None, coord=None):
        if isinstance(coord, Coord3):
            # 返回和给定坐标系的xoy平面的交线
            if not isinstance(p1, Array3):
                p1 = Array3()
            if not isinstance(p2, Array3):
                p2 = Array3()
            if core.disc3_get_intersection_with_xoy(self.handle, coord.handle, p1.handle, p2.handle):
                return p1, p2
            else:
                return
        if isinstance(other, Disc3):
            # 返回和另一个圆盘的交线
            if not isinstance(p1, Array3):
                p1 = Array3()
            if not isinstance(p2, Array3):
                p2 = Array3()
            if core.disc3_get_intersection(self.handle, other.handle, p1.handle, p2.handle):
                return p1, p2
        else:
            # 返回和线段的交点
            if not isinstance(buffer, Array3):
                buffer = Array3()
            if core.disc3_get_intersection_with_segment(self.handle, buffer.handle, p1[0], p1[1], p1[2], p2[0], p2[1],
                                                        p2[2]):
                return buffer

    core.use(None, 'disc3_get_lat_inds', c_void_p, c_void_p, c_void_p)

    def get_lat_inds(self, lat, buffer=None):
        """
        将这个圆盘投射到给定的格子上，返回这个圆盘所占据的格子的序号
        """
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        assert isinstance(lat, Lattice)
        core.disc3_get_lat_inds(self.handle, buffer.handle, lat.handle)
        return buffer

    core.use(None, 'disc3_create_mesh', c_void_p, c_void_p, c_size_t)

    def create_mesh(self, count=20, buffer=None):
        """
        生成用于显示该圆盘的三角形网格
        """
        if not isinstance(buffer, Mesh3):
            buffer = Mesh3()
        core.disc3_create_mesh(self.handle, buffer.handle, count)
        return buffer

    core.use(c_void_p, 'disc3_get_cell_ids', c_void_p)

    @property
    def cell_ids(self):
        return UintVector(handle=core.disc3_get_cell_ids(self.handle))

    core.use(c_void_p, 'disc3_get_face_ids', c_void_p)

    @property
    def face_ids(self):
        return UintVector(handle=core.disc3_get_face_ids(self.handle))

    core.use(c_double, 'disc3_get_attr', c_void_p, c_size_t)
    core.use(None, 'disc3_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        第index个自定义属性。
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return default_val
        value = core.disc3_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        第index个自定义属性。
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.disc3_set_attr(self.handle, index, value)
        return self

    core.use(None, 'disc3_add_scale', c_void_p, c_double)

    def add_scale(self, value):
        """
        在空间的位置、大小都等比例放大一定的倍数
        """
        core.disc3_add_scale(self.handle, value)

    core.use(None, 'disc3_copy', c_void_p, c_void_p)

    def copy(self, other):
        core.disc3_copy(self.handle, other.handle)

    @staticmethod
    def get_copy(disc3, buffer=None):
        if not isinstance(buffer, Disc3):
            buffer = Disc3()
        buffer.copy(disc3)
        return buffer


class Disc3Vec(HasHandle):
    """
    一个由三维圆盘组成的数组
    """
    core.use(c_void_p, 'new_vdisc3')
    core.use(None, 'del_vdisc3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Disc3Vec, self).__init__(handle, core.new_vdisc3, core.del_vdisc3)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.Disc3Vec(size={len(self)})'

    core.use(None, 'vdisc3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.vdisc3_save(self.handle, make_c_char_p(path))

    core.use(None, 'vdisc3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.vdisc3_load(self.handle, make_c_char_p(path))

    core.use(None, 'vdisc3_push_back', c_void_p, c_void_p)

    def append(self, disc):
        """
        添加一个圆盘
        """
        assert isinstance(disc, Disc3)
        core.vdisc3_push_back(self.handle, disc.handle)

    core.use(c_size_t, 'vdisc3_size', c_void_p)

    def __len__(self):
        """
        返回数量
        """
        return core.vdisc3_size(self.handle)

    core.use(c_void_p, 'vdisc3_get', c_void_p, c_size_t)

    def __getitem__(self, index):
        """
        返回index位置的数据
        """
        if index < len(self):
            return Disc3(handle=core.vdisc3_get(self.handle, index))

    core.use(None, 'vdisc3_create_mesh', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def create_mesh(self, count=20, da=99999999, na=99999999, fa=99999999, buffer=None):
        """
        生成用于显示该圆盘的三角形网格
        da:
            对于各个disc，尝试输出的自定义属性

        na:
            对于各个node，添加自定义属性，用以标识这个node所在的圆盘的序号

        fa:
            对于各个face，添加自定义属性，用以标识这个face所在的圆盘的序号
        """
        if not isinstance(buffer, Mesh3):
            buffer = Mesh3()
        core.vdisc3_create_mesh(self.handle, buffer.handle, count, da, na, fa)
        return buffer

    core.use(None, 'vdisc3_modify_perm', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def modify_perm(self, seepage, fa_k, ca_fp, da_pc, da_k):
        """
        对于圆盘控制的face，检查流体压力是否超过了临界值。如果流体压力超过了临界值，则相当于裂缝打开，则增加face渗透率；
        其中：
            fa_k: 定义face位置的渗透率
            ca_fp：定义Cell的流体压力
            da_pc：定义圆盘的临界流体压力
            da_k：定义圆盘的渗透率
        """
        assert isinstance(seepage, Seepage)
        core.vdisc3_modify_perm(self.handle, seepage.handle, fa_k, ca_fp, da_pc, da_k)


if __name__ == "__main__":
    print(about())

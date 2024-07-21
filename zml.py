# -*- coding: utf-8 -*-
"""
Description:    The core module of flow, heat transfer and stress calculation;
                Python interface for C++ code (must be used with zml.dll).

Environment:    Windows 7/10/11; Python 3.7 or later; 64-bit system;

Dependency:     None

Website:        https://gitee.com/geomech/hydrate

Author:         ZHANG Zhaobin <zhangzhaobin@mail.iggcas.ac.cn>,
                Institute of Geology and Geophysics, Chinese Academy of Sciences
"""

import ctypes
import datetime
import importlib
import math
import os
import sys
import timeit
import warnings

warnings.simplefilter("default")  # Default warning display

from ctypes import (cdll, c_void_p, c_char_p, c_int, c_int64, c_bool, c_double,
                    c_size_t, c_uint, CFUNCTYPE, POINTER)
from typing import Iterable

# Indicates whether the system is currently Windows (both Windows and Linux systems are currently supported)
is_windows = os.name == 'nt'

# Version of the zml module (date represented by six digits)
version = 240704


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
    Converts the given parameter list into a dictionary
    """
    return kwargs


class _GuiAdaptor:
    def __getattr__(self, item):
        warnings.warn('zml.gui will be removed after 2025-1-21. use zmlx.ui.GuiBuffer.gui instead',
                      DeprecationWarning)
        from zmlx.ui.GuiBuffer import gui as _gui
        return getattr(_gui, item)

    def __call__(self, *args, **kwargs):
        warnings.warn('zml.gui will be removed after 2025-1-21. use zmlx.ui.GuiBuffer.gui instead',
                      DeprecationWarning)
        from zmlx.ui.GuiBuffer import gui as _gui
        return _gui(*args, **kwargs)

    def __bool__(self):
        return self.exists()


# will be removed after 2025-1-21. use zmlx.ui.GuiBuffer.gui instead
gui = _GuiAdaptor()


def _deprecation_func(pack_name, func, date=None):
    """
    Define a function that is defined in zmlx and deprecated in zml.
    """

    def a_function(*args, **kwargs):
        warnings.warn(f'zml.{func} will be removed after {date}, use {pack_name}.{func} instead. ',
                      DeprecationWarning)
        mod = importlib.import_module(pack_name)
        f = getattr(mod, func)
        return f(*args, **kwargs)

    return a_function


information = _deprecation_func('zmlx.ui.GuiBuffer', 'information', '2025-1-21')
question = _deprecation_func('zmlx.ui.GuiBuffer', 'question', '2025-1-21')
plot = _deprecation_func('zmlx.ui.GuiBuffer', 'plot', '2025-1-21')
break_point = _deprecation_func('zmlx.ui.GuiBuffer', 'break_point', '2025-1-21')
breakpoint = break_point
gui_exec = _deprecation_func('zmlx.ui.GuiBuffer', 'gui_exec', '2025-1-21')


def is_array(o):
    """
    Checks if an object has a defined length and can use [] to get elements
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
    Send an email. Return whether the email was sent successfully.
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


# Alias of the function < for compatibility with previous code >
makedirs = make_dirs


def make_parent(path):
    """
    For any given file path, try to create an upper-level directory for it,
    so as much as possible to ensure that writing files to this location will succeed;
        Returns the entered file path
    """
    try:
        name = os.path.dirname(path)
        if not os.path.isdir(name):
            make_dirs(name)
        return path
    except:
        return path


def read_text(path, encoding=None, default=None):
    """
    Read text from a file in .TXT format
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


class _AppData(Object):
    """
    Data and file management
    """

    def __init__(self):
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
        """
        Add a search path < Avoid duplication >
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
        try:
            folder = os.path.join(self.folder, 'tags')
            make_dirs(folder)
            path = os.path.join(folder, datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
            with open(path, 'w') as f:
                f.write('\n')
        except:
            pass

    def log(self, text):
        """
        Record program operation information
        """
        try:
            folder = os.path.join(self.folder, 'logs')
            make_dirs(folder)
            with open(os.path.join(folder, datetime.datetime.now().strftime("%Y-%m-%d.log")), 'a') as f:
                f.write(f'{datetime.datetime.now()}: \n{text}\n\n\n')
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
        Get the files in the project directory
        """
        if len(args) == 0:
            # return to the root directory of the project file
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
        Returns all search paths. The first path is the preferred search path.
        After that are the current working path, cache path, custom path, and Python system path;
        Note:
            The returned path may be duplicate
        """
        paths = [os.getcwd(), self.proj()] if first is None else [first, os.getcwd(), self.proj()]
        return paths + [self.folder, os.path.join(self.folder, 'temp')] + self.paths + sys.path

    def find(self, *name, first=None):
        """
        Searches for the specified file and returns the path. If not found, None is returned
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
        """
        Search the file and return all found < and ensure that duplicate elements have been removed >
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


app_data = _AppData()


def log(text, tag=None):
    """
    Record a piece of information and, given the tag, make sure to record it only once a day.
    When given a tag, make sure that tag is a valid variable name.
    """
    if tag is not None:
        if app_data.has_tag_today(tag):
            return
        else:
            app_data.add_tag_today(tag)
    app_data.log(text)


def load_cdll(name, *, first=None):
    """
    Load C-Style Dll by the given file name and the folder.
    """
    path = app_data.find(name, first=first)
    if path is not None:
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
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        print(f'calling null function {self.name}(args={args}, kwargs={kwargs})')


def get_func(dll_obj, restype, name, *argtypes):
    """
    Configure a dll function
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
    """
    Returns the current file path
    """
    return os.path.realpath(__file__)


def get_dir():
    """
    Returns the path to the folder where the current file is located
    """
    return os.path.dirname(os.path.realpath(__file__))


dll = load_cdll('zml.dll' if is_windows else 'zml.so.1', first=get_dir())


class DllCore:
    """
    Manage errors, warnings, etc. in the C++ kernel
    """

    def __init__(self, dll):
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
        """
        Whether the dll was loaded correctly
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
        Return the version of the kernel (date of compilation)
        """
        if self.has_dll():
            return core.get_version()
        else:
            return 100101

    @property
    def compiler(self):
        """
        Returns the compiler used by the kernel and its version
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
        Declares that a function in the kernel dll will be used next
        """
        if self.has_dll():
            if self._dll_funcs.get(name) is not None:
                print(f'Warning: function <{name}> already exists')
            else:
                func = get_func(self.dll, restype, name, *argtypes)
                if func is not None:
                    self._dll_funcs[name] = lambda *args: self.run(lambda: func(*args))

    def __getattr__(self, name):
        """
        Attempts to return a dll function with a given name
        """
        return self._dll_funcs.get(name)


core = DllCore(dll=dll)


class Timer:
    """
    Used to assist in the execution time of statistical functions.
    For every function, there should be a key that represents the name of the function stored in memory.

    2023-7-7
    """

    def __init__(self, co):
        """
        Initialize with an empty table (dictionary). The key of the dictionary is the name of
        the function to be counted, and the value is the number of runs and the total time.
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
        """
        Call a function, and record the cpu time of the call, as well as the number of calls.
        Returns the result of the function.
        Note that this function will throw an exception for func to run.
        The argument after func is passed to func.
        """
        self.beg(key)
        r = func(*args, **kwargs)
        self.end(key)
        return r

    def __str__(self):
        """
        Converts data to string output.
        """
        return self.summary()

    def summary(self):
        """
        Returns cpu time-consuming statistics, only for calculation and testing
        """
        return self.co.timer_summary(0).decode()

    @property
    def key2nt(self):
        try:
            tmp = eval(self.summary())
            tmp.pop('enable', None)
            return tmp
        except:
            return {}

    def log(self, name, seconds):
        """
        Keep track of how long a process takes
        """
        self.co.timer_log(make_c_char_p(name), seconds)

    def clear(self):
        """
        reset
        """
        self.co.timer_reset()

    def enabled(self, value=None):
        """
        Whether the cpu timer is on
        """
        if value is not None:
            self.co.timer_enable(value)
        return self.co.timer_enabled()

    def beg(self, key):
        """
        Start a test
        """
        self.__key2t[key] = timeit.default_timer()

    def end(self, key):
        """
        End a test run (and record it)
        """
        t0 = self.__key2t.get(key, None)
        if t0 is not None:
            cpu_t = timeit.default_timer() - t0
            self.log(key, cpu_t)


timer = Timer(co=core)


def clock(func):
    """
    Timing for Python functions. Reference https://blog.csdn.net/BobAuditore/article/details/79377679

from zml import clock, timer
import time


@clock
def run(seconds):
    time.sleep(seconds)
    print(f"sleep for {seconds} seconds")


if __name__ == '__main__':
    for i in range(3):
        run(0.1)
    print(timer)
    """

    def clocked(*args, **kwargs):
        key = func.__name__
        timer.beg(key)
        result = func(*args, **kwargs)
        timer.end(key)
        return result

    return clocked


class _DataVersion:
    """
    Define the version of the data.
    The version number of the data is a 6-digit int (yymmdd), which is the date of the data
    """

    def __init__(self, value=version):
        """
        Initialize to set the default data version
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        self.__versions = {}
        self.__default = value

    def set(self, value=None, key=None):
        """
        Set version. 6-bit int
        """
        assert isinstance(value, int)
        assert 100000 <= value <= 999999
        if key is None:
            self.__default = value
        else:
            self.__versions[key] = value

    def __getattr__(self, key):
        """
        Returns the version of the data. 6-bit int
        """
        return self.__versions.get(key, self.__default)

    def __getitem__(self, key):
        """
        Returns the version of the data. 6-bit int
        """
        return self.__versions.get(key, self.__default)

    def __setitem__(self, key, value):
        """
        Set the version of the data. 6-bit int
        """
        self.set(key=key, value=value)


data_version = _DataVersion()

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

    core.use(None, 'str_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, String)
        core.str_clone(self.handle, other.handle)

    def make_copy(self, buf=None):
        if not isinstance(buf, String):
            buf = String()
        buf.clone(self)
        return buf


def get_time_compile():
    return core.time_compile


def run(fn):
    """
    Run code that needs to call memory and check for errors
    """
    return core.run(fn)


time_string = _deprecation_func('zmlx.filesys.tag', 'time_string', '2025-1-21')
is_time_string = _deprecation_func('zmlx.filesys.tag', 'is_time_string', '2025-1-21')
has_tag = _deprecation_func('zmlx.filesys.tag', 'has_tag', '2025-1-21')
print_tag = _deprecation_func('zmlx.filesys.tag', 'print_tag', '2025-1-21')

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
            self.core.use(None, 'lic_get_serial', c_void_p, c_bool, c_bool)
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

    def get_serial(self, base64=True, export_all=False):
        """
        Returns the usb serial number of this computer (one of them), used for registration
        """
        if self.core.has_dll():
            s = String()
            self.core.lic_get_serial(s.handle, base64, export_all)
            return s.to_str()

    @property
    def usb_serial(self):
        """
        Returns the usb serial number of this computer (one of them), used for registration
        """
        return self.get_serial()

    def create_permanent(self, serial):
        """
        Given a serial number (usb_serial), return a permanent authorization for the serial number.
        For testing only
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
        Stores the given licence data to the default location
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


lic = License(core=core)


def reg(code=None):
    """
    reg.
    When code is None, return the native serial number.
    If the length of code is less than 80, code is regarded as the serial number and licence data is created.
    Otherwise, code is treated as licence data, and save it locally.
    """
    if code is None:
        return lic.usb_serial
    else:
        assert isinstance(code, str)
        if len(code) < 80:
            return lic.create_permanent(code)
        else:
            lic.load(code)


first_only = _deprecation_func('zmlx.filesys.first_only', 'first_only', '2025-1-21')

core.use(c_double, 'test_loop', c_size_t, c_bool)


def test_loop(count, parallel=True):
    """
    Tests loops of a given length in the kernel and returns the time taken
    """
    return core.test_loop(count, parallel)


def about():
    """
    Return module information
    """
    info = f'Welcome to zml (v{version}; {core.time_compile}; {core.compiler})'
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
    dist = 0.0
    for i in range(min(len(p1), len(p2))):
        dist += (p1[i] - p2[i]) ** 2
    return dist ** 0.5


def get_norm(p):
    """
    Returns the distance from the origin
    """
    dist = 0.0
    for dim in range(len(p)):
        dist += p[dim] ** 2
    return dist ** 0.5


core.use(c_bool, 'confuse_file', c_char_p, c_char_p, c_char_p, c_bool)


def confuse_file(ipath, opath, password, is_encrypt=True):
    """
    Obfuscated encryption/decryption of file content.
    is_encrypt=True means encryption, is_encrypt=False means decryption
    """
    return core.confuse_file(make_c_char_p(ipath), make_c_char_p(opath), make_c_char_p(password), is_encrypt)


prepare_dir = _deprecation_func('zmlx.filesys.prepare_dir', 'prepare_dir', '2025-1-21')
time2str = _deprecation_func('zmlx.alg.time2str', 'time2str', '2025-1-21')
mass2str = _deprecation_func('zmlx.alg.mass2str', 'mass2str', '2025-1-21')
make_fpath = _deprecation_func('zmlx.filesys.make_fpath', 'make_fpath', '2025-1-21')
get_last_file = _deprecation_func('zmlx.filesys.get_last_file', 'get_last_file', '2025-1-21')
write_py = _deprecation_func('zmlx.io.python', 'write_py', '2025-1-21')
read_py = _deprecation_func('zmlx.io.python', 'read_py', '2025-1-21')


def parse_fid3(fluid_id):
    """
    Automatically identifies a given fluid ID as the ID of a certain component of a fluid
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
    """
    When reading a file, the input file name is checked. Where obj is the object that reads the file
    """
    assert isinstance(path, str), f'The given path <{path}> is not string while load {type(obj)}'
    assert os.path.isfile(path), f'The given path <{path}> is not file while load {type(obj)}'


def get_average_perm(p0, p1, get_perm, sample_dist=None, depth=0):
    """
    Return the average permeability < or average thermal conductivity > between two points
    NOTE:
        This function is only used to calculate the average permeability
            < series effect is taken into account when averaging >
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


add_keys = _deprecation_func('zmlx.utility.AttrKeys', 'add_keys', '2025-1-21')
AttrKeys = _deprecation_func('zmlx.utility.AttrKeys', 'AttrKeys', '2025-1-21')
install = _deprecation_func('zmlx.alg.install', 'install', '2025-1-21')


def get_index(index, count=None):
    """
    Returns the corrected sequence number. Make sure that 0 <= index < count is returned
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
    disable_timer = app_data.getenv(key='disable_timer', encoding='utf-8', default='False')
    if disable_timer == 'True':
        timer.enabled(False)
        app_data.log(f'timer disabled')
except:
    pass

try:
    app_data.log(f'import zml <zml: v{version}, Python: {sys.version}>')
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


class FieldAdaptor:
    def __getattr__(self, item):
        warnings.warn('zml.Field will be remove after 2025-1-21. use zmlx.utility.Field.Field instead',
                      DeprecationWarning)
        from zmlx.utility.Field import Field
        return getattr(Field, item)

    def __call__(self, *args, **kwargs):
        warnings.warn('zml.Field will be remove after 2025-1-21. use zmlx.utility.Field.Field instead',
                      DeprecationWarning)
        from zmlx.utility.Field import Field
        return Field(*args, **kwargs)


Field = FieldAdaptor()


class Vector(HasHandle):
    """
    Mapping C++ class: std::vector<double>
    """
    core.use(c_void_p, 'new_vf')
    core.use(None, 'del_vf', c_void_p)

    def __init__(self, value=None, path=None, size=None, handle=None):
        """
        Create this Vector object, and possibly initialize it
        """
        super(Vector, self).__init__(handle, core.new_vf, core.del_vf)
        if handle is None:
            if value is not None:
                self.set(value)
                return
            if path is not None:
                self.load(path)
                return
            if size is not None:
                self.size = size
                return
        else:
            assert value is None and path is None and size is None

    def __str__(self):
        return f'zml.Vector({self.to_list()})'

    core.use(None, 'vf_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.vf_save(self.handle, make_c_char_p(path))

    core.use(None, 'vf_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.vf_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vf_size', c_void_p)

    @property
    def size(self):
        return core.vf_size(self.handle)

    core.use(None, 'vf_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.vf_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_double, 'vf_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vf_get(self.handle, idx)

    core.use(None, 'vf_set', c_void_p, c_size_t, c_double)

    def __setitem__(self, idx, value):
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vf_set(self.handle, idx, value)

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

    def fill(self, value=0.0):
        """
        填充一个数值. 默认为0
        """
        p = self.pointer
        assert p is not None
        for i in range(self.size):
            p[i] = value

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

    core.use(None, 'vf_read', c_void_p, c_void_p)

    def read_memory(self, pointer):
        """
        读取内存数据
        """
        core.vf_read(self.handle, ctypes.cast(pointer, c_void_p))

    core.use(None, 'vf_write', c_void_p, c_void_p)

    def write_memory(self, pointer):
        """
        将数据写入到给定的内存地址
        """
        core.vf_write(self.handle, ctypes.cast(pointer, c_void_p))

    def read_numpy(self, data):
        warnings.warn('remove after 2025-6-2', DeprecationWarning)
        from zmlx.alg.Vector import read_numpy
        return read_numpy(self, data)

    def write_numpy(self, data):
        warnings.warn('remove after 2025-6-2', DeprecationWarning)
        from zmlx.alg.Vector import write_numpy
        return write_numpy(self, data)

    def to_numpy(self):
        warnings.warn('remove after 2025-6-2', DeprecationWarning)
        from zmlx.alg.Vector import to_numpy
        return to_numpy(self)

    core.use(c_void_p, 'vf_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.vf_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_double))


class IntVector(HasHandle):
    """
    映射C++类：std::vector<long long>
    """
    core.use(c_void_p, 'new_vi')
    core.use(None, 'del_vi', c_void_p)

    def __init__(self, value=None, handle=None):
        super(IntVector, self).__init__(handle, core.new_vi, core.del_vi)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'vi_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.vi_save(self.handle, make_c_char_p(path))

    core.use(None, 'vi_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.vi_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vi_size', c_void_p)

    @property
    def size(self):
        return core.vi_size(self.handle)

    core.use(None, 'vi_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.vi_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_int64, 'vi_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vi_get(self.handle, idx)

    core.use(None, 'vi_set', c_void_p, c_size_t, c_int64)

    def __setitem__(self, idx, value):
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vi_set(self.handle, idx, value)

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

    core.use(c_void_p, 'vi_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.vi_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_int64))


Int64Vector = IntVector


class UintVector(HasHandle):
    """
    映射C++类：std::vector<std::size_t>
    """
    core.use(c_void_p, 'new_vui')
    core.use(None, 'del_vui', c_void_p)

    def __init__(self, value=None, handle=None):
        super(UintVector, self).__init__(handle, core.new_vui, core.del_vui)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(None, 'vui_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.vui_save(self.handle, make_c_char_p(path))

    core.use(None, 'vui_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.vui_load(self.handle, make_c_char_p(path))

    core.use(None, 'vui_print', c_void_p, c_char_p)

    def print_file(self, path):
        if path is not None:
            core.vui_print(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'vui_size', c_void_p)

    @property
    def size(self):
        return core.vui_size(self.handle)

    core.use(None, 'vui_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.vui_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(c_size_t, 'vui_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vui_get(self.handle, idx)

    core.use(None, 'vui_set', c_void_p, c_size_t, c_size_t)

    def __setitem__(self, idx, value):
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vui_set(self.handle, idx, value)

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

    core.use(c_void_p, 'vui_pointer', c_void_p)

    @property
    def pointer(self):
        """
        首个元素的指针
        """
        ptr = core.vui_pointer(self.handle)
        if ptr:
            return ctypes.cast(ptr, POINTER(c_size_t))


class StrVector(HasHandle):
    core.use(c_void_p, 'new_vs')
    core.use(None, 'del_vs', c_void_p)

    def __init__(self, handle=None):
        super(StrVector, self).__init__(handle, core.new_vs, core.del_vs)

    core.use(c_size_t, 'vs_size', c_void_p)

    @property
    def size(self):
        return core.vs_size(self.handle)

    core.use(None, 'vs_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        core.vs_resize(self.handle, value)

    def __len__(self):
        return self.size

    core.use(None, 'vs_get', c_void_p, c_size_t, c_void_p)

    def __getitem__(self, idx):
        idx = get_index(idx, self.size)
        if idx is not None:
            s = String()
            core.vs_get(self.handle, idx, s.handle)
            return s.to_str()

    core.use(None, 'vs_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        idx = get_index(idx, self.size)
        if idx is not None:
            s = String(value=value)
            core.vs_set(self.handle, idx, s.handle)

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
    core.use(c_void_p, 'new_vp')
    core.use(None, 'del_vp', c_void_p)

    def __init__(self, value=None, handle=None):
        """
        初始化
        """
        super(PtrVector, self).__init__(handle, core.new_vp, core.del_vp)
        if handle is None:
            if value is not None:
                self.set(value)

    core.use(c_size_t, 'vp_size', c_void_p)

    @property
    def size(self):
        """
        元素的数量
        """
        return core.vp_size(self.handle)

    core.use(None, 'vp_resize', c_void_p, c_size_t)

    @size.setter
    def size(self, value):
        """
        设置元素的数量，并默认利用nullptr进行填充
        """
        core.vp_resize(self.handle, value)

    def __len__(self):
        """
        返回元素的数量
        """
        return self.size

    core.use(c_void_p, 'vp_get', c_void_p, c_size_t)

    def __getitem__(self, idx):
        """
        返回地址
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.vp_get(self.handle, idx)

    core.use(None, 'vp_set', c_void_p, c_size_t, c_void_p)

    def __setitem__(self, idx, value):
        """
        设置地址
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.vp_set(self.handle, idx, value)

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
    core.use(c_void_p, 'new_mat2')
    core.use(None, 'del_mat2', c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        super(Matrix2, self).__init__(handle, core.new_mat2, core.del_mat2)
        if handle is None:
            if path is not None:
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __str__(self):
        return f'zml.Matrix2(size={self.size})'

    core.use(None, 'mat2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.mat2_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.mat2_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat2_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat2_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.mat2_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.mat2_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat2_size_0', c_void_p)
    core.use(c_size_t, 'mat2_size_1', c_void_p)

    @property
    def size_0(self):
        return core.mat2_size_0(self.handle)

    @property
    def size_1(self):
        return core.mat2_size_1(self.handle)

    core.use(None, 'mat2_resize', c_void_p, c_size_t, c_size_t)

    def resize(self, value):
        assert len(value) == 2
        core.mat2_resize(self.handle, value[0], value[1])

    @property
    def size(self):
        return self.size_0, self.size_1

    @size.setter
    def size(self, value):
        self.resize(value)

    core.use(c_double, 'mat2_get', c_void_p, c_size_t, c_size_t)

    def get(self, key0, key1):
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            return core.mat2_get(self.handle, key0, key1)

    core.use(None, 'mat2_set', c_void_p, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, value):
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        if key0 is not None and key1 is not None:
            assert key0 < self.size_0
            assert key1 < self.size_1
            core.mat2_set(self.handle, key0, key1, value)

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

    core.use(None, 'mat2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, Matrix2)
        core.mat2_clone(self.handle, other.handle)

    core.use(None, 'mat2_fill', c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """
        填充矩阵的元素. 当parallel为True的时候，则在内核层面，并行地进行.
        """
        core.mat2_fill(self.handle, value, parallel)


class Matrix3(HasHandle):
    """
    映射C++类：zml::matrix_ty<double, 3>. 一个三维的矩阵，其中的每一个元素都是浮点数.
    """
    core.use(c_void_p, 'new_mat3')
    core.use(None, 'del_mat3', c_void_p)

    def __init__(self, path=None, handle=None, size=None, value=None):
        """
        初始化。当给定size的时候，将设置大小。当给定value的时候，将填充初始值.
        """
        super(Matrix3, self).__init__(handle, core.new_mat3, core.del_mat3)
        if handle is None:
            if path is not None:
                self.load(path)
            if size is not None:
                self.resize(size)
            if value is not None:
                self.fill(value)

    def __str__(self):
        return f'zml.Matrix3(size={self.size})'

    core.use(None, 'mat3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'mat3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'mat3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'mat3_size_0', c_void_p)
    core.use(c_size_t, 'mat3_size_1', c_void_p)
    core.use(c_size_t, 'mat3_size_2', c_void_p)

    @property
    def size_0(self):
        """
        第0个维度的大小
        """
        return core.mat3_size_0(self.handle)

    @property
    def size_1(self):
        """
        第1个维度的大小
        """
        return core.mat3_size_1(self.handle)

    @property
    def size_2(self):
        """
        第2个维度的大小
        """
        return core.mat3_size_2(self.handle)

    core.use(None, 'mat3_resize', c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        """
        改变形状
        """
        assert len(value) == 3
        core.mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        """
        矩阵大小
        """
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        """
        矩阵大小
        """
        self.resize(value)

    core.use(c_double, 'mat3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """
        读取元素
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return core.mat3_get(self.handle, key0, key1, key2)

    core.use(None, 'mat3_set', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def set(self, key0, key1, key2, value):
        """
        设置元素
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            core.mat3_set(self.handle, key0, key1, key2, value)

    def __getitem__(self, key):
        """
        读取元素
        """
        assert len(key) == 3
        return self.get(*key)

    def __setitem__(self, key, value):
        """
        设置元素
        """
        assert len(key) == 3
        self.set(*key, value)

    core.use(None, 'mat3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, Matrix3)
        core.mat3_clone(self.handle, other.handle)

    core.use(None, 'mat3_fill', c_void_p, c_double, c_bool)

    def fill(self, value, parallel=False):
        """
        填充矩阵的元素. 当parallel为True的时候，则在内核层面，并行地进行.
        """
        core.mat3_fill(self.handle, value, parallel)


class Tensor3Matrix3(HasHandle):
    """
    映射C++类：zml::matrix_ty<zml::tensor3_ty, 3>
    """
    core.use(c_void_p, 'new_ts3mat3')
    core.use(None, 'del_ts3mat3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Tensor3Matrix3, self).__init__(handle, core.new_ts3mat3, core.del_ts3mat3)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'ts3mat3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.ts3mat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.ts3mat3_load(self.handle, make_c_char_p(path))

    core.use(None, 'ts3mat3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'ts3mat3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.ts3mat3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.ts3mat3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'ts3mat3_size_0', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_1', c_void_p)
    core.use(c_size_t, 'ts3mat3_size_2', c_void_p)

    @property
    def size_0(self):
        return core.ts3mat3_size_0(self.handle)

    @property
    def size_1(self):
        return core.ts3mat3_size_1(self.handle)

    @property
    def size_2(self):
        return core.ts3mat3_size_2(self.handle)

    core.use(None, 'ts3mat3_resize', c_void_p, c_size_t, c_size_t, c_size_t)

    def resize(self, value):
        assert len(value) == 3
        core.ts3mat3_resize(self.handle, value[0], value[1], value[2])

    @property
    def size(self):
        return self.size_0, self.size_1, self.size_2

    @size.setter
    def size(self, value):
        self.resize(value)

    core.use(c_void_p, 'ts3mat3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, key0, key1, key2):
        """
        返回某个元素的引用.
        """
        key0 = get_index(key0, self.size_0)
        key1 = get_index(key1, self.size_1)
        key2 = get_index(key2, self.size_2)
        if key0 is not None and key1 is not None and key2 is not None:
            return Tensor3(handle=core.ts3mat3_get(self.handle, key0, key1, key2))

    def __getitem__(self, key):
        """
        返回某个元素的引用.
        """
        assert len(key) == 3
        return self.get(*key)

    core.use(None, 'ts3mat3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, Tensor3Matrix3)
        core.ts3mat3_clone(self.handle, other.handle)

    core.use(None, 'ts3mat3_interp', c_void_p, c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double, c_double, c_double)

    def get_interp(self, left, step, pos, buffer=None):
        """
        将矩阵视为插值，返回插值数据
        """
        assert len(left) == 3 and len(step) == 3 and len(pos) == 3
        if not isinstance(buffer, Tensor3):
            buffer = Tensor3()
        core.ts3mat3_interp(self.handle, buffer.handle, left[0], left[1], left[2],
                            step[0], step[1], step[2], pos[0], pos[1], pos[2])
        return buffer


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.interp1_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp1_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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

    core.use(None, 'interp1_clear', c_void_p)

    def clear(self):
        core.interp1_clear(self.handle)

    core.use(None, 'interp1_get_vx', c_void_p, c_void_p)
    core.use(None, 'interp1_get_vy', c_void_p, c_void_p)

    def get_data(self, x=None, y=None):
        """
        返回内核数据的拷贝
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        创建插值。其中y=get_value(x)为给定的函数.

        注意：
            当xmin==xmax或者dx==0的时候，在x方向上是常数
            当ymin==ymax或者dy==0的时候，在y方向上是常数
        """
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double)
        core.interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, kernel(get_value))

    @staticmethod
    def create_const(value):
        """
        创建常量场(给定的数值)
        """
        f = Interp2()
        f.create(xmin=0, dx=0, xmax=0, ymin=0, dy=0, ymax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp2_empty', c_void_p)

    @property
    def empty(self):
        return core.interp2_empty(self.handle)

    core.use(None, 'interp2_clear', c_void_p)

    def clear(self):
        core.interp2_clear(self.handle)

    core.use(c_double, 'interp2_get', c_void_p, c_double, c_double, c_bool)

    def get(self, x, y, no_external=True):
        """
        返回给定坐标x, y下的数值
        """
        return core.interp2_get(self.handle, x, y, no_external)

    def __call__(self, *args, **kwargs):
        """
        返回给定坐标x, y下的数值
        """
        return self.get(*args, **kwargs)

    core.use(c_bool, 'interp2_is_inner', c_void_p, c_double, c_double)

    def is_inner(self, x, y):
        """
        判断给定的坐标是否为内部的点(不需要外插)
        """
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        assert xmin <= xmax and dx >= 0
        assert ymin <= ymax and dy >= 0
        assert zmin <= zmax and dz >= 0
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double)
        core.interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                            kernel(get_value))

    @staticmethod
    def create_const(value):
        """
        创建常量场(给定的数值)
        """
        f = Interp3()
        f.create(xmin=0, dx=0, xmax=0,
                 ymin=0, dy=0, ymax=0,
                 zmin=0, dz=0, zmax=0, get_value=lambda *args: value)
        return f

    core.use(c_bool, 'interp3_empty', c_void_p)

    @property
    def empty(self):
        return core.interp3_empty(self.handle)

    core.use(None, 'interp3_clear', c_void_p)

    def clear(self):
        core.interp3_clear(self.handle)

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

    def __init__(self, data=None, path=None, handle=None):
        super(FileMap, self).__init__(handle, core.new_fmap, core.del_fmap)
        if handle is None:
            if data is not None:
                self.data = data
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

    core.use(c_void_p, 'fmap_get', c_void_p, c_char_p)

    def get(self, key):
        """
        当存在key的时候，返回key内容的引用。调用之前必须检查key是否存在
        """
        handle = core.fmap_get(self.handle, make_c_char_p(key))
        if handle:
            return FileMap(handle=handle)

    core.use(None, 'fmap_set', c_void_p, c_void_p, c_char_p)

    def set(self, key, fmap):
        """
        将fmap存储到key里面
        """
        if isinstance(fmap, FileMap):
            core.fmap_set(self.handle, fmap.handle, make_c_char_p(key))
        else:
            fmap = FileMap(data=fmap)
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
            _check_ipath(path, self)
            core.fmap_load(self.handle, make_c_char_p(path))

    core.use(c_char_p, 'fmap_get_char_p', c_void_p)

    @property
    def data(self):
        return core.fmap_get_char_p(self.handle).decode()

    core.use(None, 'fmap_set_char_p', c_void_p, c_char_p)

    @data.setter
    def data(self, value):
        if not isinstance(value, str):
            value = f'{value}'
        core.fmap_set_char_p(self.handle, make_c_char_p(value))

    core.use(c_void_p, 'fmap_get_data', c_void_p)

    @property
    def buffer(self):
        return String(handle=core.fmap_get_data(self.handle))

    core.use(None, 'fmap_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, FileMap)
        core.fmap_clone(self.handle, other.handle)


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.array2_save(self.handle, make_c_char_p(path))

    core.use(None, 'array2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        dim = get_index(dim, 2)
        if dim is not None:
            return core.array2_get(self.handle, dim)

    core.use(None, 'array2_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        dim = get_index(dim, 2)
        if dim is not None:
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

    def clone(self, other):
        """
        克隆数据
        """
        for i in range(2):
            self.set(i, other[i])

    core.use(c_double, 'array2_get_angle', c_void_p)

    def get_angle(self):
        return core.array2_get_angle(self.handle)


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.array3_save(self.handle, make_c_char_p(path))

    core.use(None, 'array3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        dim = get_index(dim, 3)
        if dim is not None:
            return core.array3_get(self.handle, dim)

    core.use(None, 'array3_set', c_void_p, c_size_t, c_double)

    def set(self, dim, value):
        dim = get_index(dim, 3)
        if dim is not None:
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

    def clone(self, other):
        """
        克隆数据
        """
        for i in range(3):
            self.set(i, other[i])


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.tensor2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
            return core.tensor2_get(self.handle, i, j)

    core.use(None, 'tensor2_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        assert len(key) == 2
        i = get_index(key[0], 2)
        j = get_index(key[1], 2)
        if i is not None and j is not None:
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

    core.use(None, 'tensor2_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, Tensor2)
        core.tensor2_clone(self.handle, other.handle)

    core.use(None, 'tensor2_rotate', c_void_p, c_void_p, c_double)

    def get_rotate(self, angle, buffer=None):
        """
        将张量旋转给定的角度.
        """
        if not isinstance(buffer, Tensor2):
            buffer = Tensor2()
        core.tensor2_rotate(self.handle, buffer.handle, angle)
        return buffer

    core.use(c_double, 'tensor2_get_max_principle_value', c_void_p)

    @property
    def max_principle_value(self):
        return core.tensor2_get_max_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_min_principle_value', c_void_p)

    @property
    def min_principle_value(self):
        return core.tensor2_get_min_principle_value(self.handle)

    core.use(c_double, 'tensor2_get_principle_angle', c_void_p)

    @property
    def principle_angle(self):
        return core.tensor2_get_principle_angle(self.handle)


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.tensor3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
            return core.tensor3_get(self.handle, i, j)

    core.use(None, 'tensor3_set', c_void_p, c_size_t, c_size_t, c_double)

    def __setitem__(self, key, value):
        assert len(key) == 2
        i = get_index(key[0], 3)
        j = get_index(key[1], 3)
        if i is not None and j is not None:
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

    def __add__(self, other):
        return Tensor3(xx=self.xx + other.xx,
                       yy=self.yy + other.yy,
                       zz=self.zz + other.zz,
                       xy=self.xy + other.xy,
                       yz=self.yz + other.yz,
                       zx=self.zx + other.zx,
                       )

    def __sub__(self, other):
        return Tensor3(xx=self.xx - other.xx,
                       yy=self.yy - other.yy,
                       zz=self.zz - other.zz,
                       xy=self.xy - other.xy,
                       yz=self.yz - other.yz,
                       zx=self.zx - other.zx,
                       )

    def __mul__(self, value):
        return Tensor3(xx=self.xx * value,
                       yy=self.yy * value,
                       zz=self.zz * value,
                       xy=self.xy * value,
                       yz=self.yz * value,
                       zx=self.zx * value,
                       )

    def __truediv__(self, value):
        return Tensor3(xx=self.xx / value,
                       yy=self.yy / value,
                       zz=self.zz / value,
                       xy=self.xy / value,
                       yz=self.yz / value,
                       zx=self.zx / value,
                       )

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

    core.use(None, 'tensor3_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        克隆数据
        """
        assert isinstance(other, Tensor3)
        core.tensor3_clone(self.handle, other.handle)


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.tensor2interp2_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor2interp2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_size_t)
        core.tensor2interp2_create(self.handle, xmin, dx, xmax, ymin, dy, ymax,
                                   kernel(get_value))

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
    """
    三阶张量的三维插值. 
    """
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.tensor3interp3_save(self.handle, make_c_char_p(path))

    core.use(None, 'tensor3interp3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        kernel = CFUNCTYPE(c_double, c_double, c_double, c_double, c_size_t)
        core.tensor3interp3_create(self.handle, xmin, dx, xmax, ymin, dy, ymax, zmin, dz, zmax,
                                   kernel(get_value))

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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.coord2_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
    """
    三维笛卡尔坐标系. 用以point和tensor的转换.
    """
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
        if handle is None:  # 此时为新建对象.
            if path is not None:
                self.load(path)
            if origin is not None and xdir is not None and ydir is not None:
                self.set(origin, xdir, ydir)
        else:
            assert origin is None and xdir is None and ydir is None

    core.use(None, 'coord3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.coord3_save(self.handle, make_c_char_p(path))

    core.use(None, 'coord3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
    三维网格类，有点(Node)、线(Link)、面(Face)、体(Body)所组成的网络.
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
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_node_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_node_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_node_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_node_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_node_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def links(self):
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self):
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self):
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        core.use(c_double, 'mesh3_get_node_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_node_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            if index is None:
                return default_val
            value = core.mesh3_get_node_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
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
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_link_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_link_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_link_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        core.use(c_size_t, 'mesh3_get_link_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_link_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def faces(self):
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self):
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

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

        def get_attr(self, index, default_val=None, **valid_range):
            if index is None:
                return default_val
            value = core.mesh3_get_link_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
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
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_face_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_face_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_face_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_face_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index):
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_face_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)

        @property
        def nodes(self):
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self):
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def bodies(self):
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

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

        def get_attr(self, index, default_val=None, **valid_range):
            if index is None:
                return default_val
            value = core.mesh3_get_face_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
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
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_body_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)

        core.use(c_size_t, 'mesh3_get_body_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index):
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_body_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)

        core.use(c_size_t, 'mesh3_get_body_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_body_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)

        @property
        def nodes(self):
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self):
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self):
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

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

        def get_attr(self, index, default_val=None, **valid_range):
            if index is None:
                return default_val
            value = core.mesh3_get_body_attr(self.model.handle, self.index, index)
            if _attr_in_range(value, **valid_range):
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
        return (f'zml.Mesh3(handle = {self.handle}, node_n = {self.node_number}, link_n = {self.link_number}, '
                f'face_n = {self.face_number}, body_n = {self.body_number})')

    core.use(None, 'mesh3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.mesh3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mesh3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        index = get_index(index, self.node_number)
        if index is not None:
            return Mesh3.Node(self, index)

    def get_link(self, index):
        index = get_index(index, self.link_number)
        if index is not None:
            return Mesh3.Link(self, index)

    def get_face(self, index):
        index = get_index(index, self.face_number)
        if index is not None:
            return Mesh3.Face(self, index)

    def get_body(self, index):
        index = get_index(index, self.body_number)
        if index is not None:
            return Mesh3.Body(self, index)

    @property
    def nodes(self):
        return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

    @property
    def links(self):
        return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

    @property
    def faces(self):
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def bodies(self):
        return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

    core.use(c_size_t, 'mesh3_add_node', c_void_p, c_double, c_double, c_double)

    def add_node(self, x, y, z):
        index = core.mesh3_add_node(self.handle, x, y, z)
        return self.get_node(index)

    core.use(c_size_t, 'mesh3_add_link', c_void_p, c_size_t, c_size_t)

    def add_link(self, nodes):
        """
        注意，如果添加的link已经存在，则直接返回已有的link
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
        根据给定的links来创建一个face并且返回。注意，在创建的过程中，会自动识别links的端点的位置，并且对nodes进行
        排序，从而尽可能保证，face的所有的nodes，恰好能够按照顺序形成一个闭环。 Comment @ 23-09-16
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
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_links(self.handle, kernel(should_del))

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
from zml import Mesh3
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


class LinearExpr(HasHandle):
    core.use(c_void_p, 'new_lexpr')
    core.use(None, 'del_lexpr', c_void_p)

    def __init__(self, handle=None):
        super(LinearExpr, self).__init__(handle, core.new_lexpr, core.del_lexpr)

    core.use(None, 'lexpr_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.lexpr_save(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.lexpr_load(self.handle, make_c_char_p(path))

    core.use(None, 'lexpr_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'lexpr_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.lexpr_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
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
        return self.handle == rhs.handle

    def __ne__(self, rhs):
        return not (self == rhs)

    def __str__(self):
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
        线性表达式的常数
        """
        return core.lexpr_get_c(self.handle)

    @c.setter
    def c(self, value):
        """
        线性表达式的常数
        """
        core.lexpr_set_c(self.handle, value)

    def set_c(self, value):
        self.c = value
        return self

    core.use(c_size_t, 'lexpr_get_length', c_void_p)

    @property
    def length(self):
        """
        线性表达式除了常数项之外的项数
        """
        return core.lexpr_get_length(self.handle)

    def __len__(self):
        """
        线性表达式除了常数项之外的项数
        """
        return self.length

    core.use(c_size_t, 'lexpr_get_index', c_void_p, c_size_t)
    core.use(c_double, 'lexpr_get_weight', c_void_p, c_size_t)

    def __getitem__(self, i):
        """
        返回第i项的序号和系数
        """
        i = get_index(i, self.length)
        if i is not None:
            index = core.lexpr_get_index(self.handle, i)
            weight = core.lexpr_get_weight(self.handle, i)
            return index, weight

    core.use(None, 'lexpr_add', c_void_p, c_size_t, c_double)

    def add(self, index, weight):
        """
        添加一项
        """
        core.lexpr_add(self.handle, index, weight)
        return self

    core.use(None, 'lexpr_clear', c_void_p)

    def clear(self):
        """
        清除所有的项，并将常数项设置为0
        """
        core.lexpr_clear(self.handle)
        return self

    core.use(None, 'lexpr_merge', c_void_p)

    def merge(self):
        """
        合并系数(并且删除系数为0的项)
        """
        core.lexpr_merge(self.handle)

    core.use(None, 'lexpr_plus', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lexpr_multiply', c_void_p, c_size_t, c_double)

    def __add__(self, other):
        assert isinstance(other, LinearExpr)
        result = LinearExpr()
        core.lexpr_plus(result.handle, self.handle, other.handle)
        return result

    def __sub__(self, other):
        return self.__add__(other * (-1.0))

    def __mul__(self, scale):
        result = LinearExpr()
        core.lexpr_multiply(result.handle, self.handle, scale)
        return result

    def __truediv__(self, scale):
        return self.__mul__(1.0 / scale)

    @staticmethod
    def create(index):
        """
        创建仅包含一项的线性表达式
        """
        lexpr = LinearExpr()
        lexpr.c = 0
        lexpr.add(index, 1.0)
        return lexpr

    @staticmethod
    def create_constant(c):
        """
        创建常量
        """
        lexpr = LinearExpr()
        lexpr.c = c
        return lexpr


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
        super(DynSys, self).__init__(handle, core.new_dynsys, core.del_dynsys)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'dynsys_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.dynsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'dynsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_pos(self.handle, idx)

    core.use(None, 'dynsys_set_pos', c_void_p, c_size_t, c_double)

    def set_pos(self, idx, value):
        """
        自由度的当前值.
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_pos(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_vel', c_void_p, c_size_t)

    def get_vel(self, idx):
        """
        自由度的速度.
            参考对 get_pos的注释. 返回对应自由度运动的速度.
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_vel(self.handle, idx)

    core.use(None, 'dynsys_set_vel', c_void_p, c_size_t, c_double)

    def set_vel(self, idx, value):
        """
        自由度的速度
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_vel(self.handle, idx, value)

    core.use(c_double, 'dynsys_get_mas', c_void_p, c_size_t)

    def get_mas(self, idx):
        """
        自由度的质量.
            用以刻画该自由度的惯性.
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            return core.dynsys_get_mas(self.handle, idx)

    core.use(None, 'dynsys_set_mas', c_void_p, c_size_t, c_double)

    def set_mas(self, idx, value):
        """
        自由度的质量.
            用以刻画该自由度的惯性.
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            core.dynsys_set_mas(self.handle, idx, value)

    core.use(c_void_p, 'dynsys_get_p2f', c_void_p, c_size_t)

    def get_p2f(self, idx):
        """
        根据位置计算自由度的受力. 这个受力是一个线性表达式，即建立这个自由度的受力与自由度位置(以及其它多个自由度的位置)之间的线性关系.
            这里所谓的受力，即自由度的质量乘以自由度的加速度.
        """
        idx = get_index(idx, self.size)
        if idx is not None:
            handle = core.dynsys_get_p2f(self.handle, idx)
            if handle > 0:
                return LinearExpr(handle=handle)

    core.use(c_double, 'dynsys_get_lexpr_value', c_void_p, c_void_p)

    def get_lexpr_value(self, lexpr):
        """
        返回一个关于此系数各个自由度的线性表达式的取值. 有些内容，比如单元的应力、应变等，都可以书写成为自由度的线性表达式。
        有了这个表达式之后，后续就可以比较快速方便地计算出这些值.
        """
        assert isinstance(lexpr, LinearExpr)
        return core.dynsys_get_lexpr_value(self.handle, lexpr.handle)


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

        def get_attr(self, index, default_val=None, **valid_range):
            """
            该Spring的第index个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
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
        return (f'zml.SpringSys(handle = {self.handle}, node_n = {self.node_number}, '
                f'virtual_node_n = {self.virtual_node_number}, spring_n = {self.spring_number})')

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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            assert isinstance(path, str)
            core.springsys_save(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.springsys_load(self.handle, make_c_char_p(path))

    core.use(None, 'springsys_print_node_pos', c_void_p, c_char_p)

    def print_node_pos(self, path):
        """
        打印node的位置
        """
        assert isinstance(path, str)
        core.springsys_print_node_pos(self.handle, make_c_char_p(path))

    def iterate(self, dt, dynsys, solver):
        """
        向前迭代dt时间步长。具体地，将执行如何步骤：
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
        index = get_index(index, self.node_number)
        if index is not None:
            return SpringSys.Node(self, index)

    def get_virtual_node(self, index):
        """
        返回虚拟节点对象
        """
        index = get_index(index, self.virtual_node_number)
        if index is not None:
            return SpringSys.VirtualNode(self, index)

    def get_spring(self, index):
        """
        返回弹簧对象
        """
        index = get_index(index, self.spring_number)
        if index is not None:
            return SpringSys.Spring(self, index)

    def get_damper(self, index):
        """
        返回阻尼器对象
        """
        index = get_index(index, self.damper_number)
        if index is not None:
            return SpringSys.Damper(self, index)

    @property
    def nodes(self):
        return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

    @property
    def virtual_nodes(self):
        return Iterator(self, self.virtual_node_number, lambda m, ind: m.get_virtual_node(ind))

    @property
    def springs(self):
        return Iterator(self, self.spring_number, lambda m, ind: m.get_spring(ind))

    @property
    def dampers(self):
        return Iterator(self, self.damper_number, lambda m, ind: m.get_damper(ind))

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
        获得所有node的x, y, z坐标
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
        """
        将节点的质量、速度、位置导出到dynsys(需要在每一步执行)
        """
        core.springsys_export_mas_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_export_p2f', c_void_p, c_void_p)

    def export_p2f(self, dynsys):
        """
        将系数矩阵导出到dynsys (需要在发生显著变形的时候去调用)
        """
        core.springsys_export_p2f(self.handle, dynsys.handle)

    core.use(None, 'springsys_update_pos_vel', c_void_p, c_void_p)

    def update_pos_vel(self, dynsys):
        """
        从dynsys读取数据，更新各个Node的位置和速度
        """
        core.springsys_update_pos_vel(self.handle, dynsys.handle)

    core.use(None, 'springsys_apply_dampers', c_void_p, c_double)

    def apply_dampers(self, dt):
        """
        应用减速过程
        """
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

        def get_attr(self, index, default_val=None, **valid_range):
            """
            第index个自定义属性
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
            第index个自定义属性
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
            return core.seepage_mesh_cell_get_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            return self.face_number

        core.use(c_size_t, 'seepage_mesh_cell_get_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index):
            index = get_index(index, self.face_number)
            return self.model.get_face(core.seepage_mesh_cell_get_face_id(self.model.handle, self.index, index))

        core.use(c_size_t, 'seepage_mesh_cell_get_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index):
            index = get_index(index, self.cell_number)
            return self.model.get_cell(core.seepage_mesh_cell_get_cell_id(self.model.handle, self.index, index))

        @property
        def cells(self):
            """
            此Cell周围的所有Cell
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            此Cell周围的所有Face
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

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
            return (f'zml.SeepageMesh.Face(handle = {self.model.handle}, index = {self.index}, '
                    f'area = {self.area}, length = {self.length}) ')

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
            i = get_index(i, 2)
            if i is not None:
                if i > 0:
                    return self.model.get_cell(self.cell_i1)
                else:
                    return self.model.get_cell(self.cell_i0)

        def cells(self):
            return self.get_cell(0), self.get_cell(1)

        core.use(c_double, 'seepage_mesh_get_face_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            第index个自定义属性
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.seepage_mesh_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
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
        """
        return core.seepage_mesh_get_cell_n(self.handle)

    def get_cell(self, ind):
        """
        返回第ind个cell
        """
        ind = get_index(ind, self.cell_number)
        if ind is not None:
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
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        用以迭代所有的face
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def volume(self):
        """
        返回整个模型整体的体积
        """
        vol = 0
        for cell in self.cells:
            vol += cell.vol
        return vol

    def load_ascii(self, *args, **kwargs):
        warnings.warn('SeepageMesh.load_ascii will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.ascii import load_ascii
        load_ascii(*args, **kwargs, mesh=self)

    def save_ascii(self, *args, **kwargs):
        warnings.warn('SeepageMesh.save_ascii will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.ascii import save_ascii
        save_ascii(*args, **kwargs, mesh=self)

    @staticmethod
    def load_mesh(*args, **kwargs):
        warnings.warn('SeepageMesh.load_mesh will be removed after 2025-5-27, '
                      'please use the function in zmlx.seepage_mesh.load_mesh instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.load_mesh import load_mesh as load
        return load(*args, **kwargs)

    @staticmethod
    def create_cube(*args, **kwargs):
        warnings.warn('The zml.SeepageMesh.create_cube will be removed after 2025-5-27. '
                      'please use zmlx.seepage_mesh.cube.create_cube instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.cube import create_cube as create
        return create(*args, **kwargs)

    @staticmethod
    def create_cylinder(*args, **kwargs):
        warnings.warn('The zml.SeepageMesh.create_cylinder will be removed after 2025-5-27. '
                      'please use zmlx.seepage_mesh.cylinder.create_cylinder instead',
                      DeprecationWarning)
        from zmlx.seepage_mesh.cylinder import create_cylinder as create
        return create(*args, **kwargs)

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
            i = get_index(i, self.size)
            if i is not None:
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.element_map_save(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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


class Groups(HasHandle):
    core.use(c_void_p, 'new_groups')
    core.use(None, 'del_groups', c_void_p)

    def __init__(self, handle=None):
        super(Groups, self).__init__(handle, core.new_groups, core.del_groups)

    core.use(None, 'groups_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.groups_save(self.handle, make_c_char_p(path))

    core.use(None, 'groups_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.groups_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'groups_size', c_void_p)

    @property
    def size(self):
        return core.groups_size(self.handle)

    core.use(c_void_p, 'groups_get', c_void_p, c_size_t)

    def get(self, idx):
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
            初始化一个反应。当给定path的时候，则载入之前创建好并序列化存储的反应。
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
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.reaction_save(self.handle, make_c_char_p(path))

        core.use(None, 'reaction_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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
            发生1kg物质的化学反应<1kg的左侧物质，转化为1kg的右侧物质>释放的热量，单位焦耳.
            注意，如果反应是吸热反应，则此heat为负值.
            """
            return core.reaction_get_dheat(self.handle)

        @heat.setter
        def heat(self, value):
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
            和heat对应的参考温度，只有当反应前后的温度都等于此temp的时候，释放的热量才可以使用heat来定义.
            """
            return core.reaction_get_t0(self.handle)

        @temp.setter
        def temp(self, value):
            core.reaction_set_t0(self.handle, value)

        core.use(None, 'reaction_set_p2t', c_void_p, c_void_p, c_void_p)

        def set_p2t(self, p, t):
            """
            设置不同的压力下，反应可以发生的临界温度. 对于吸热反应，只有当温度大于此临界温度的时候，反应才会发生；
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
                对于吸热反应，随着温度的增加，反应的速率应当增加；
                对于放热反应，随着温度的降低，反应的速率降低；
                当温度偏移量为0的时候，反应的速率为0.
            此处，反应的速率定义为，对于1kg的物质，在1s内发生反应的质量.
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
            assert fa_t is not None
            assert fa_c is not None
            assert abs(weight) <= 1.00001
            core.reaction_add_component(self.handle, *parse_fid3(index), weight, fa_t, fa_c)

        core.use(None, 'reaction_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的反应组分
            """
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
            """
            清除所有的抑制剂定义
            """
            core.reaction_clear_inhibitors(self.handle)

        core.use(None, 'reaction_react', c_void_p, c_void_p, c_double, c_void_p)

        def react(self, model, dt, buf=None):
            """
            将该反应作用到Seepage的所有的Cell上dt时间。这个过程会修改model中各个Cell中相应组分的质量和温度，但是会保证总的质量不会发生改变。
            其中:
                buf为一个缓冲区(double*)，记录各个Cell上发生的反应的质量;
                    务必确保此缓冲区的大小足够，否则会出现致命的错误!!!

            返回
                反应发生的总的质量.
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
            """
            warnings.warn('Use <adjust_weights>. <adjust_widghts> will be removed after 2024-1-1',
                          DeprecationWarning)
            self.adjust_weights()

        core.use(c_double, 'reaction_get_rate', c_void_p, c_void_p)

        def get_rate(self, cell):
            """
            获得给定Cell在当前状态(温度、压力、抑制剂等条件)下的<瞬时的>反应速率. 此函数主要用于测试.
            """
            assert isinstance(cell, Seepage.CellData)
            return core.reaction_get_rate(self.handle, cell.handle)

        core.use(None, 'reaction_set_idt', c_void_p, c_size_t)
        core.use(c_size_t, 'reaction_get_idt', c_void_p)

        @property
        def idt(self):
            """
            Cell的属性ID。Cell的此属性用以定义反应作用到该Cell上的时候，平衡温度的调整量.
            这允许在不同的Cell上，有不同的反应温度.
            默认情况下，此属性不定义，则反应在各个Cell上的温度是一样的。
            注：
                此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。
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
            和idt配合使用. 在Cell定义温度调整量的时候，可以利用这个权重再对这个调整量进行（缩放）调整.
            比如，当Cell给的温度的调整量的单位不是K的时候，可以利用wdt属性来添加一个倍率.
            注：
                此属性为一个测试功能，当后续有更好的实现方案的时候，可能会被移除。
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
            Cell的属性ID。
            Cell的此属性用以定义反应作用到该Cell上的时候，反应速率应该乘以的倍数。若定义这个属性，且Cell的这个属性值小于等于0，那么
            反应在这个Cell上将不会发生
                Note: 如果希望某个反应只在部分Cell上发生，则可以利用这个属性来实现
            """
            return core.reaction_get_irate(self.handle)

        @irate.setter
        def irate(self, value):
            core.reaction_set_irate(self.handle, value)

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
                当给定handle的时候，则创建当前数据的引用，此时忽略其它所有的参数。
                当handle为None的时候:
                    当给定path，则从文件载入，否则，将根据其它参数进行初始化.
                    特别注意:
                        当den或者vis为None的时候，将清除C++层面的默认数据
            """
            super(Seepage.FluDef, self).__init__(handle, core.new_fludef, core.del_fludef)
            if handle is None:
                # 现在，这是一个新建数据，将进行必要的初始化
                if path is not None:
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
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.fludef_save(self.handle, make_c_char_p(path))

        core.use(None, 'fludef_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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

        @property
        def den(self):
            """
            流体密度的插值
                只有当组分的数量为0的时候才可以使用, 否则触发异常
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_den(self.handle))

        @den.setter
        def den(self, value):
            """
            设置密度数据，参数为None的时候，则清除现有数据
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
            流体粘性的插值
                只有当组分的数量为0的时候才可以使用, 否则触发异常
            """
            assert self.component_number == 0
            return Interp2(handle=core.fludef_get_vis(self.handle))

        @vis.setter
        def vis(self, value):
            """
            设置粘性数据，参数为None的时候，则清除现有数据
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
            返回给定压力和温度下的密度
            """
            return self.den(pressure, temp)

        def get_vis(self, pressure, temp):
            """
            返回给定压力和温度下的粘性
            """
            return self.vis(pressure, temp)

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
            assert 0.1 <= value <= 1.0e8
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
            idx = get_index(idx, self.component_number)
            if idx is not None:
                return Seepage.FluDef(handle=core.fludef_get_component(self.handle, idx))

        core.use(None, 'fludef_clear_components', c_void_p)

        def clear_components(self):
            """
            清除所有的组分
            """
            core.fludef_clear_components(self.handle)

        core.use(c_size_t, 'fludef_add_component', c_void_p, c_void_p)

        def add_component(self, flu, name=None):
            """
            添加流体组分，并返回组分的ID
            """
            assert isinstance(flu, Seepage.FluDef)
            idx = core.fludef_add_component(self.handle, flu.handle)
            if name is not None:
                self.get_component(idx).name = name
            return idx

        @staticmethod
        def create(defs, name=None):
            """
            将存储在list中的多个流体的定义，组合成为一个具有多个组分的单个流体定义.
            当给定name的时候，则返回的数据使用此name.
            注意：
                此函数将返回给定数据的拷贝，因此，原始的数据并不会被引用和修改.
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
            流体组分的名称.
            """
            return core.fludef_get_name(self.handle).decode()

        @name.setter
        def name(self, value):
            """
            流体组分的名称.
            """
            core.fludef_set_name(self.handle, make_c_char_p(value))

        core.use(None, 'fludef_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            克隆数据
            """
            assert isinstance(other, Seepage.FluDef)
            core.fludef_clone(self.handle, other.handle)

        def get_copy(self, name=None):
            """
            返回当前数据的一个拷贝(当给定name的时候，则修改返回数据的name)
            """
            data = Seepage.FluDef()
            data.clone(self)
            if name is not None:
                data.name = name
            return data

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
            创建给定handle的引用，或者创建流体数据.
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
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.fluid_save(self.handle, make_c_char_p(path))

        core.use(None, 'fluid_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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
            假设：
                在计算的过程中，流体的密度不会发生剧烈的变化，因此，在一次迭代的过程中，流体的密度可以
                视为不变的。在一次迭代之后，可以根据最新的温度和压力来更新流体的密度。
            注意：
                在利用TherFlowConfig来iterate的时候，如果模型中存储了流体的定义，那么流体密度的
                更新会被自动调用，从而保证流体的密度总是最新的。
            """
            return core.fluid_get_den(self.handle)

        @den.setter
        def den(self, value):
            assert value > 0
            core.fluid_set_den(self.handle, value)

        core.use(c_double, 'fluid_get_vis', c_void_p)
        core.use(None, 'fluid_set_vis', c_void_p, c_double)

        @property
        def vis(self):
            """
            流体粘性系数. Pa.s
                注意: 除非外部修改，否则vis维持不变
            流体粘性的更新规则和密度相似。
            """
            return core.fluid_get_vis(self.handle)

        @vis.setter
        def vis(self, value):
            assert value > 0
            core.fluid_set_vis(self.handle, value)

        @property
        def is_solid(self):
            """
            该流体单元在计算内核中是否可以被视为固体.
            注意：
                该属性将被弃用
            """
            warnings.warn('FluData.is_solid will be deleted after 2024-5-5', DeprecationWarning)
            return self.vis >= 0.5e30

        core.use(c_double, 'fluid_get_attr', c_void_p, c_size_t)
        core.use(None, 'fluid_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            第index个流体自定义属性。当两个流体数据相加时，自定义属性将根据质量进行加权平均。
            """
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
            参考get_attr函数
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.fluid_set_attr(self.handle, index, value)
            return self

        core.use(None, 'fluid_clone', c_void_p, c_void_p)

        def clone(self, other):
            """
            拷贝所有的数据
            """
            assert isinstance(other, Seepage.FluData)
            core.fluid_clone(self.handle, other.handle)

        def get_copy(self):
            data = Seepage.FluData()
            data.clone(self)
            return data

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
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.seepage_cell_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_cell_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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
            """
            在三维空间中的x坐标
            """
            return core.seepage_cell_get_pos(self.handle, 0)

        @x.setter
        def x(self, value):
            core.seepage_cell_set_pos(self.handle, 0, value)

        @property
        def y(self):
            """
            在三维空间中的y坐标
            """
            return core.seepage_cell_get_pos(self.handle, 1)

        @y.setter
        def y(self, value):
            core.seepage_cell_set_pos(self.handle, 1, value)

        @property
        def z(self):
            """
            在三维空间中的z坐标
            """
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
            assert len(value) == 3
            for dim in range(3):
                core.seepage_cell_set_pos(self.handle, dim, value[dim])

        def distance(self, other):
            """
            返回距离另外一个Cell或者另外一个位置的距离
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
            """
            return core.seepage_cell_get_v0(self.handle)

        @v0.setter
        def v0(self, value):
            assert value >= 1.0e-10, f'value = {value}'
            core.seepage_cell_set_v0(self.handle, value)

        core.use(c_double, 'seepage_cell_get_k', c_void_p)
        core.use(None, 'seepage_cell_set_k', c_void_p, c_double)

        @property
        def k(self):
            """
            流体压力增加1Pa的时候，孔隙体积的增加量(m^3). k的数值越小，则刚度越大.
            """
            return core.seepage_cell_get_k(self.handle)

        @k.setter
        def k(self, value):
            core.seepage_cell_set_k(self.handle, value)

        def set_pore(self, p, v, dp, dv):
            """
            Create a pore so that when the internal pressure is equal to p, the volume is v;
            if the pressure changes dp, the volume changes to dv
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
            给定内部流体的体积，根据孔隙刚度计算孔隙内流体的压力.
            """
            return (v - self.v0) / self.k

        def p2v(self, p):
            """
            给定内部流体的压力，根据孔隙刚度计算内部流体的体积
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
            assert 0 <= value < 10
            core.seepage_cell_set_fluid_n(self.handle, value)

        def get_fluid(self, *args):
            """
            返回给定序号的流体.(当参数数量为1的时候，返回Seepage.Fluid对象; 当参数数量大于1的时候，返回Seepage.FluData对象)
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
            All fluids in the cell
            """
            return Iterator(self, self.fluid_number, lambda m, ind: m.get_fluid(ind))

        def get_component(self, indexes):
            """
            返回给定序号的组分.
            """
            if is_array(indexes):
                return self.get_fluid(*indexes)
            else:
                return self.get_fluid(indexes)

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
            """
            return core.seepage_cell_get_attr_n(self.handle)

        def get_attr(self, index, default_val=None, **valid_range):
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
            if _attr_in_range(value, **valid_range):
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
            """
            从other克隆数据（所有的数据）
            """
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
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.seepage_get_cell_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            与该Cell连接的第index个Face。当index个Face不存在时，返回None
            注：改Face的另一侧，即为get_cell返回的Cell
            """
            index = get_index(index, self.face_number)
            if index is not None:
                face_id = core.seepage_get_cell_face_id(self.model.handle, self.index, index)
                return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            此Cell周围的所有Cell
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            此Cell周围的所有Face
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

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
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.seepage_face_save(self.handle, make_c_char_p(path))

        core.use(None, 'seepage_face_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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

        def get_attr(self, index, default_val=None, **valid_range):
            """
            该Face的第 attr_id个自定义属性值。当不存在时，默认为一个无穷大的值(大于1.0e100)
            """
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
            index = get_index(index, self.cell_number)
            if index is not None:
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

        def get_another(self, cell):
            """
            返回另外一侧的Cell
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
            super(Seepage.Injector, self).__init__(handle, core.new_injector, core.del_injector)
            if handle is None:
                if path is not None:
                    self.load(path)

        core.use(None, 'injector_save', c_void_p, c_char_p)

        def save(self, path):
            """
            Serialized save. Optional extension:
            1:.txt
                .TXT format
                (cross-platform, basically unreadable)
            2:.xml
                .XML format
                (specific readability, largest volume, slowest read and write, cross-platform)
            3:. Other
                binary formats
                (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
            """
            if path is not None:
                core.injector_save(self.handle, make_c_char_p(path))

        core.use(None, 'injector_load', c_void_p, c_char_p)

        def load(self, path):
            """
            Read the serialization archive.
            To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
            """
            if path is not None:
                _check_ipath(path, self)
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
            即将注入到Cell中的流体的数据. 这里返回的是一个引用 (从而可以直接修改内部的数据)
            """
            return Seepage.FluData(handle=core.injector_get_flu(self.handle))

        core.use(None, 'injector_set_fid', c_void_p, c_size_t, c_size_t, c_size_t)

        def set_fid(self, fluid_id):
            """
            设置注入的流体的ID. 注意：如果需要注热的是热量，则将fluid_id设置为None.
            """
            core.injector_set_fid(self.handle, *parse_fid3(fluid_id))

        core.use(c_size_t, 'injector_get_fid_length', c_void_p)
        core.use(c_size_t, 'injector_get_fid_of', c_void_p, c_size_t)

        def get_fid(self):
            """
            返回注入流体的ID
            """
            count = core.injector_get_fid_length(self.handle)
            return [core.injector_get_fid_of(self.handle, idx) for idx in range(count)]

        @property
        def fid(self):
            """
            注入的流体的ID. 注意：如果需要注热的是热量，则将fluid_id设置为None.
            """
            return self.get_fid()

        @fid.setter
        def fid(self, value):
            """
            注入的流体的ID. 注意：如果需要注热的是热量，则将fluid_id设置为None.
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
            """
            return core.injector_get_value(self.handle)

        @value.setter
        def value(self, val):
            """
            设置注入的数值。
            """
            core.injector_set_value(self.handle, val)

        @property
        def time(self):
            warnings.warn('Property Seepage.Injector.time has been removed',
                          DeprecationWarning)
            return 0

        @time.setter
        def time(self, value):
            warnings.warn('Property Seepage.Injector.time has been removed',
                          DeprecationWarning)

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
            """
            热边界和cell之间换热的系数 (当大于0的时候，则实施固定温度的加热,否则为固定功率的加热);
            """
            return core.injector_get_g_heat(self.handle)

        @g_heat.setter
        def g_heat(self, value):
            core.injector_set_g_heat(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_mc', c_void_p)
        core.use(None, 'injector_set_ca_mc', c_void_p, c_size_t)

        @property
        def ca_mc(self):
            """
            cell的mc属性的ID
            """
            return core.injector_get_ca_mc(self.handle)

        @ca_mc.setter
        def ca_mc(self, value):
            """
            cell的mc属性的ID
            """
            core.injector_set_ca_mc(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_t', c_void_p)
        core.use(None, 'injector_set_ca_t', c_void_p, c_size_t)

        @property
        def ca_t(self):
            """
            cell的温度属性的id
            """
            return core.injector_get_ca_t(self.handle)

        @ca_t.setter
        def ca_t(self, value):
            """
            cell的温度属性的id
            """
            core.injector_set_ca_t(self.handle, value)

        core.use(c_size_t, 'injector_get_ca_no_inj', c_void_p)
        core.use(None, 'injector_set_ca_no_inj', c_void_p, c_size_t)

        @property
        def ca_no_inj(self):
            """
            在根据位置来寻找注入的cell的时候，凡是设置了ca_no_inj的cell，将会被忽略（从而避免被Injector操作）
            """
            return core.injector_get_ca_no_inj(self.handle)

        @ca_no_inj.setter
        def ca_no_inj(self, value):
            core.injector_set_ca_no_inj(self.handle, value)

        core.use(None, 'injector_add_oper', c_void_p, c_double, c_char_p)

        def add_oper(self, time, oper):
            """
            添加在time时刻的一个操作. 注意，oper支持如下关键词
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
            其它关键词将会被忽略(不抛出异常).
            """
            core.injector_add_oper(self.handle, time, make_c_char_p(oper if isinstance(oper, str) else f'{oper}'))
            return self

        core.use(None, 'injector_work', c_void_p, c_void_p, c_double, c_double)

        def work(self, model, *, time=None, dt=None):
            """
            执行注入操作。会同步更新injector内部存储的time属性；
            注：此函数不需要调用。内置在Seepage中的Injector，会在Seepage.iterate函数中被自动调用
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
            对于此渗流模型，当定义了热传导相关的参数之后，可以作为一个热传导模型来使用。具体和Thermal模型类似。其中：
            ca_t:   Cell的温度属性的ID；
            ca_mc:  Cell范围内质量和比热的乘积；
            fa_g:   Face导热的通量g; 单位时间内通过Face的热量dH=g*dT；
            dt：    时间步长;
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
        return f"zml.Seepage(handle={self.handle}, cell_n={cell_n}, face_n={face_n}, note='{self.get_note()}')"

    core.use(None, 'seepage_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.seepage_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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

    core.use(c_char_p, 'seepage_get_text', c_void_p, c_char_p)
    core.use(None, 'seepage_set_text', c_void_p, c_char_p, c_char_p)

    def get_text(self, key):
        """
        返回模型内部存储的文本数据
        """
        return core.seepage_get_text(self.handle, make_c_char_p(key)).decode()

    def set_text(self, key, text):
        """
        设置模型中存储的文本数据
        """
        if not isinstance(text, str):
            text = f'{text}'
        core.seepage_set_text(self.handle, make_c_char_p(key), make_c_char_p(text))

    def add_note(self, text):
        self.set_text('note', self.get_text('note') + text)

    def get_note(self):
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
        """
        core.seepage_remove_cell(self.handle, cell_id)

    core.use(None, 'seepage_remove_face', c_void_p, c_size_t)

    def remove_face(self, face_id):
        """
        移除给定id的face
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变
        """
        core.seepage_remove_face(self.handle, face_id)

    core.use(None, 'seepage_remove_faces_of_cell', c_void_p, c_size_t)

    def remove_faces_of_cell(self, cell_id):
        """
        移除给定id的cell的所有的face，使其成为一个孤立的cell
        注意：
            这是一个复杂的操作，会涉及到很多连接关系，以及Cell和Face的顺序的改变
        """
        core.seepage_remove_faces_of_cell(self.handle, cell_id)

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
    core.use(None, 'seepage_set_inj_n', c_void_p, c_size_t)

    @property
    def injector_number(self):
        """
        Injector的数量
        """
        return core.seepage_get_inj_n(self.handle)

    @injector_number.setter
    def injector_number(self, count):
        """
        设置注入点的数量. 注意，对于新的injector，所有的参数都将使用默认值，后续必须进行配置.
            请谨慎使用此接口来添加注入点.
            重设injector_number主要用来清空已有的注入点.
        """
        core.seepage_set_inj_n(self.handle, count)

    def get_cell(self, index):
        """
        返回第index个Cell对象
        """
        index = get_index(index, self.cell_number)
        if index is not None:
            return Seepage.Cell(self, index)

    def get_face(self, index):
        """
        返回第index个Face对象
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Seepage.Face(self, index)

    core.use(c_void_p, 'seepage_get_inj', c_void_p, c_size_t)

    def get_injector(self, index):
        index = get_index(index, self.injector_number)
        if index is not None:
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

        if flu is not None:
            assert isinstance(flu, Seepage.FluData)
            inj.flu.clone(flu)

        if pos is not None:   # 给定注入的位置，后续，则自动去查找附近的cell
            inj.pos = pos

        if radi is not None:  # 查找的半径
            inj.radi = radi

        if ca_mc is not None:  # Cell的属性
            inj.ca_mc = ca_mc

        if ca_t is not None:  # Cell的属性(温度属性，在注入热量的时候会被修改)
            inj.ca_t = ca_t

        if g_heat is not None:   # 恒定温度加热的时候需要给定
            inj.g_heat = g_heat

        if opers is not None:   # 对属性的操作定时器
            for item in opers:
                inj.add_oper(*item)

        if value is not None:   # 当前的值
            inj.value = value

        return inj

    @property
    def cells(self):
        """
        模型中所有的Cell
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        模型中所有的Face
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def injectors(self):
        """
        模型中所有的Injector
        """
        return Iterator(self, self.injector_number, lambda m, ind: m.get_injector(ind))

    core.use(None, 'seepage_apply_injs', c_void_p, c_double,
             c_double)

    def apply_injectors(self, *, time=None, dt=None):
        """
        所有的注入点执行注入操作.
        """
        if time is None:
            warnings.warn('time is None for Seepage.Injector, use time=0 as default')
            time = 0
        if dt is None:
            return
        core.seepage_apply_injs(self.handle, time, dt)

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
        """
        返回model中gr的数量
        """
        return core.seepage_get_gr_n(self.handle)

    core.use(c_void_p, 'seepage_get_gr', c_void_p, c_size_t)

    def get_gr(self, idx):
        """
        返回序号为idx的gr
        """
        idx = get_index(idx, self.gr_number)
        if idx is not None:
            return Interp1(handle=core.seepage_get_gr(self.handle, idx))

    @property
    def grs(self):
        """
        迭代所有的gr
        """
        return Iterator(model=self, count=self.gr_number, get=lambda m, ind: m.get_gr(ind))

    core.use(c_size_t, 'seepage_add_gr', c_void_p, c_void_p)

    def add_gr(self, gr, need_id=False):
        """
        添加一个gr. 其中gr应该为Interp1类型.
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
        """
        if isinstance(value, Interp1):
            self.set_kr(kr=value)
            return
        else:
            x = value[0]
            y = value[1]
            self.set_kr(saturation=x, kr=y)
            return

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

    def get_attr(self, index, default_val=None, **valid_range):
        """
        模型的第index个自定义属性
        """
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
            fluid_id为需要更新的流体的ID (当None的时候，则更新所有)
            kernel为Interp2(p,T)
            relax_factor为松弛因子，限定密度的最大变化幅度.

        注意:
            当 relax_factor <= 0的时候，内核不会执行任何更新  (since 2023-9-27)
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
        """
        if dt is None:
            return
        if thermal_model is None:   # 在模型的内部交换热量（流体和固体交换）
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

    core.use(c_size_t, 'seepage_get_nearest_cell_id',
             c_void_p, c_double, c_double, c_double, c_size_t, c_size_t)

    def get_nearest_cell(self, pos, i_beg=None, i_end=None):
        """
        返回与给定位置距离最近的cell (在[i_beg, i_end)的范围内搜索)
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
        """
        assert isinstance(other, Seepage)
        core.seepage_clone(self.handle, other.handle)

    def get_copy(self):
        """
        返回一个拷贝.
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
        """
        if count <= 0:
            return
        assert isinstance(other, Seepage)
        core.seepage_clone_inner_faces(self.handle, other.handle, ibeg0, ibeg1, count)

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

    core.use(None, 'seepage_update_cond', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def update_cond(self, ca_v0, fa_g0, fa_igr, relax_factor=1.0):
        """
        给定初始时刻各Cell流体体积v0，各Face的导流g0，v/v0到g/g0的映射gr，来更新此刻Face的g.
        ca_v0是cell的属性id，fa_g0是face的属性id的时候，fa_igr是face的属性id
            (用以表示此face选用的gr的序号。注意此时必须提前将gr存储到model中).
        """
        core.seepage_update_cond(self.handle, ca_v0, fa_g0, fa_igr, relax_factor)

    core.use(None, 'seepage_update_g0', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def update_g0(self, fa_g0, fa_k, fa_s, fa_l):
        """
        对于所有的face，根据它的渗透率，面积和长度来计算cond (流体饱和的时候的cond).
            ---
            此函数非必须，可以基于numpy在Python层面实现同样的功能，后续可能会移除.
        """
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
             c_void_p, c_size_t, c_double, c_void_p)

    def get_linear_dpre(self, fid0, fid1, s2p=None, ca_ipc=99999999, vs0=None, vk=None, ds=0.05, cell_ids=None):
        """
        更新两种流体之间压力差和饱和度之间的线性关系
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
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.seepage_get_vol_fraction(self.handle, buffer.handle, *parse_fid3(fid))
        return buffer

    core.use(None, 'seepage_get_face_gradient', c_void_p, c_void_p, c_void_p)

    def get_face_gradient(self, fa, ca):
        """
        根据cell中心位置的属性的值来计算各个face位置的梯度.
            (c1 - c0) / dist
        其中:
            fa为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_face_gradient来替代此函数
        """
        core.seepage_get_face_gradient(self.handle, ctypes.cast(fa, c_void_p), ctypes.cast(ca, c_void_p))

    core.use(None, 'seepage_get_face_diff', c_void_p, c_void_p, c_void_p)

    def get_face_diff(self, fa, ca):
        """
        计算face两侧的cell的属性的值的差异。
            c1 - c0
        其中:
            fa为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_face_diff来替代此函数
        """
        core.seepage_get_face_diff(self.handle, ctypes.cast(fa, c_void_p), ctypes.cast(ca, c_void_p))

    core.use(None, 'seepage_get_face_sum', c_void_p, c_void_p, c_void_p)

    def get_face_sum(self, fa, ca):
        """
        计算face两侧的cell的属性的值的和。
            c1 + c0
        其中:
            fa为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_face_sum来替代此函数
        """
        core.seepage_get_face_sum(self.handle, ctypes.cast(fa, c_void_p), ctypes.cast(ca, c_void_p))

    core.use(None, 'seepage_get_face_left', c_void_p, c_void_p, c_void_p)

    def get_face_left(self, fa, ca):
        """
        计算face左侧的cell属性
        其中:
            fa为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_face_left来替代此函数
        """
        core.seepage_get_face_left(self.handle, ctypes.cast(fa, c_void_p), ctypes.cast(ca, c_void_p))

    core.use(None, 'seepage_get_face_right', c_void_p, c_void_p, c_void_p)

    def get_face_right(self, fa, ca):
        """
        计算face右侧的cell属性
        其中:
            fa为face的属性(指针，用于输出)
            ca为各个cell的属性(指针，用于输入)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_face_right来替代此函数
        """
        core.seepage_get_face_right(self.handle, ctypes.cast(fa, c_void_p), ctypes.cast(ca, c_void_p))

    core.use(None, 'seepage_get_cell_average', c_void_p, c_void_p, c_void_p)

    def get_cell_average(self, ca, fa):
        """
        计算cell周围face的平均值
        其中:
            ca为各个cell的属性(指针，用于输出)
            fa为face的属性(指针，用于输如)
        建议：
            这里的参数都是指针。建议使用zmlx.config.seepage.get_cell_average来替代此函数
        """
        core.seepage_get_cell_average(self.handle, ctypes.cast(ca, c_void_p), ctypes.cast(fa, c_void_p))

    def get_face_average(self, *args, **kwargs):
        warnings.warn('This function will be removed after 2025-4-6, use get_cell_average instead',
                      DeprecationWarning)
        return self.get_cell_average(*args, **kwargs)

    core.use(None, 'seepage_heating', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def heating(self, ca_mc, ca_t, ca_p, dt):
        """
        按照各个Cell给定的功率来对各个Cell进行加热 (此功能非必须，可以借助numpy实现).
        其中：
            ca_p：定义Cell加热的功率.
        """
        core.seepage_heating(self.handle, ca_mc, ca_t, ca_p, dt)

    core.use(c_size_t, 'seepage_get_fludef_n', c_void_p)

    @property
    def fludef_number(self):
        """
        模型内存储的流体定义的数量
        """
        return core.seepage_get_fludef_n(self.handle)

    core.use(c_bool, 'seepage_find_fludef', c_void_p, c_char_p, c_void_p)

    def find_fludef(self, name, buffer=None):
        """
        查找给定name的流体定义的ID
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
        """
        self.clear_fludefs()
        for item in args:
            self.add_fludef(item)

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
        """
        清除所有的毛管压力曲线
        """
        core.seepage_clear_pcs(self.handle)

    core.use(c_size_t, 'seepage_get_reaction_n', c_void_p)

    @property
    def reactions(self):
        """
        迭代所有的反应
        """
        return Iterator(model=self, count=self.reaction_number, get=lambda m, ind: m.get_reaction(ind))

    @property
    def reaction_number(self):
        return core.seepage_get_reaction_n(self.handle)

    core.use(c_void_p, 'seepage_get_reaction', c_void_p, c_size_t)

    def get_reaction(self, idx):
        idx = get_index(idx, self.reaction_number)
        if idx is not None:
            return Seepage.Reaction(handle=core.seepage_get_reaction(self.handle, idx))

    core.use(c_size_t, 'seepage_add_reaction', c_void_p, c_void_p)

    def add_reaction(self, data, need_id=False):
        """
        添加一个反应
        """
        if not isinstance(data, Seepage.Reaction):
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
        """
        core.seepage_clear_reactions(self.handle)

    def create_reaction(self, **kwargs):
        """
        根据给定的参数，创建一个反应（可能需要读取model中的流体定义，以及会在model中注册属性）
        """
        data = Seepage.Reaction()

        temp = kwargs.get('temp', None)
        if temp is not None:
            data.temp = temp

        heat = kwargs.get('heat', None)
        if heat is not None:
            data.heat = heat

        p2t = kwargs.get('p2t', None)
        if p2t is not None:
            p, t = p2t
            data.set_p2t(p, t)

        t2q = kwargs.get('t2q', None)
        if t2q is not None:
            t, q = t2q
            data.set_t2q(t, q)

        components = kwargs.get('components', None)
        if components is not None:
            for comp in components:
                kind = comp.get('kind')
                if isinstance(kind, str):
                    kind = self.find_fludef(kind)

                weight = comp.get('weight')
                assert -1 <= weight <= 1

                fa_t = comp.get('fa_t', None)
                assert fa_t is not None
                if isinstance(fa_t, str):
                    fa_t = self.reg_flu_key(fa_t)

                fa_c = comp.get('fa_c', None)
                assert fa_c is not None
                if isinstance(fa_c, str):
                    fa_c = self.reg_flu_key(fa_c)

                data.add_component(index=kind, weight=weight, fa_t=fa_t, fa_c=fa_c)

        inhibitors = kwargs.get('inhibitors', None)
        if inhibitors is not None:
            for inh in inhibitors:
                # 这里要注意的是，这里的浓度指的是质量浓度.
                sol = inh.get('sol')
                if isinstance(sol, str):
                    sol = self.find_fludef(sol)

                liq = inh.get('liq')
                if isinstance(liq, str):
                    liq = self.find_fludef(liq)

                data.add_inhibitor(sol=sol, liq=liq, c=inh.get('c'), t=inh.get('t'))

        idt = kwargs.get('idt', None)
        if idt is not None:
            if isinstance(idt, str):
                idt = self.reg_cell_key(idt)
            data.idt = idt

        wdt = kwargs.get('wdt', None)
        if wdt is not None:
            data.wdt = wdt

        irate = kwargs.get('irate', None)
        if irate is not None:
            if isinstance(irate, str):
                irate = self.reg_cell_key(irate)
            data.irate = irate

        return data

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
            index=-3, distance between two cells

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
        warnings.warn('Seepage.numpy will be removed after 2025-1-21. Use zmlx.utility.SeepageNumpy Instead. '
                      , DeprecationWarning)
        from zmlx.utility.SeepageNumpy import SeepageNumpy
        return SeepageNumpy(model=self)

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
        return self

    core.use(c_bool, 'seepage_has_tag', c_void_p, c_char_p)

    def has_tag(self, tag):
        """
        返回模型是否包含给定的这个标签
        """
        return core.seepage_has_tag(self.handle, make_c_char_p(tag))

    def not_has_tag(self, tag):
        return not self.has_tag(tag)

    core.use(None, 'seepage_add_tag', c_void_p, c_char_p)

    def add_tag(self, tag, *tags):
        """
        在模型中添加给定的标签.
            支持添加多个(since 2024-2-23)
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
        """
        core.seepage_del_tag(self.handle, make_c_char_p(tag))
        if len(tags) > 0:
            for tag in tags:
                self.del_tag(tag=tag)
        return self

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
        val = core.seepage_get_key(self.handle, make_c_char_p(key))
        if val < 9999:
            return val

    core.use(None, 'seepage_set_key', c_void_p, c_char_p, c_int64)

    def set_key(self, key, value):
        """
        设置键值. 会直接覆盖现有的键值
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
        """
        core.seepage_del_key(self.handle, make_c_char_p(key))
        if len(keys) > 0:
            for key in keys:
                self.del_key(key=key)
        return self

    core.use(None, 'seepage_clear_keys', c_void_p)

    def clear_keys(self):
        core.seepage_clear_keys(self.handle)
        return self

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

    def get_model_key(self, key):
        """
        返回用于model的键值
        """
        return self.get_key('m_' + key)

    def get_cell_key(self, key):
        """
        返回用于cell的键值
        """
        return self.get_key('n_' + key)

    def get_face_key(self, key):
        """
        返回用于face的键值
        """
        return self.get_key('b_' + key)

    def get_flu_key(self, key):
        """
        返回用于flu的键值
        """
        return self.get_key('f_' + key)

    core.use(None, 'seepage_get_keys', c_void_p, c_void_p)

    def get_keys(self):
        """
        返回所有的keys（作为dict）
        """
        s = String()
        core.seepage_get_keys(self.handle, s.handle)
        return eval(s.to_str())

    def set_keys(self, **kwargs):
        """
        设置keys. 会覆盖现有的键值.
        """
        for key, value in kwargs.items():
            self.set_key(key, value)
        return self

    core.use(None, 'seepage_get_tags', c_void_p, c_void_p)

    def get_tags(self):
        """
        返回所有的tags（作为set）
        """
        s = String()
        core.seepage_get_tags(self.handle, s.handle)
        return eval(s.to_str())

    core.use(None, 'seepage_pop_cells', c_void_p, c_size_t)

    def pop_cells(self, count=1):
        """
        删除最后count个Cell的所有的Face，然后移除最后count个Cell
        """
        core.seepage_pop_cells(self.handle, count)
        return self

    core.use(None, 'seepage_group_cells', c_void_p, c_void_p)

    def get_cell_groups(self):
        """
        对所有的cell进行分区，使得对于任意一个cell，都不会和与它相关的cell分在一组 (用于并行)
        """
        g = Groups()
        core.seepage_group_cells(self.handle, g.handle)
        return g

    core.use(None, 'seepage_group_faces', c_void_p, c_void_p)

    def get_face_groups(self):
        g = Groups()
        core.seepage_group_faces(self.handle, g.handle)
        return g

    core.use(None, 'seepage_update_sand', c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_void_p, c_double, c_void_p)

    def update_sand(self, sol_sand, flu_sand, dt, v2q, vel=None):
        """
        计算流动的砂和沉降的砂之间的平衡. 其中vel为一个double类型的指针，存储在各个cell中当前的流动速度
        """
        assert isinstance(v2q, Interp1)
        if vel is None:
            vel = 0   # Data is None
        if isinstance(vel, Vector):
            vel = vel.pointer

        if isinstance(sol_sand, str):
            sol_sand = self.find_fludef(name=sol_sand)
            assert sol_sand is not None

        if isinstance(flu_sand, str):
            flu_sand = self.find_fludef(name=flu_sand)
            assert flu_sand is not None

        # 它一定要在某一种流体内
        assert len(flu_sand) >= 2

        core.seepage_update_sand(self.handle, *parse_fid3(sol_sand),
                                 *parse_fid3(flu_sand), vel, dt, v2q.handle)

    core.use(None, 'seepage_get_cell_flu_vel', c_void_p, c_void_p,
             c_size_t, c_double)

    def get_cell_flu_vel(self, fid, last_dt, buf=None):
        """
        根据上一个时间步各个face内流过的流体的体积，来计算各个cell位置流体流动的速度.
        返回：
            一个Vector对象(优先使用buf)
        """
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
            index = get_index(index, self.cell_number)
            if index is not None:
                cell_id = core.thermal_get_cell_cell_id(self.model.handle, self.index, index)
                return self.model.get_cell(cell_id)

        def get_face(self, index):
            """
            连接的第index个Face
            """
            index = get_index(index, self.face_number)
            if index is not None:
                face_id = core.thermal_get_cell_face_id(self.model.handle, self.index, index)
                return self.model.get_face(face_id)

        @property
        def cells(self):
            """
            所有相邻的Cell
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self):
            """
            所有相邻的Face
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

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
            index = get_index(index, self.cell_number)
            if index is not None:
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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.thermal_save(self.handle, make_c_char_p(path))

    core.use(None, 'thermal_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
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
        index = get_index(index, self.cell_number)
        if index is not None:
            return Thermal.Cell(self, index)

    def get_face(self, index):
        """
        模型中第index个Face
        """
        index = get_index(index, self.face_number)
        if index is not None:
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
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self):
        """
        返回所有的Face
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

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


class TherFlowAdaptor:
    def __getattr__(self, item):
        warnings.warn('please use <zmlx.config.TherFlowConfig> instead of <zml.TherFlowConfig>',
                      DeprecationWarning)
        from zmlx.config.TherFlowConfig import TherFlowConfig as Config
        return getattr(Config, item)

    def __call__(self, *args, **kwargs):
        warnings.warn('please use <zmlx.config.TherFlowConfig> instead of <zml.TherFlowConfig>',
                      DeprecationWarning)
        from zmlx.config.TherFlowConfig import TherFlowConfig as Config
        return Config(*args, **kwargs)


TherFlowConfig = TherFlowAdaptor()
SeepageTher = TherFlowAdaptor()


class ConjugateGradientSolver(HasHandle):
    """
    The wrapper of the ConjugateGradientSolver from Eigen
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

    core.use(c_double, 'cg_sol_get_tolerance', c_void_p)

    def get_tolerance(self):
        """
        the tolerance of the solver
        """
        return core.cg_sol_get_tolerance(self.handle)


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

        @property
        def phase(self):
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

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

        @property
        def cid(self):
            return self.get_cid()

        @cid.setter
        def cid(self, value):
            self.set_cid(value)

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

        @property
        def radi(self):
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

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
            assert len(value) >= 3
            for i in range(3):
                core.ip_node_set_pos(self.handle, i, value[i])

        @property
        def pos(self):
            return self.get_pos()

        @pos.setter
        def pos(self, value):
            self.set_pos(value)

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
            idx = get_index(idx, self.node_n)
            if idx is not None:
                i_node = core.ip_get_node_node_id(self.model.handle, self.index, idx)
                return self.model.get_node(i_node)

        core.use(c_size_t, 'ip_get_node_bond_id', c_void_p, c_size_t, c_size_t)

        def get_bond(self, idx):
            """
            此Node连接的第idx个Bond
            """
            idx = get_index(idx, self.bond_n)
            if idx is not None:
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

        @property
        def radi(self):
            return self.get_radi()

        @radi.setter
        def radi(self, value):
            self.set_radi(value)

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

        @property
        def dp0(self):
            return self.get_dp0()

        @dp0.setter
        def dp0(self, value):
            self.set_dp0(value)

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

        @property
        def dp1(self):
            return self.get_dp1()

        @dp1.setter
        def dp1(self, value):
            self.set_dp1(value)

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
            idx = get_index(idx, self.node_n)
            if idx is not None:
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

        @property
        def node_id(self):
            return self.get_node_id()

        @node_id.setter
        def node_id(self, value):
            self.set_node_id(value)

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

        @property
        def phase(self):
            return self.get_phase()

        @phase.setter
        def phase(self, value):
            self.set_phase(value)

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

        @property
        def qinj(self):
            return self.get_qinj()

        @qinj.setter
        def qinj(self, value):
            self.set_qinj(value)

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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        assert isinstance(path, str)
        core.ip_save(self.handle, make_c_char_p(path))

    core.use(None, 'ip_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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

    @property
    def time(self):
        return self.get_time()

    @time.setter
    def time(self, value):
        self.set_time(value)

    core.use(c_size_t, 'ip_add_node', c_void_p)

    def add_node(self):
        """
        添加一个Node，并返回新添加的Node对象
        """
        index = core.ip_add_node(self.handle)
        return self.get_node(index)

    def get_node(self, index):
        """
        返回序号为index的Node对象
        """
        index = get_index(index, self.node_n)
        if index is not None:
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
        return self.get_bond(index)

    def get_bond(self, index):
        """
        返回给定序号的Bond
        """
        index = get_index(index, self.bond_n)
        if index is not None:
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
        return self.get_bond(index)

    core.use(c_size_t, 'ip_get_node_n', c_void_p)

    def get_node_n(self):
        return core.ip_get_node_n(self.handle)

    @property
    def node_n(self):
        return self.get_node_n()

    core.use(c_size_t, 'ip_get_bond_n', c_void_p)

    def get_bond_n(self):
        return core.ip_get_bond_n(self.handle)

    @property
    def bond_n(self):
        return self.get_bond_n()

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

    @property
    def outlet_n(self):
        return self.get_outlet_n()

    @outlet_n.setter
    def outlet_n(self, value):
        self.set_outlet_n(value)

    core.use(None, 'ip_set_outlet', c_void_p, c_size_t, c_size_t)

    def set_outlet(self, index, value):
        """
        第index个出口对应的Node的序号
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
            value = get_index(value, self.node_n)
            if value is not None:
                core.ip_set_outlet(self.handle, index, value)

    core.use(c_size_t, 'ip_get_outlet', c_void_p, c_size_t)

    def get_outlet(self, index):
        """
        第index个出口对应的Node的序号
        """
        index = get_index(index, self.outlet_n)
        if index is not None:
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

    @property
    def gravity(self):
        return self.get_gravity()

    @gravity.setter
    def gravity(self, value):
        self.set_gravity(value)

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

    @property
    def inj_n(self):
        return self.get_inj_n()

    @inj_n.setter
    def inj_n(self, value):
        self.set_inj_n(value)

    def get_inj(self, index):
        """
        返回第index个注入点
        """
        index = get_index(index, self.inj_n)
        if index is not None:
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

    @property
    def oper_n(self):
        return self.get_oper_n()

    def get_oper(self, idx):
        idx = get_index(idx, self.oper_n)
        if idx is not None:
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

    core.use(None, 'ip_write_pos', c_void_p, c_size_t, c_void_p)

    def write_pos(self, dim, pointer):
        core.ip_write_pos(self.handle, dim, ctypes.cast(pointer, c_void_p))

    core.use(None, 'ip_write_phase', c_void_p, c_void_p)

    def write_phase(self, pointer):
        core.ip_write_phase(self.handle, ctypes.cast(pointer, c_void_p))

    def nodes_write(self, *args, **kwargs):
        warnings.warn('remove after 2025-6-2', DeprecationWarning)
        from zmlx.alg.ip_nodes_write import ip_nodes_write
        return ip_nodes_write(self, *args, **kwargs)


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
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.dfn2d_save(self.handle, make_c_char_p(path))

    core.use(None, 'dfn2d_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
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
        idx = get_index(idx, self.fracture_n)
        if idx is not None:
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


class Lattice3(HasHandle):
    """
    用以临时存放数据序号的格子
    """
    core.use(c_void_p, 'new_lat3')
    core.use(None, 'del_lat3', c_void_p)

    def __init__(self, box=None, shape=None, handle=None):
        super(Lattice3, self).__init__(handle, core.new_lat3, core.del_lat3)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape)

    def __str__(self):
        return f'zml.Lattice3(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'lat3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.lat3_save(self.handle, make_c_char_p(path))

    core.use(None, 'lat3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.lat3_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'lat3_lrange', c_void_p, c_size_t)

    @property
    def box(self):
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似
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
        """
        return [core.lat3_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'lat3_size', c_void_p, c_size_t)

    @property
    def size(self):
        """
        返回三维维度上网格的数量<至少为1>
        """
        return [core.lat3_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'lat3_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'lat3_get_centers', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        返回格子的中心点
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

    core.use(None, 'lat3_create', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box, shape):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小.
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
        """
        assert len(pos) == 3, f'pos = {pos}'
        core.lat3_add_point(self.handle, *pos, index)


class DDMSolution2(HasHandle):
    """
    二维DDM的基本解
    """
    core.use(c_void_p, 'new_ddm_sol2')
    core.use(None, 'del_ddm_sol2', c_void_p)

    def __init__(self, handle=None):
        super(DDMSolution2, self).__init__(handle, core.new_ddm_sol2, core.del_ddm_sol2)

    def __str__(self):
        return (f'zml.DDMSolution2(handle={self.handle}, '
                f'alpha={self.alpha}, beta={self.beta}, '
                f'shear_modulus={self.shear_modulus / 1.0e9}GPa, '
                f'poisson_ratio={self.poisson_ratio}, '
                f'adjust_coeff={self.adjust_coeff})')

    core.use(None, 'ddm_sol2_save', c_void_p, c_char_p)
    core.use(None, 'ddm_sol2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.ddm_sol2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
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


class FractureNetwork(HasHandle):
    class VertexData(Object):
        def __init__(self, handle):
            self.handle = handle

        core.use(c_double, 'frac_nd_get_pos', c_void_p, c_size_t)

        @property
        def x(self):
            """
            x坐标
            """
            return core.frac_nd_get_pos(self.handle, 0)

        @property
        def y(self):
            """
            y坐标
            """
            return core.frac_nd_get_pos(self.handle, 1)

        @property
        def pos(self):
            """
            位置
            """
            return self.x, self.y

        core.use(c_double, 'frac_nd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_nd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            第index个自定义属性
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
            参考get_attr函数
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.frac_nd_set_attr(self.handle, index, value)
            return self

    class FractureData(HasHandle):

        core.use(c_void_p, 'new_frac_bd')
        core.use(None, 'del_frac_bd', c_void_p)

        def __init__(self, handle=None):
            super(FractureNetwork.FractureData, self).__init__(handle, core.new_frac_bd, core.del_frac_bd)

        core.use(c_double, 'frac_bd_get_attr', c_void_p, c_size_t)
        core.use(None, 'frac_bd_set_attr', c_void_p, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            第index个自定义属性
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
            参考get_attr函数
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
            return core.frac_bd_get_ds(self.handle)

        @ds.setter
        def ds(self, value):
            core.frac_bd_set_ds(self.handle, value)

        core.use(c_double, 'frac_bd_get_dn', c_void_p)
        core.use(None, 'frac_bd_set_dn', c_void_p, c_double)

        @property
        def dn(self):
            return core.frac_bd_get_dn(self.handle)

        @dn.setter
        def dn(self, value):
            core.frac_bd_set_dn(self.handle, value)

        core.use(c_double, 'frac_bd_get_h', c_void_p)
        core.use(None, 'frac_bd_set_h', c_void_p, c_double)

        @property
        def h(self):
            return core.frac_bd_get_h(self.handle)

        @h.setter
        def h(self, value):
            core.frac_bd_set_h(self.handle, value)

        core.use(c_double, 'frac_bd_get_fric', c_void_p)
        core.use(None, 'frac_bd_set_fric', c_void_p, c_double)

        @property
        def f(self):
            """
            摩擦系数
            """
            return core.frac_bd_get_fric(self.handle)

        @f.setter
        def f(self, value):
            """
            摩擦系数
            """
            core.frac_bd_set_fric(self.handle, value)

        core.use(c_double, 'frac_bd_get_p0', c_void_p)
        core.use(None, 'frac_bd_set_p0', c_void_p, c_double)

        @property
        def p0(self):
            """
            p = max(0, p0 + k * dn)
            """
            return core.frac_bd_get_p0(self.handle)

        @p0.setter
        def p0(self, value):
            """
            p = max(0, p0 + k * dn)
            """
            core.frac_bd_set_p0(self.handle, value)

        core.use(c_double, 'frac_bd_get_k', c_void_p)
        core.use(None, 'frac_bd_set_k', c_void_p, c_double)

        @property
        def k(self):
            """
            p = max(0, p0 + k * dn)
            """
            return core.frac_bd_get_k(self.handle)

        @k.setter
        def k(self, value):
            """
            p = max(0, p0 + k * dn)
            """
            core.frac_bd_set_k(self.handle, value)

        core.use(c_double, 'frac_bd_get_fp', c_void_p)

        @property
        def fp(self):
            """
            根据此时的dn, p0和k计算得到的fp
            """
            return core.frac_bd_get_fp(self.handle)

        @staticmethod
        def create(ds=None, dn=None, h=None, f=None, p0=None, k=None):
            """
            创建裂缝数据. Since 2024-2-19
            """
            data = FractureNetwork.FractureData()
            if ds is not None:
                data.ds = ds
            if dn is not None:
                data.dn = dn
            if h is not None:
                data.h = h
            if k is not None:
                data.k = k
            if p0 is not None:
                data.p0 = p0
            if f is not None:
                data.f = f
            return data

    class Vertex(VertexData):

        core.use(c_void_p, 'frac_nt_get_nd', c_void_p, c_size_t)

        def __init__(self, network, index):
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.vertex_number
            self.network = network
            self.index = index
            super(FractureNetwork.Vertex, self).__init__(
                handle=core.frac_nt_get_nd(network.handle, index))

        def __str__(self):
            return f'zml.FractureNetwork.Vertex(index={self.index}, pos=[{self.x}, {self.y}])'

        core.use(c_size_t, 'frac_nt_nd_get_bd_n', c_void_p, c_size_t)

        @property
        def fracture_number(self):
            return core.frac_nt_nd_get_bd_n(self.network.handle, self.index)

        core.use(c_size_t, 'frac_nt_nd_get_bd_i', c_void_p, c_size_t, c_size_t)

        def get_fracture(self, index):
            index = get_index(index, self.fracture_number)
            if index is not None:
                return self.network.get_fracture(
                    core.frac_nt_nd_get_bd_i(self.network.handle, self.index, index))

    class Fracture(FractureData):

        core.use(c_void_p, 'frac_nt_get_bd', c_void_p, c_size_t)

        def __init__(self, network, index):
            assert isinstance(network, FractureNetwork)
            assert isinstance(index, int)
            assert index < network.fracture_number
            super(FractureNetwork.Fracture, self).__init__(
                handle=core.frac_nt_get_bd(network.handle, index))
            self.network = network
            self.index = index

        def __str__(self):
            return f'zml.FractureNetwork.Fracture(index={self.index}, pos={self.pos}, ds={self.ds}, dn={self.dn})'

        @property
        def vertex_number(self):
            return 2

        core.use(c_size_t, 'frac_nt_bd_get_nd_i', c_void_p, c_size_t, c_size_t)

        def get_vertex(self, index):
            index = get_index(index, self.vertex_number)
            if index is not None:
                return self.network.get_vertex(
                    core.frac_nt_bd_get_nd_i(self.network.handle, self.index, index))

        @property
        def pos(self):
            """
            裂缝的位置。格式: x0, y0, x1, y1
            """
            p0 = self.get_vertex(0).pos
            p1 = self.get_vertex(1).pos
            return p0[0], p0[1], p1[0], p1[1]

        @property
        def center(self):
            """
            裂缝的中心点坐标
            """
            p0 = self.get_vertex(0).pos
            p1 = self.get_vertex(1).pos
            return (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2

        core.use(c_double, 'frac_nt_get_bd_angle', c_void_p, c_size_t)

        @property
        def angle(self):
            """
            裂缝的方向角度.
            """
            return core.frac_nt_get_bd_angle(self.network.handle, self.index)

    core.use(c_void_p, 'new_frac_nt')
    core.use(None, 'del_frac_nt', c_void_p)

    def __init__(self, path=None, handle=None):
        super(FractureNetwork, self).__init__(handle, core.new_frac_nt, core.del_frac_nt)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return (f'zml.FractureNetwork(handle={self.handle}, '
                f'vertex_n={self.vertex_number}, fracture_n={self.fracture_number})')

    core.use(None, 'frac_nt_save', c_void_p, c_char_p)

    def save(self, path):
        """
        Serialized save. Optional extension:
        1:.txt
            .TXT format
            (cross-platform, basically unreadable)
        2:.xml
            .XML format
            (specific readability, largest volume, slowest read and write, cross-platform)
        3:. Other
            binary formats
            (fastest and smallest, but files generated under Windows and Linux cannot be read from each other)
        """
        if path is not None:
            core.frac_nt_save(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_load', c_void_p, c_char_p)

    def load(self, path):
        """
        Read the serialization archive.
        To determine the file format (txt, xml, and binary) based on the extension, refer to the save function
        """
        if path is not None:
            _check_ipath(path, self)
            core.frac_nt_load(self.handle, make_c_char_p(path))

    core.use(None, 'frac_nt_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'frac_nt_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.frac_nt_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.frac_nt_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(c_size_t, 'frac_nt_get_nd_n', c_void_p)

    @property
    def vertex_number(self):
        return core.frac_nt_get_nd_n(self.handle)

    def get_vertex(self, index):
        index = get_index(index, self.vertex_number)
        if index is not None:
            return FractureNetwork.Vertex(self, index)

    core.use(c_size_t, 'frac_nt_get_bd_n', c_void_p)

    @property
    def fracture_number(self):
        return core.frac_nt_get_bd_n(self.handle)

    def get_fracture(self, index):
        index = get_index(index, self.fracture_number)
        if index is not None:
            return FractureNetwork.Fracture(self, index)

    core.use(c_size_t, 'frac_nt_add_nd', c_void_p, c_double, c_double)

    def add_vertex(self, x, y):
        index = core.frac_nt_add_nd(self.handle, x, y)
        return self.get_vertex(index)

    core.use(c_size_t, 'frac_nt_add_bd', c_void_p, c_size_t, c_size_t)

    def add_fracture(self, i0, i1):
        index = core.frac_nt_add_bd(self.handle, i0, i1)
        return self.get_fracture(index)

    core.use(None, 'frac_nt_clear', c_void_p)

    def clear(self):
        core.frac_nt_clear(self.handle)

    @property
    def vertexes(self):
        return Iterator(model=self,
                        count=self.vertex_number, get=lambda m, ind: m.get_vertex(ind))

    @property
    def fractures(self):
        return Iterator(model=self,
                        count=self.fracture_number, get=lambda m, ind: m.get_fracture(ind))


class InfMatrix(HasHandle):
    core.use(c_void_p, 'new_frac_mat')
    core.use(None, 'del_frac_mat', c_void_p)

    def __init__(self, network=None, sol2=None, handle=None):
        """
        创建给定handle的引用
        """
        super(InfMatrix, self).__init__(handle, core.new_frac_mat, core.del_frac_mat)
        if network is not None and sol2 is not None:
            self.update(network=network, sol2=sol2)

    core.use(c_size_t, 'frac_mat_size', c_void_p)

    @property
    def size(self):
        return core.frac_mat_size(self.handle)

    core.use(None, 'frac_mat_create', c_void_p, c_void_p, c_void_p)

    def update(self, network, sol2):
        assert isinstance(network, FractureNetwork)
        assert isinstance(sol2, DDMSolution2)
        core.frac_mat_create(self.handle, network.handle, sol2.handle)


class FracAlg:
    core.use(c_size_t, 'frac_alg_update_disp', c_void_p, c_void_p,
             c_size_t, c_size_t,
             c_double, c_double,
             c_size_t, c_size_t, c_double, c_double)

    @staticmethod
    def update_disp(network, matrix, fa_yy=99999999, fa_xy=99999999,
                    gradw_max=0, err_max=0.1, iter_min=10, iter_max=10000,
                    ratio_max=0.99, dist_max=1.0e6):
        """
        更新位移
        """
        assert isinstance(network, FractureNetwork)
        assert isinstance(matrix, InfMatrix)
        return core.frac_alg_update_disp(network.handle, matrix.handle, fa_yy, fa_xy,
                                         gradw_max, err_max, iter_min, iter_max,
                                         ratio_max, dist_max)

    core.use(None, 'frac_alg_extend_tip',
             c_void_p, c_void_p, c_void_p, c_double, c_double, c_double)

    @staticmethod
    def extend_tip(network, kic, sol2, l_extend, va_wmin=99999999, angle_max=0.6):
        assert isinstance(network, FractureNetwork)
        assert isinstance(kic, Tensor2)
        assert isinstance(sol2, DDMSolution2)
        core.frac_alg_extend_tip(network.handle, kic.handle, sol2.handle, l_extend,
                                 va_wmin, angle_max)

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
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork)
        core.frac_alg_update_topology(seepage.handle, network.handle, layer_n, z_min, z_max,
                                      ca_area, fa_width, fa_dist)

    core.use(None, 'frac_alg_add_frac', c_void_p, c_double, c_double, c_double, c_double,
             c_double, c_void_p)

    @staticmethod
    def add_frac(network: FractureNetwork, p0, p1, lave, *, data=None):
        """
        添加裂缝单元.
        注意：
            将根据给定的lave来分割单元，并自动处理和已有裂缝之间的位置关系.
        """
        assert isinstance(network, FractureNetwork)
        if data is not None:
            assert isinstance(data, FractureNetwork.FractureData)
        core.frac_alg_add_frac(network.handle, p0[0], p0[1], p1[0], p1[1], lave, 0 if data is None else data.handle)

    core.use(None, 'frac_alg_get_induced', c_void_p, c_size_t, c_size_t, c_void_p)

    @staticmethod
    def get_induced(network, fa_xy, fa_yy, matrix):
        """
        计算诱导应力，并且存储到给定的属性中
        """
        assert isinstance(network, FractureNetwork)
        assert isinstance(matrix, InfMatrix)
        assert network.fracture_number == matrix.size
        core.frac_alg_get_induced(network.handle, fa_xy, fa_yy, matrix.handle)


def main(argv: list):
    """
    模块运行的主函数.
    """
    if len(argv) == 1:
        print(about())
        return
    if len(argv) == 2:
        if argv[1] == 'env':
            try:
                from zmlx.alg.install_dep import install_dep
                install_dep(print)
            except Exception as e:
                print(e)
        return


if __name__ == "__main__":
    main(sys.argv)

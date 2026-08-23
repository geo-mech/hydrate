"""控制台内核执行器。

在独立线程中执行用户代码，支持暂停/停止/断点，
通过 Qt 信号与主线程通信。

Modified by Claude, 2026-08-12
"""

import os
import timeit

from zmlx.alg.base import time2str
from zmlx.system import app_data
from zmlx.ui.alg import add_code_history, add_exec_history, get_last_exec_history
from zmlx.ui.pyqt import QtCore
from zmlx.ui.settings import play_error, load_priority, priority_value
from zmlx.ui.utils import CodeFile, SharedValue, BreakPoint


class ConsoleThread(QtCore.QThread):
    """代码执行线程。

    在独立线程中运行用户代码，完成后通过信号通知主线程。
    """

    sig_done = QtCore.pyqtSignal()
    sig_err = QtCore.pyqtSignal(str)

    def __init__(self, code):
        """初始化执行线程。

        Args:
            code: 要执行的可调用对象。
        """
        super(ConsoleThread, self).__init__()
        self.code = code
        self.result = None
        self.post_task = None
        self.text_end = None
        self.time_beg = None

    def run(self):
        """在线程中执行代码，捕获 KeyboardInterrupt 和通用异常。"""
        if self.code is not None:
            try:
                self.result = self.code()
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
            except Exception as err:
                self.sig_err.emit(f'{err}')
        self.sig_done.emit()


class Console(QtCore.QObject):
    """控制台内核。

    管理代码执行的完整生命周期：启动 → 暂停/继续 → 停止，
    支持执行脚本文件和 Python 代码字符串。
    """

    sig_kernel_started = QtCore.pyqtSignal()
    sig_kernel_done = QtCore.pyqtSignal()
    sig_kernel_err = QtCore.pyqtSignal(str)
    sig_refresh = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Console, self).__init__(parent)
        self.kernel_err = None
        self.thread = None
        self.result = None
        self.break_point = BreakPoint(self)
        self.flag_exit = SharedValue(False)

    def get_pause(self):
        """返回是否处于暂停状态。"""
        return self.break_point.locked()

    def set_pause(self, value):
        """设置暂停/继续状态，触发界面刷新。"""
        if value != self.get_pause():
            if self.break_point.locked():
                self.break_point.unlock()
            else:
                self.break_point.lock()
            self.sig_refresh.emit()

    def get_stop(self):
        """返回是否处于停止状态。"""
        return self.flag_exit.get()

    def set_stop(self, value):
        """设置停止状态（停止时自动解除暂停）。"""
        self.flag_exit.set(value)
        if value:
            self.set_pause(False)
        self.sig_refresh.emit()

    def stop(self):
        """切换停止/运行状态（UI 按钮回调）。"""
        app_data.log(f'execute <stop_clicked> of {self}')
        self.set_stop(not self.get_stop())

    def exec_file(self, fname=None):
        """执行 Python 脚本文件。

        Args:
            fname: 文件路径。
        """
        if not isinstance(fname, str):
            return
        if os.path.isfile(fname):
            self.start_func(CodeFile(fname), name='__main__')

    def start_func(
            self, code, text_beg=None, text_end=None,
            post_task=None, file=None, name=None, add_history=True):
        """
        启动方程，注意，这个函数的调用不支持多线程（务必再主线程中调用）
        """
        if code is None:  # 清除最后一次调用的信息
            if add_history:
                add_exec_history(None)
            return

        if self.is_running():
            play_error()
            return

        if add_history:
            add_exec_history(dict(
                code=code, text_beg=text_beg, text_end=text_end,
                post_task=post_task, file=file, name=name, add_history=add_history))

        if isinstance(code, CodeFile):  # 此时，执行脚本文件
            if not code.exists():
                if add_history:
                    add_exec_history(None)
                return
            file = code.abs_path()
            code = code.get_text()
            text_beg = f"Start: {file}"
            text_end = 'Done'
            add_code_history(file)  # 记录代码历史
            app_data.log(f'execute file: {file}')  # since 230923

        self.result = None
        self.kernel_err = None

        app_data.space['__file__'] = file if isinstance(file, str) else ''
        app_data.space['__name__'] = name if isinstance(name, str) else ''

        if isinstance(code, str):
            self.thread = ConsoleThread(lambda: exec(code, app_data.space))
        else:
            self.thread = ConsoleThread(code)

        self.thread.post_task = post_task
        self.thread.text_end = text_end
        self.thread.sig_done.connect(self.__kernel_exited)
        self.thread.sig_err.connect(self.__kernel_err)
        priority = load_priority()
        if text_beg is not None:
            print(f'{text_beg} ({priority})')
        self.thread.time_beg = timeit.default_timer()
        self.set_stop(False)
        self.set_pause(False)
        self.thread.start(priority_value(priority))
        self.sig_kernel_started.emit()
        self.sig_refresh.emit()

    def start_last(self):
        """重新执行上一次的代码。"""
        last_history = get_last_exec_history()
        if last_history is not None:
            self.start_func(**last_history)

    def __kernel_exited(self):
        """内核线程完成后的回调：获取结果，打印耗时，执行善后任务。"""
        if self.thread is not None:
            self.result = self.thread.result  # 首先，要获得结果

            self.set_stop(False)
            self.set_pause(False)

            if self.thread.text_end is not None:
                print(self.thread.text_end)

            time_end = timeit.default_timer()
            if self.thread.time_beg is not None and time_end is not None:
                t = time2str(time_end - self.thread.time_beg)
                print(f'Time used = {t}\n')

            post_task = self.thread.post_task
            self.thread = None  # 到此未知，线程结束

            self.sig_kernel_done.emit()
            self.sig_refresh.emit()

            try:  # 完成了所有的工作，再执行善后
                if callable(post_task):
                    post_task()
            except Exception as err:
                print(err)

    def __kernel_err(self, err):
        """内核线程异常回调：记录错误信息。"""
        self.kernel_err = err
        print(f'Error: {err}')
        self.sig_kernel_err.emit(err)
        try:
            app_data.log(f'meet exception: {err}')
        except Exception as err:
            print(err)

    def is_running(self):
        """返回内核是否正在运行。"""
        return self.thread is not None

    def get_break_point(self):
        """返回断点控制器。"""
        return self.break_point

    def get_flag_exit(self):
        """返回停止标志。"""
        return self.flag_exit

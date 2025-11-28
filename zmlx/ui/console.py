import os
import timeit

from zml import app_data
from zmlx.alg.base import time2str
from zmlx.ui.alg import add_code_history, add_exec_history, get_last_exec_history
from zmlx.ui.pyqt import QtCore
from zmlx.ui.settings import play_error, load_priority, priority_value
from zmlx.ui.utils import CodeFile, SharedValue, BreakPoint


class ConsoleThread(QtCore.QThread):
    sig_done = QtCore.pyqtSignal()
    sig_err = QtCore.pyqtSignal(str)

    def __init__(self, code):
        super(ConsoleThread, self).__init__()
        self.code = code
        self.result = None
        self.post_task = None
        self.text_end = None
        self.time_beg = None

    def run(self):
        if self.code is not None:
            try:
                self.result = self.code()
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
            except Exception as err:
                self.sig_err.emit(f'{err}')
        self.sig_done.emit()


class Console(QtCore.QObject):
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
        return self.break_point.locked()

    def set_pause(self, value):
        if value != self.get_pause():
            if self.break_point.locked():
                self.break_point.unlock()
            else:
                self.break_point.lock()
            self.sig_refresh.emit()

    def get_stop(self):
        return self.flag_exit.get()

    def set_stop(self, value):
        self.flag_exit.set(value)
        if value:
            self.set_pause(False)
        self.sig_refresh.emit()

    def stop(self):
        app_data.log(f'execute <stop_clicked> of {self}')
        self.set_stop(not self.get_stop())

    def exec_file(self, fname=None):
        if not isinstance(fname, str):
            return
        if os.path.isfile(fname):
            self.start_func(CodeFile(fname), name='__main__')

    def start_func(
            self, code, text_beg=None, text_end=None,
            post_task=None, file=None, name=None):
        """
        启动方程，注意，这个函数的调用不支持多线程（务必再主线程中调用）
        """
        if code is None:  # 清除最后一次调用的信息
            add_exec_history(None)
            return

        if self.is_running():
            play_error()
            return

        add_exec_history(dict(
            code=code, text_beg=text_beg, text_end=text_end,
            post_task=post_task, file=file, name=name))

        if isinstance(code, CodeFile):  # 此时，执行脚本文件
            if not code.exists():
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
        last_history = get_last_exec_history()
        if last_history is not None:
            self.start_func(**last_history)

    def __kernel_exited(self):
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
        self.kernel_err = err
        print(f'Error: {err}')
        self.sig_kernel_err.emit(err)
        try:
            app_data.log(f'meet exception: {err}')
        except Exception as err:
            print(err)

    def is_running(self):
        return self.thread is not None

    def get_break_point(self):
        return self.break_point

    def get_flag_exit(self):
        return self.flag_exit

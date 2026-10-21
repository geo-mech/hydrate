"""控制台内核执行器：**界面上唯一允许跑长任务的线程槽位**.

⚠️ 用之前先看 [`AGENTS.md`](AGENTS.md) §6（控制台与线程模型）—— 那里有
「什么时候用 ``gui.start`` / ``gui.call`` / ``gui.add_task``」的选型表与排查表。
本文只讲实现。

⚠️ **`Console` 仍是长任务唯一槽位**（2026-10-20 加注，别误读）
------------------------------------------------------------
「长任务」= 仿真、批量计算这类**要能被暂停/停止**、跑几分钟到几小时的工作。这句话
**不因新增工具而改变**：同一天加入的
:mod:`zmlx.ui.utils.thread_runner` 只解决「**多个短/中任务并发**」（扫描、加载、批量小
请求），**不是**本类的替代品 ——

- 它不接管工具栏的「暂停 / 继续 / 停止」（那三个按钮只对 :func:`gui.break_point` 生效）；
- 它不参与 ``Console.thread`` 的单槽位记账，两者**互不知情**；
- 反过来说，**并发短任务也不能塞进本类** —— ``start_func`` 忙时直接丢弃请求。

判据一句话：**需要「暂停/继续/停止」⇒ 本类；只是「并行做完再回写界面」⇒ thread_runner**。
详见 ``AGENTS.md`` §6.3（单任务约束）与 §6.8（thread_runner 的分工表）。

结构
----
``MainWindow`` 持有一个 :class:`Console`（``QObject``，GUI 线程），它至多持有**一个**
:class:`ConsoleThread`（``QThread``）。调用链是::

    gui.start(func, post_task=...)      # GuiBuffer.start → GuiApi.command('start', ...)
      → MainWindow.start_func           # 转发（main.py）
      → Console.start_func              # 建线程、记账、发信号
      → ConsoleThread.run               # **内核线程**里执行 func

⚠️ **单任务、不排队**：``Console.thread`` 是唯一槽位。``is_running()`` 为真时
:meth:`Console.start_func` 只 ``play_error()`` 响一声，然后**丢弃**请求 —— 不抛异常、
不返回失败标记（2026-10-20 实测：忙时第二个 ``gui.start`` 完全不执行）。所以调用方
**必须自己判** ``gui.is_running()``，并把「忙」告诉用户。

信号（都在 GUI 线程被处理）
--------------------------
- ``sig_kernel_started`` / ``sig_kernel_done`` —— 起止。``sig_done`` 由 ConsoleThread
  发出、连到 :meth:`Console.__kernel_exited`（GUI 线程的槽），``post_task`` 就在那里跑：
  **任务抛异常也会执行**，所以「回写按钮 / 状态栏」应当放这里。
- ``sig_kernel_err`` —— 异常，打印到 stderr（界面里显示成红字）。
- ``sig_refresh`` —— 让主窗口刷新状态。它同时会刷新**当前标签页**（版本按钮借它显示
  「运行中 / 已暂停」）—— 这就是「内核一结束，插件页会自动重扫」的来源。

暂停 / 停止 / 断点
------------------
三者都靠脚本里放的 ``gui.break_point()`` 生效：它在**内核线程**里阻塞等「继续」，在
**GUI 线程**里径直返回（见 :class:`zmlx.ui.utils.break_point.BreakPoint`）—— 否则
GUI 线程会自己等自己，界面冻死。不写 ``break_point()`` 的脚本停不下来，这是设计使然。

⚠️ :meth:`Console.start_func` 还会改写 ``app_data.space`` 的 ``__name__`` / ``__file__``
（即使传的是 callable），而右侧命令行与脚本**共用**这个 namespace。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-20: 补机制说明（单任务约束、信号链路、暂停语义）
Modified by DeepSeek, 2026-10-20: 文档头明确「Console 仍是长任务唯一槽位」，与 thread_runner 划清边界
"""

import os
import sys
import timeit

from zmlx.algs.base import time2str
from zmlx.system import app_data, log
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
        # ⚠️ 不用 f'{self}'：它的 repr 带**内存地址**，每次都不同 ->
        #    tag 每次都不同 -> 去重完全失效，还会把无意义地址刷进日志。
        log('execute <stop_clicked>', tag='execute <stop_clicked>')
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
            log(f'execute file: {file}',  # since 230923
                tag=f'execute file: {file}')

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
            # 蓝色（ANSI 34）：系统提示用统一的蓝，浅色主题下深蓝 / 暗色主题下浅蓝
            # （取色见 OutputWidget 的 _Ansi；控制台关掉「ANSI 颜色」时会被过滤成纯文本）
            print(f'\033[34m{text_beg} ({priority})\033[0m')
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
                # 与 Start 同一角色（系统提示），用同一个蓝
                print(f'\033[34m{self.thread.text_end}\033[0m')

            time_end = timeit.default_timer()
            if self.thread.time_beg is not None and time_end is not None:
                t = time2str(time_end - self.thread.time_beg)
                # 蓝色（ANSI 34）：浅色主题下深蓝、暗色主题下浅蓝（见 OutputWidget 的 _Ansi）
                print(f'\033[34mTime used = {t}\033[0m\n')

            post_task = self.thread.post_task
            self.thread = None  # 到此未知，线程结束

            self.sig_kernel_done.emit()
            self.sig_refresh.emit()

            try:  # 完成了所有的工作，再执行善后
                if callable(post_task):
                    post_task()
            except Exception as err:
                print(err, file=sys.stderr)

    def __kernel_err(self, err):
        """内核线程异常回调：记录错误信息。"""
        self.kernel_err = err
        print(f'Error: {err}', file=sys.stderr)
        self.sig_kernel_err.emit(err)
        try:
            log(f'meet exception: {err}', tag=f'meet exception: {err}')
        except Exception as err:
            print(err, file=sys.stderr)

    def is_running(self):
        """返回内核是否正在运行。"""
        return self.thread is not None

    def get_break_point(self):
        """返回断点控制器。"""
        return self.break_point

    def get_flag_exit(self):
        """返回停止标志。"""
        return self.flag_exit

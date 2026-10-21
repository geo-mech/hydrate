"""任务处理器（``TaskProc``）：队列 + 信号驱动的回调执行器.

通过 ``add(task)`` 把回调丢进队列，再由信号 ``__sig_do_task`` 触发执行，
从而避免 GUI 阻塞。「信号」这一步是关键：无论从哪个线程 ``add``，真正执行
任务的都是持有这个 ``QObject`` 的那个线程（通常是 GUI 线程）。

⚠️ 与 :class:`zmlx.ui.utils.gui_api.GuiApi` 的分工：``GuiApi`` 是**同步**的
（调用者阻塞等返回值与异常），``TaskProc`` 是**异步**的（丢下就走，拿不到
结果）。要返回值用 ``GuiApi``，只是「稍后在 GUI 线程跑一下」用 ``TaskProc``。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
"""

from queue import Queue, Empty

from zmlx.ui.pyqt import QtCore


class TaskProc(QtCore.QObject):
    """任务处理器（队列 + 信号驱动）。

    通过 ``add(task)`` 添加回调函数到队列，
    由信号 ``__sig_do_task`` 触发执行，避免 GUI 阻塞。
    """

    __sig_do_task = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__tasks = Queue()
        self.__mtx = QtCore.QMutex()
        self.__sig_do_task.connect(self.__do_task)

    def _get_task(self):
        """
        弹出一个任务.
        """
        self.__mtx.lock()
        try:  # 尝试从队列中弹出一个任务
            res = self.__tasks.get(block=False)
        except Empty:
            res = None
        except Exception as err:
            print(f'Error: {err}')
            res = None
        self.__mtx.unlock()
        return res

    def __do_task(self):
        while True:
            try:
                task = self._get_task()
                if task is None:
                    break
                else:
                    if not callable(task):
                        raise RuntimeError('The task is not a function')
                    task()
            except Exception as err:
                print(f'meet error {err}')

    def add(self, task):
        """添加任务到队列。"""
        try:
            if callable(task):
                self.__mtx.lock()
                self.__tasks.put(task, block=False)
                self.__mtx.unlock()
                self.__sig_do_task.emit()
        except Exception as err:
            print(f'meet error {err}')

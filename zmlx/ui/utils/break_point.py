"""断点控制器（``BreakPoint``）：暂停 / 继续 / 安全终止.

它要同时满足两件互相拉扯的事：

1. **内核线程要能「停下来等恢复」** —— 用户点「暂停」后，迭代必须停在下一个
   断点上，直到点「继续」；
2. **GUI 线程绝不能被它卡住** —— 否则界面彻底冻死（连「继续」都点不动）。

⚠️ **不能用一把互斥量同时承担这两件事** —— 老实现就是那么写的，结果是「暂停」
在 **GUI 线程**上取锁（``console.set_pause(True)`` ← 工具栏按钮
:meth:`MainWindow.click_pause`），持锁者成了 GUI 线程自己；此后界面上任何一次
``gui.break_point()`` 都对同一把**非递归**锁再 ``lock()``，调用者永久阻塞。
真踩过：用户报告「界面偶尔彻底卡死，无法复现」。

⚠️ 也**不能**简单改成「拿不到锁就直接过」（``tryLock``）——那确实不卡死了，
但内核也再停不下来，等于**把「暂停」这个功能删掉**（实测：暂停后内核线程
1.5 秒内照常跑完）。

所以 :meth:`pass_only` 内部按**调用者身份**决定等不等：内核线程等（这才是「暂停」
生效的地方），**GUI 线程径直返回**（界面永不冻死）。

实现用 ``threading.Event`` 表示「正在暂停」：Event 允许**多个线程同时等待**、
且没有「锁归谁所有」的概念，所以不存在某个线程占着不放的问题；
:meth:`unlock` 一次唤醒所有等待者。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
"""

import threading as _threading

from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.utils.shared import SharedValue


class _GuiThread:
    """「当前线程是不是 GUI 线程」的判定（不实例化，纯命名空间）。

    照本仓库约定，模块级只留 import / 类定义，故把原本的模块级函数
    ``_is_gui_thread`` 收进这个私有类，作为 :meth:`current` 静态方法。
    """

    @staticmethod
    def current():
        """当前线程是不是 Qt 的主（GUI）线程.

        ⚠️ 用在 :class:`BreakPoint` 里判断「能不能在这里等」：GUI 线程**绝不能**被
        断点阻塞（否则界面冻死，连「继续」都点不动），所以它必须能识别出来自己。

        ⚠️ 没有 ``QApplication`` 时（无头 / 纯逻辑测试）``instance()`` 返回 ``None``，
        此时一律按「不是 GUI 线程」处理 —— 那些场合本来也没有界面会被卡住；而
        :class:`BreakPoint` 的等待语义仍需保留，故不能反过来返回 True。

        Returns:
            bool: True 表示当前线程是 Qt 主线程。
        """
        try:
            app = QtWidgets.QApplication.instance()
            if app is None:
                return False
            return QtCore.QThread.currentThread() is app.thread()
        except Exception:
            return False


class BreakPoint(QtCore.QObject):
    """断点控制器（暂停 / 继续 / 安全终止）。

    详见模块 docstring。
    """

    __sig_unlocked = QtCore.pyqtSignal()
    __sig_locked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(BreakPoint, self).__init__(parent)
        #: 暂停期间被 **clear**（``wait`` 阻塞），恢复时 **set**（唤醒所有等待者）
        self.__resumed = _threading.Event()
        self.__resumed.set()
        self.__locked = SharedValue(False)

    def pass_only(self):
        """「路过」断点：**暂停期间阻塞**（等 :meth:`unlock`），但 **GUI 线程径直返回**。

        ⚠️ 那三行判断是本类**唯一**要小心的地方，也是「界面永不冻死」的全部实现：

        1. ``not locked()`` → 没暂停，立即通过；
        2. ``_GuiThread.current()`` → **GUI 线程直接过**。暂停本来就是从 GUI 线程发起
           的（``console.set_pause(True)`` ← 工具栏按钮 :meth:`MainWindow.click_pause`
           / ``gui.pause()`` 内部的 ``command('click_pause')``），让 GUI 线程再回来
           等自己就是死锁 —— 界面会彻底冻住，连「继续」都点不动，只能杀进程。
           真踩过：用户报告「界面偶尔彻底卡死，无法复现」。
        3. 其余（内核线程）→ 真的等，这才是「暂停」生效的地方。

        ⚠️ 老实现用一把**非递归 QMutex** 做这件事（``lock()`` / ``unlock()``），
        于是「暂停」取的锁被 GUI 线程自己持有，界面上任何一次 ``break_point()``
        都对同一把锁再 ``lock()`` → 永久阻塞。现在改用 ``threading.Event``：
        它允许**多个线程同时等待**、且没有「锁归谁所有」的概念。

        ⚠️ 也**不能**改成「拿不到就过」（无条件 ``tryLock``）：那样确实不卡死，
        但内核也再停不下来，等于**把「暂停」功能删掉**（实测：暂停后内核线程
        1.5 秒内照常跑完）。必须按**调用者身份**区分，而不是取消等待。

        ⚠️ **刻意不给 ``timeout`` 参数**：能超时返回，就意味着「暂停状态下迭代
        自己又跑起来了」—— 而且用户看不出来（他以为停了）。要等就一直等到
        :meth:`unlock`，不存在「等一会儿」的中间状态。

        Returns:
            bool: True 表示当时确实处于暂停态（等过）；False 表示没等
            （未暂停，或调用者是 GUI 线程）。
        """
        if not self.__locked.get():
            return False            # 没暂停：立即通过
        if _GuiThread.current():
            return False            # ⚠️ GUI 线程绝不能等 —— 它正是那个「要去解锁的人」
        self.__resumed.wait()
        return True

    def locked(self):
        """返回是否处于锁定状态。"""
        return self.__locked.get()

    def lock(self):
        """暂停：此后 :meth:`pass_only` 会阻塞（GUI 线程除外）。"""
        if not self.__locked.get():
            self.__resumed.clear()
            self.__locked.set(True)
            self.__sig_locked.emit()

    def unlock(self):
        """恢复：唤醒所有停在 :meth:`pass_only` 上的线程。"""
        if self.__locked.get():
            self.__locked.set(False)
            self.__resumed.set()
            self.__sig_unlocked.emit()

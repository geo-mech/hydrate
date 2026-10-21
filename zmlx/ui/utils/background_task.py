"""后台循环任务（``BackgroundTask``）：把一个无参回调放到最低优先级的函数里反复执行.

设计目标只有一句话：**让这个任务一直在跑，但绝不占着 CPU**。

要做的事只有一件 —— 调用 :meth:`BackgroundTask.set_task` 记住任务，线程就起来，
按「执行一次 → 睡一会儿」的节奏一直转到任务被清空。

为什么放在 ``zmlx/ui/utils/``
----------------------------

它建立在 **Qt 的线程原语**上（``QThread`` / ``QMutex`` / ``QWaitCondition``），与本目录
其余代码同一套路；线程优先级也直接走 Qt 的 ``QThread.Priority.LowestPriority``
（实测落到 Windows 的 ``THREAD_PRIORITY_LOWEST``，即 OS 优先级 **-2**），不必自己
``ctypes`` 调 ``SetThreadPriority``。

⚠️ 因此**它需要有 Qt**：无头模式（``--no-gui``）下本模块会抛 ``ImportError``。
需要「不依赖 Qt 的后台循环」时，请用 stdlib 的 ``threading`` 另写一个（本类**没有**
做双后端，免得两套线程语义混在一起）。

⚠️ **本模块刻意不被 ``zmlx/ui/utils/__init__.py`` 转发**（需要 Qt 的那几个同门模块
都被转发了，它是例外）：它一 import 就要求 ``QtCore`` 存在，而无头模式下 ``QtCore``
是 ``None``，一旦转发，``import zmlx.ui.utils`` 本身就会炸。它保持按需单独导入：
``from zmlx.ui.utils.background_task import BackgroundTask``。

三重「不占 CPU」的保证
---------------------

1. **线程优先级压到最低**：``start(QThread.Priority.LowestPriority)``。
   ⚠️ 优先级只决定「有竞争时谁先让路」，**不决定「占多少 CPU」** —— 真正省 CPU 靠下面两条。
2. **每执行一次，至少睡 ``min_sleep``（默认 0.2 秒 = 200 毫秒）**。睡着时不占 CPU。
3. **按「任务耗时占周期的比例」动态拉长睡眠**：目标
   ``work / (work + sleep) <= ratio``（``ratio`` 默认 0.2），于是

   .. code-block:: text

       sleep >= work * (1 - ratio) / ratio          # ratio = 0.2 时就是「睡足 4 倍耗时」

   取 ``max(min_sleep, 上式)``。

   注意这是**上界**而不是目标值：有了 200 毫秒的底，一个 0.1 毫秒的小任务实际只占
   ``0.1 / 200.1 ≈ 0.05%``，远低于 20%。想知道真实占比看 :attr:`stats` 里的 ``duty``。

计时口径
--------

「任务占用的时间」按**墙钟**计（``time.perf_counter``，与仓库里 ``FrameRateCtrl`` /
``GuiIterator`` 用的 ``timeit.default_timer`` 是同一个时钟）。⚠️ 因此若任务自己内部
有等待（IO、``sleep``），那段等待也算进 ``work``，会睡得更久一些 —— 这是刻意的：
「占用」按墙钟理解才符合直觉，也更保守。

用法
----

.. code-block:: python

    from zmlx.ui.utils.background_task import BackgroundTask

    task = BackgroundTask(ratio=0.2)        # 任务的耗时最多占总时间的 20%
    task.set_task(do_something)             # 记住任务并起线程；立刻执行第一次
    ...
    task.set_task(None)                     # 清空任务（线程转入空闲等待）
    print(task.stats['duty'])               # 实测的真实占比

也可以 ``with`` 着用（退出时真正把线程停掉并等它收尾）：::

    with BackgroundTask(0.2) as task:
        task.set_task(refresh)
        ...

线程生命周期（照本仓库的线程契约）
----------------------------------

1. **线程不设 parent**（``QtCore.QThread(None)``）：标签页/控件销毁走 ``deleteLater()``，
   会**连同子对象**一起删 —— parent 指向别处的 ``QThread`` 在运行中被析构会让进程
   直接崩（``QThread: Destroyed while thread is still running``，**不是** Python 异常，
   ``try/except`` 兜不住）。
2. **用模块级列表 ``_RUNNING`` 持强引用**（与 ``tabs/demo_view.py`` 同一写法），
   跑完由 ``finished`` 摘表。这样即使调用方把 ``BackgroundTask`` 丢掉，也不会出现
   「QThread 还在跑却被回收」。
3. ⚠️ 线程体持有的是宿主的 **weakref**（不是强引用）：于是「宿主被回收」能被线程自己
   发现并收工 —— 既不会变成永远转下去的僵尸线程，也不会形成环。

``set_task(None)`` 的语义
-------------------------

它**清空任务**，线程随即转入**空闲等待**（``QWaitCondition`` 上无限期等待，0 次唤醒、
0% CPU），**不是**把线程销毁。这样做有个实打实的好处：**不存在「刚停就重启」的竞态**
（线程一旦退出，就必须由 ``set_task`` 重新拉起，而这中间是有窗口的）。
真正让线程收工的是 :meth:`__exit__`（``with`` 退出）与对象被回收。

几个刻意的取舍
--------------

- **只有一个公开方法** :meth:`set_task`。此外只有一个只读属性 :attr:`stats`
  （用来核实「是不是真的只占了 20%」）和 ``__enter__`` / ``__exit__``。
- **任务抛异常不会停掉循环**：计一次错、报一次错（同一条错误最多每
  ``ERROR_REPORT_INTERVAL`` 秒报一次，免得刷屏），然后照常继续。
- **换任务是「下一轮生效」**，不会打断本轮睡眠 —— 于是「每次调用后至少睡 ``min_sleep``」
  在任何调用顺序下都成立（睡眠只可能被「关机」打断，而那时也不再执行任务了）。
- **任务必须是零参可调用**；要带参数请用 ``functools.partial`` / ``lambda``。
- ⚠️ 任务跑在**后台线程**里，**不许直接碰界面控件**。要更新界面请把它转投回主线程
  （``zmlx.ui.gui_exec`` / ``GuiApi``）。

Created by DeepSeek, 2026-10-16
"""

import atexit
import sys
import time
import traceback
import weakref

from zmlx.ui.pyqt import QtCore

if QtCore is None:  # 无头模式（或 Qt 绑定导入失败）
    raise ImportError(
        'BackgroundTask 建立在 Qt 的线程原语上（QThread/QMutex/QWaitCondition），'
        '当前进程没有导入任何 Qt 绑定（多半是 --no-gui 无头模式），因此不可用。'
    )

#: 正在跑的线程（**模块级**强引用）。
#:
#: ⚠️ 线程**不设 parent**（见模块 docstring），所以必须由别的东西持着它，否则
#: QThread 在运行中被回收 = 进程直接崩。跑完由 ``finished`` 摘表。
#: 这与 ``tabs/demo_view.py`` 的 ``_RUNNING`` 是同一套写法。
_RUNNING = []


def _forget(thread):
    """把已经跑完的线程从登记表里摘掉。"""
    try:
        _RUNNING.remove(thread)
    except ValueError:
        pass


def _shutdown_all():
    """解释器收尾时，把登记表里还在跑的线程都请走。

    为什么要这一步：``QThread`` 对象在**运行中**被析构会让进程直接崩
    （``QThread: Destroyed while thread is still running``）。正常路径下不会走到这里
    （调用方该用 ``with`` 或 ``set_task(None)``），但「脚本跑完就撒手不管」是最常见
    的用法之一 —— 与其赌解释器收尾顺序，不如明确地在收尾时把线程停掉。
    """
    for thread in list(_RUNNING):
        try:
            owner = thread.owner()
            if owner is not None:
                owner._stop_thread()          # 有界等待（JOIN_TIMEOUT_MS）
            else:
                thread.wait(200)              # 宿主没了：它自己就该退出了
        except Exception:
            pass


#: ``atexit`` 钩子只注册一次（且**只在真的起过线程之后**才注册，见 set_task）
_ATEXIT_REGISTERED = False


def _ensure_atexit():
    """确保退出钩子已注册（在 ``set_task`` 持锁时调用）。"""
    global _ATEXIT_REGISTERED
    if not _ATEXIT_REGISTERED:
        _ATEXIT_REGISTERED = True
        atexit.register(_shutdown_all)


class _Runner(QtCore.QThread):
    """线程体：反复「等任务 → 执行一次 → 睡够」，直到宿主被回收或要求关机。

    ⚠️ 它只持有宿主的 **weakref** —— 不是强引用。这样：
    「宿主被回收」能被线程自己发现（于是收工），又不会形成
    ``宿主 → 线程 → 宿主`` 的环把两者一起钉住。
    """

    def __init__(self, owner):
        """初始化。

        Args:
            owner: :class:`BackgroundTask` 实例（**只弱引用**，不强留）。
        """
        super(_Runner, self).__init__(None)       # ⚠️ parent 一律留空
        self.setObjectName('BackgroundTask')
        self._owner = weakref.ref(owner)

    def owner(self):
        """返回宿主（已被回收时为 None）。"""
        return self._owner()

    def run(self):
        """线程体（异常绝不允许逃出 ``run()``）。"""
        try:
            while True:
                owner = self._owner()
                if owner is None:
                    return                        # 宿主已被回收：收工
                if not owner._pump():
                    return                        # 被要求关机
        except Exception:
            try:
                traceback.print_exc(file=sys.stderr)
            except Exception:
                pass


class BackgroundTask:
    """把无参回调放到最低优先级线程里反复执行的「后台循环任务」。

    详见模块 docstring。类的公开接口只有一个方法 :meth:`set_task`。
    """

    #: 默认的「任务耗时 / 总耗时(含睡眠)」上限
    DEFAULT_RATIO = 0.2

    #: 默认的最小睡眠（秒）；即需求里的「至少 200 毫秒」
    DEFAULT_MIN_SLEEP = 0.2

    #: 同一条错误最多每这么多秒报一次（避免日志被刷爆）
    ERROR_REPORT_INTERVAL = 10.0

    #: ``__exit__`` 里等线程收尾的最长时间（毫秒）
    JOIN_TIMEOUT_MS = 2000

    #: 睡眠的分片长度（毫秒）：只为让「关机请求」能在几百毫秒内被发现；
    #: 分片期间线程是**睡着**的，不占 CPU。
    NAP_SLICE_MS = 250

    def __init__(self, task=None, ratio=DEFAULT_RATIO, min_sleep=DEFAULT_MIN_SLEEP,
                 max_sleep=None, on_error=None):
        """初始化（**不会**在构造时就起线程 —— 起线程由 :meth:`set_task` 负责）。

        Args:
            task: 可选的初始任务；给了就等价于再调一次 ``set_task(task)``。
            ratio: 任务的耗时占「任务+睡眠」总时间的比例上限，必须落在 ``(0, 1)``。
                ⚠️ 实际占比会被 ``min_sleep`` 进一步压低，它保证的是**上界**。
            min_sleep: 每执行一次至少睡多少秒（默认 0.2）。
            max_sleep: 睡眠上限（秒）；None 表示不封顶。
                ⚠️ 设了它就等于放弃 ``ratio`` 的保证 —— 任务偶发地慢时会被强行拉回，
                好处是任务不至于因为一次慢调用而「休眠」太久。
            on_error: 任务抛异常时的回调 ``on_error(exc)``；None 表示打印到 stderr。

        Raises:
            ValueError: 参数越界。
            TypeError: ``task`` / ``on_error`` 不是可调用的东西。
        """
        ratio = float(ratio)
        if not 0.0 < ratio < 1.0:
            raise ValueError(f'ratio 必须落在 (0, 1) 开区间, 得到 {ratio}')

        min_sleep = float(min_sleep)
        if min_sleep < 0.0:
            raise ValueError(f'min_sleep 不能为负数, 得到 {min_sleep}')

        if max_sleep is not None:
            max_sleep = float(max_sleep)
            if max_sleep < min_sleep:
                raise ValueError(
                    f'max_sleep({max_sleep}) 不能小于 min_sleep({min_sleep})')

        if on_error is not None and not callable(on_error):
            raise TypeError(
                f'on_error 必须可调用或为 None, 得到 {type(on_error).__name__}')

        self._ratio = ratio
        self._min_sleep = min_sleep
        self._max_sleep = max_sleep
        self._on_error = on_error

        # ---- 线程状态 ----
        self._mutex = QtCore.QMutex()
        self._cond = QtCore.QWaitCondition()
        self._task = None            # 当前任务（None = 空闲等待）
        self._thread = None          # 在跑的那个线程
        self._closed = False         # 是否要求线程收工（__exit__ / 被回收）

        # ---- 统计（只读快照见 stats）----
        self._runs = 0
        self._errors = 0
        self._last_work = 0.0
        self._sleep = min_sleep
        self._work_seconds = 0.0
        self._total_seconds = 0.0
        self._last_report = -1.0e18

        if task is not None:
            self.set_task(task)

    # ==================================================================== 公开接口
    def set_task(self, task):
        """记住（或更换、清空）要反复执行的任务。

        - ``task`` 是零参可调用对象时：记住它；若线程没在跑就起一个并**立刻执行第一次**。
          换任务**不影响**本轮已经在进行/即将进行的睡眠 —— 下一轮生效。
        - ``task`` 是 None 时：清空任务，线程随即转入**空闲等待**（不销毁，也不占 CPU）；
          之后再 ``set_task(新任务)`` 会立刻接上。线程真正收工由 ``with`` 退出或对象被
          回收负责。

        Args:
            task: 零参可调用对象，或 None。

        Raises:
            TypeError: ``task`` 既不是 None 也不可调用。
        """
        if task is not None and not callable(task):
            raise TypeError(
                f'task 必须可调用或为 None, 得到 {type(task).__name__}')

        start = False
        with QtCore.QMutexLocker(self._mutex):
            self._task = task
            self._closed = False          # 允许「__exit__ 之后再 set_task」重新开张
            thread = self._thread
            if task is not None and (thread is None or thread.isFinished()):
                thread = _Runner(self)
                self._thread = thread
                _RUNNING.append(thread)
                # 跑完摘表（用带默认参数的 lambda 持住线程本体，写法同 demo_view.py）
                thread.finished.connect(lambda t=thread: _forget(t))
                _ensure_atexit()          # 起过线程了，退出时要有人把它们请走
                start = True
            self._cond.wakeAll()          # 空闲/睡眠中的线程：立刻看到变化
        if start:
            thread.start(QtCore.QThread.Priority.LowestPriority)

    @property
    def stats(self):
        """运行统计的只读快照（用来核实 ``duty`` 是否真的低于 ``ratio``）。

        Returns:
            dict: ``running``（线程是否活着）/ ``has_task``（当前是否有任务）/
            ``runs`` / ``errors`` / ``last_work``（上一次任务耗时，秒）/
            ``sleep``（当前睡眠，秒）/ ``ratio``（设定值）/ ``work_seconds`` /
            ``total_seconds`` / ``duty``（实测占比 = ``work_seconds / total_seconds``）。
        """
        with QtCore.QMutexLocker(self._mutex):
            work = self._work_seconds
            total = self._total_seconds
            thread = self._thread
            return {
                'running': thread is not None and not thread.isFinished(),
                'has_task': self._task is not None,
                'runs': self._runs,
                'errors': self._errors,
                'last_work': self._last_work,
                'sleep': self._sleep,
                'ratio': self._ratio,
                'work_seconds': work,
                'total_seconds': total,
                'duty': (work / total) if total > 0.0 else 0.0,
            }

    # ==================================================================== 线程体
    def _pump(self):
        """等一个任务 → 执行一次 → 睡够（**只在 ``_Runner`` 那个线程里被调用**）。

        Returns:
            bool: False 表示收到「关机」请求，线程该收工了。
        """
        # 1) 等任务；没有就**无限期**地在条件变量上等着（既不退出，也不占 CPU）
        with QtCore.QMutexLocker(self._mutex):
            while self._task is None and not self._closed:
                self._cond.wait(self._mutex)
            if self._closed:
                return False
            task = self._task

        # 2) 执行一次，并**计时**（口径是墙钟，见模块 docstring）
        t_beg = time.perf_counter()
        failed = False
        error = None
        try:
            task()
        except Exception as err:              # 任务出错不许把循环带走
            failed = True
            error = err
        work = time.perf_counter() - t_beg

        # 3) 睡够（这段时间就是「让出 CPU」的地方）
        sleep_seconds = self._sleep_for(work)
        with QtCore.QMutexLocker(self._mutex):
            self._sleep = sleep_seconds
        slept = self._nap(sleep_seconds)

        # 4) 记统计 / 报错
        self._record(work, work + slept, failed)
        if error is not None:
            self._report(error)

        if self._closed:
            return False
        return True

    def _nap(self, seconds):
        """睡满 ``seconds`` 秒。

        ⚠️ **只有「关机」能打断它** —— 换任务、清空任务都不打断，于是
        「每次调用任务后至少睡 ``min_sleep``」在任何调用顺序下都成立。
        等待分片（``NAP_SLICE_MS``）做，只是为了让关机请求能在几百毫秒内被发现；
        分片期间线程是睡着的，不占 CPU。

        Returns:
            float: 实际睡了的秒数。
        """
        deadline = time.perf_counter() + seconds
        while True:
            remain = deadline - time.perf_counter()
            if remain <= 0.0:
                return seconds
            msecs = int(remain * 1000.0) + 1
            with QtCore.QMutexLocker(self._mutex):
                self._cond.wait(self._mutex, min(msecs, self.NAP_SLICE_MS))
                if self._closed:
                    return seconds - remain

    def _sleep_for(self, work):
        """算出这次任务之后该睡多久。

        Args:
            work: 本次任务实际耗时（秒）。

        Returns:
            float: 睡眠秒数 = ``max(min_sleep, work * (1 - ratio) / ratio)``，
            若设了 ``max_sleep`` 再封顶。
        """
        need = work * (1.0 - self._ratio) / self._ratio
        seconds = max(self._min_sleep, need)
        if self._max_sleep is not None:
            seconds = min(seconds, self._max_sleep)
        return seconds

    # ==================================================================== 统计 / 报错
    def _record(self, work, cycle, failed):
        """累计统计量（``cycle`` = 本次任务耗时 + 实际睡眠）。"""
        with QtCore.QMutexLocker(self._mutex):
            self._runs += 1
            if failed:
                self._errors += 1
            self._last_work = work
            self._work_seconds += work
            self._total_seconds += cycle

    def _report(self, error):
        """报告任务里的异常（同一条错误按间隔限流，避免刷屏）。"""
        with QtCore.QMutexLocker(self._mutex):
            now = time.perf_counter()
            first = self._errors == 1
            if not first and (now - self._last_report) < self.ERROR_REPORT_INTERVAL:
                return
            self._last_report = now
            count = self._errors

        if self._on_error is not None:
            try:
                self._on_error(error)
            except Exception:
                pass
            return

        # ⚠️ 这里也要包一层：GUI 程序可能根本没有 stderr，print 会抛异常 ——
        #    那会把循环带走，而循环一死任务就永远不跑了。
        try:
            text = ''.join(traceback.format_exception(
                type(error), error, error.__traceback__))
            print(f'[BackgroundTask] 任务抛出异常（累计第 {count} 次）:\n{text}',
                  file=sys.stderr)
        except Exception:
            pass

    # ==================================================================== 生命周期
    def _stop_thread(self):
        """要求线程收工并等它退出（有界等待）。"""
        with QtCore.QMutexLocker(self._mutex):
            self._closed = True
            self._task = None
            thread = self._thread
            self._cond.wakeAll()
        if thread is not None:
            thread.wait(self.JOIN_TIMEOUT_MS)
            with QtCore.QMutexLocker(self._mutex):
                if self._thread is thread:
                    self._thread = None

    def __enter__(self):
        """进入 ``with``：返回自身。"""
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """退出 ``with``：让线程收工并（最多等 ``JOIN_TIMEOUT_MS``）等它退出。"""
        self._stop_thread()
        return False

    def __del__(self):
        """被回收时兜底：通知线程收工（线程本身持有本对象的 weakref，也会自己发现）。

        ⚠️ 这里**不 join** —— 析构可能发生在解释器收尾阶段，那时阻塞等待很危险。
        """
        try:
            with QtCore.QMutexLocker(self._mutex):
                self._closed = True
                self._task = None
                self._cond.wakeAll()
        except Exception:
            pass


def test():
    """直接运行本文件时的小演示：验证「任务再忙也只占 ratio 的时间」。

    直接跑：``python -m zmlx.ui.utils.background_task``
    """
    app = QtCore.QCoreApplication([])
    task = BackgroundTask(ratio=0.2, min_sleep=0.2)

    def work():
        end = time.perf_counter() + 0.06           # 每次忙 60 毫秒
        while time.perf_counter() < end:
            pass                                   # 純 CPU 空转，模拟「有点重的任务」

    def report():
        s = task.stats
        print(f"runs={s['runs']:3d}  last_work={s['last_work'] * 1000:6.1f} ms  "
              f"sleep={s['sleep'] * 1000:6.1f} ms  duty={s['duty'] * 100:5.1f}%  "
              f"(ratio={s['ratio'] * 100:.0f}%)")

    task.set_task(work)
    timer = QtCore.QTimer()
    timer.timeout.connect(report)
    timer.start(500)
    QtCore.QTimer.singleShot(3200, app.quit)
    app.exec()
    timer.stop()
    task._stop_thread()
    print('停止后:', task.stats)


if __name__ == '__main__':
    test()

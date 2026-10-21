"""自动线程执行器（``ThreadRunner``）：把「起一个线程跑回调 / 跑完回调」集中到一处.

一句话：**给一个函数和一个完成回调，就起一个线程去跑；多个任务并行不互斥；
能问「还剩几个在跑」；能「立刻」叫停全部。**

⚠️ **先划清边界**：本模块**不是** ``Console`` 的替代品 ——
**``Console`` 仍是长任务唯一槽位**（仿真、批量计算这类要能被暂停/停止的工作）。
本模块只管「多个短/中任务并发」。判据一句话：**需要暂停/继续/停止 ⇒ ``gui.start``；
只是并行做完再回写界面 ⇒ 本模块**。详见下方「与既有机制的分工」与
``zmlx/ui/AGENTS.md`` §6.3 / §6.8。

为什么需要它
------------

在此之前，界面上每处需要后台工作的地方都自己写一遍 ``QThread`` 子类：
``tabs/image_browser``、``tabs/plugin_list_edit``、``tabs/check_count_view``、
``tabs/feedbacks_view``、``tabs/license_register``、``plugins/builtin/runtime_env`` …
（全仓 17 个文件）。重复的其实是**同样四件事**：

1. 建线程、起线程；
2. 用模块级列表持强引用 —— 否则 ``QThread`` 在运行中被回收会让进程**直接崩**
   （``Destroyed while thread is still running``，不是 Python 异常，``try/except`` 兜不住）；
3. 线程体包 ``try/except``，否则任务一抛异常，线索就断在后台线程里；
4. 跑完把结果搬回 GUI 线程（``gui.call`` / ``gui.add_task`` 再写一遍）。

本模块把这四件事一次做完，调用方只剩「一个函数 + 一个完成回调」。

⚠️ **下面这条决定了整个设计**：「**安全地立即终止线程**」在 Python 里**做不到**字面意义。
``threading`` 没有 ``kill``；``QThread.terminate()`` 会跳过 ``finally``、留下没释放的锁和
C++ 对象，本仓已因此崩过。能做的是下面三条的组合，本模块就是这么实现的：

======================  ====================================================
手段                     效果
======================  ====================================================
协作式取消               任务在自己选的轮询点退出 ⇒ **安全**，延迟等于轮询间隔
守护线程（daemon）        卡死在阻塞调用里的线程不阻止进程退出
「放弃」语义               :meth:`ThreadRunner.cancel_all` **立刻返回**，绝不卡界面
======================  ====================================================

因此 :meth:`~ThreadRunner.cancel_all` 的返回值是**「还剩几个没能停下来」**，而不是
「全部已停止」—— 这是把无法消除的不确定性如实交给你，而不是假装它不存在。

能取消的前提是**任务自己配合**：在耗时循环里轮询 :attr:`TaskHandle.cancelled`、调
:meth:`TaskHandle.check` 或 :meth:`TaskHandle.sleep`。一个纯 ``time.sleep(60)`` 或一次
DLL 调用**无法被打断**，只能被放弃。

三个能力
--------

======================  ==========================================  ==========================
要什么                   调什么                                      返回
======================  ==========================================  ==========================
起一个线程跑并带回结果    ``runner.start(func, on_done)``              :class:`TaskHandle`
还剩几个在跑             ``runner.count`` / ``count()``               ``int``
立刻叫停全部             ``runner.cancel_all(wait)``                  未停下的个数 ``int``
======================  ==========================================  ==========================

``on_done`` 跑在哪个线程
------------------------

**默认送回 GUI 线程**（``dispatch='auto'``）。这一条是为界面写的：绝大多数完成回调要做的
事就是回写控件，而控件只能在 GUI 线程碰。于是

.. code-block:: python

    handle = run(load_files, lambda: self.btn.setEnabled(True))   # on_done 在 GUI 线程跑

判定规则只有两条：

1. 进程里**有** ``QCoreApplication``（即界面已启动）⇒ 排队送回 GUI 线程的事件循环；
2. **没有**（无头模式、纯脚本、``--no-gui``）⇒ 就在工作线程里**就地执行**。

⚠️ 注意第 1 条与「谁调的 ``start``」**无关**：即使从后台线程发起任务，完成回调也回到
GUI 线程 —— 因为「回写界面」才是这个回调的典型用途。要它留在自己的工作线程里？
显式传 ``dispatch='inline'``。

⚠️ **``on_done`` 是「线程结束」回调，不是「成功」回调**：任务抛异常、任务被取消，
只要它**真的结束了**，``on_done`` 就会被调用一次。要区分，看 ``handle.error`` /
``handle.cancelled`` / ``handle.result``。这样设计是因为最常见的用法是「恢复按钮状态」，
那件事在失败时同样必须做。

⚠️ 因此 ``on_done`` **允许**用命名形参接收句柄，省掉「回调里引用外层 ``h``」的那个坑
（``h = run(...)`` 还没赋值、回调就被调用了 —— 极短任务 + 内联派发时**理论上会**发生）：

.. code-block:: python

    def on_loaded(task):                    # 形参名 handle/task/token/job ⇒ 收到句柄
        btn.setEnabled(True)
        if task.error is not None:
            gui.status(f'失败: {task.error}')

    run(partial(load, paths), on_loaded)

⚠️ **被放弃的线程不会触发 ``on_done``**（它还没结束，晚些收工时你已经不再期望回调）；
``cancel_all`` 的返回值告诉你有几个属于这种情况。

与既有机制的分工
----------------

====================  ==============================================================
机制                   定位（**别混用**）
====================  ==============================================================
``Console``           **仍是长任务唯一槽位**（仿真、批量计算这类要能被暂停/停止的工作）。
                      本模块是「多个短/中任务并发」，**不是它的替代品**：不接管工具栏
                      的「暂停/继续/停止」（那些只对 ``gui.break_point()`` 生效）、
                      不参与 ``Console.thread`` 的单槽位记账，**两者互不知情**。
                      反过来，并发短任务**不能**塞给 ``gui.start``（忙时直接丢弃）。
                      判据：需要暂停/停止 ⇒ ``gui.start``；并行做完再回写 ⇒ 本模块。
                      权威说法见 ``zmlx/ui/AGENTS.md`` §6.3 与 §6.8。
``TaskProc``          「稍后在 GUI 线程跑一下」，异步、无结果。
``GuiApi``            「现在就在 GUI 线程跑一下」，同步、有返回值与异常。**绝不要**
                      在工作线程里拿着锁调它（死锁）。
``BackgroundTask``    **一个**最低优先级的循环，反复执行同一个回调（轮询型，如刷新）。
                      本模块是「一次性任务」，跑完即收。
====================  ==============================================================

用法
----

.. code-block:: python

    from functools import partial

    from zmlx.ui.utils.thread_runner import run, count, cancel_all, current

    def load(paths, task):           # 形参名在 task/handle/token/job 且**必选** ⇒ 自动注入
        data = []
        for path in paths:
            task.check()             # 已被取消 ⇒ 抛 TaskCancelled，直接跳出
            if not task.sleep(0.01):  # 可被打断的睡眠；返回 False 表示期间被取消
                return None
            data.append(read(path))
        return data

    def work():                      # 零参也行，改用 current() 拿令牌
        for path in paths:
            current().check()
            ...

    btn.setEnabled(False)                                        # 任务期间禁用
    handle = run(partial(load, paths), lambda: btn.setEnabled(True))   # 回调在 GUI 线程
    print(count())                                               # 还剩几个在跑
    cancel_all(wait=0.2)                                         # 立刻叫停，最多等 0.2 秒

⚠️ **只有形参名在 ``{'task', 'handle', 'token', 'job'}`` 里、且没有默认值的**才会被
注入令牌。刻意不做「只要有一个必选形参就注入」—— 那会把 ``def work(path)`` 的 ``path``
悄悄换成一个 TaskHandle。

⚠️ 任务体里**不许直接碰控件**。``on_done`` 会自动回投；任务体本身要更新界面，请用
``gui.call`` / ``gui.add_task``（见 ``zmlx/ui/AGENTS.md`` §6.4）。

限制
----

- **不能用 ``with`` 复用同一个 runner 跑「一次性任务集」后再起**：``close()`` 之后
  ``start`` 会抛 ``RuntimeError``（这是刻意的，避免「静默丢弃任务」）。
- **``on_done`` 里的异常不会传播**（已经在线程收尾路径上），只打印堆栈到 stderr。
- **默认不限制并发数**（``max_threads=None``）。要限就在构造时给，超限时 ``start``
  **抛 ``RuntimeError``**（不是排队、更不是静默丢弃 —— 静默丢弃正是本仓
  ``gui.start`` 被诟病的那个行为）。
- **本模块不需要 Qt**：只在需要「回投 GUI 线程」时才惰性导入 ``zmlx.ui.pyqt``。
  因此在无头模式（``--no-gui``）下也能导入使用，只是 ``on_done`` 就地执行。

Created by DeepSeek, 2026-10-20
"""

from __future__ import annotations

import functools
import inspect
import threading
import time
import traceback
from typing import Any, Callable, Optional, Set, Tuple

__all__ = [
    'TaskCancelled',
    'TaskHandle',
    'ThreadRunner',
    'current',
    'run',
    'count',
    'cancel_all',
    'wait_all',
]

#: 允许自动注入 :class:`TaskHandle` 的形参名（小写比较）。
_HANDLE_NAMES = frozenset({'task', 'handle', 'token', 'job'})

#: 当前线程正在执行的任务（由工作线程写入，见 :func:`current`）。
_local = threading.local()

#: GUI 线程上的信号泵与它的创建锁（全局唯一，见 :func:`_gui_pump`）。
_pump_lock = threading.Lock()
_pump = None


class TaskCancelled(Exception):
    """任务被取消.

    由 :meth:`TaskHandle.check` 抛出。任务体**可以**捕获它做清理然后 ``return``；
    也可以放任它冒出 —— :class:`ThreadRunner` 会把它记成「被取消」，**不算错误**
    （``handle.error`` 保持 ``None``）。
    """


class TaskHandle:
    """单个任务的句柄：取消令牌 + 结果容器.

    由 :meth:`ThreadRunner.start` 创建并返回，**不要自己实例化**。

    它同时是两样东西：

    1. **取消令牌** —— 任务体通过 :attr:`cancelled` / :meth:`check` / :meth:`sleep`
       感知「有人要求我停下」；
    2. **结果容器** —— 线程结束后 :attr:`result` / :attr:`error` / :attr:`elapsed`
       才有意义（由 :attr:`done` 保证可见性）。

    ⚠️ 属性分布：``cancelled`` / ``done`` / ``elapsed`` 在任何线程随时可读；
    ``result`` / ``error`` **必须先确认 ``done`` 为真**再读（之前读到的可能是半成品）。
    """

    def __init__(self, func: Callable, on_done: Optional[Callable] = None, *,
                 name: Optional[str] = None, inject: bool = False,
                 inject_done: bool = False):
        self._func = func
        self._on_done = on_done
        self._inject = inject
        self._inject_done = inject_done
        #: 任务名（用于线程名与日志；不要求唯一）
        self.name = name
        self._cancel = threading.Event()
        self._done = threading.Event()
        self._result = None
        self._error = None
        self._on_done_error = None
        self._cancelled_by_task = False
        self._abandoned = False
        self._pump = None
        self._thread = None
        self._t0 = time.monotonic()
        self._t1 = None

    # ------------------------------------------------------------------ 只读状态
    @property
    def cancelled(self) -> bool:
        """是否已被要求取消（含任务自己因取消而 ``return`` 的情况）。"""
        return self._cancel.is_set() or self._cancelled_by_task

    @property
    def abandoned(self) -> bool:
        """是否已被「放弃」（取消后超出等待窗口仍未结束 —— 它的 ``on_done`` 不会再被调用）。"""
        return self._abandoned

    @property
    def done(self) -> bool:
        """线程体是否已经结束（正常返回 / 抛异常 / 被取消，都算结束）.

        ⚠️ ``done`` 为真**不代表 ``on_done`` 已执行完**：``on_done`` 是在线程收尾时
        **派发**的，回投 GUI 线程时它还在队列里排队。要等它跑完，请在 ``on_done``
        自己里置一个事件/标志，或轮询你自己的状态。
        """
        return self._done.is_set()

    @property
    def running(self) -> bool:
        """线程是否还在跑（= ``not done``）。"""
        return not self._done.is_set()

    @property
    def result(self) -> Any:
        """任务返回值；任务未成功返回时为 ``None``。"""
        return self._result

    @property
    def error(self) -> Optional[BaseException]:
        """任务抛出的异常；被取消或正常返回时为 ``None``。"""
        return self._error

    @property
    def on_done_error(self) -> Optional[BaseException]:
        """完成回调自己抛出的异常（只记录，不传播）；没有则为 ``None``。"""
        return self._on_done_error

    @property
    def elapsed(self) -> float:
        """已耗时（秒）：未结束时是「到此刻」，结束后是「总耗时」。"""
        t1 = self._t1
        return (t1 if t1 is not None else time.monotonic()) - self._t0

    @property
    def thread_name(self) -> Optional[str]:
        """底层线程名（未启动时为 ``None``）。"""
        return self._thread.name if self._thread is not None else None

    # ------------------------------------------------------------------ 协作式取消
    def check(self):
        """若已被要求取消，抛 :class:`TaskCancelled`；否则立即返回.

        这是**最省事**的轮询写法：抛出去就行，:class:`ThreadRunner` 会把它记成
        「被取消」而**不算错误**。

        Raises:
            TaskCancelled: 已被要求取消。
        """
        if self._cancel.is_set():
            raise TaskCancelled(f'任务已被取消: {self.name or self._func!r}')

    def sleep(self, seconds: float) -> bool:
        """可被取消打断的睡眠（替代 ``time.sleep``）。

        Args:
            seconds: 睡眠秒数（``<= 0`` 时立即返回）。

        Returns:
            bool: True 表示睡满了；False 表示**期间被取消**（调用方一般应 ``return``）。
        """
        if seconds <= 0:
            return not self._cancel.is_set()
        return not self._cancel.wait(seconds)  # wait() 返回 True 表示「等到取消」

    def wait(self, timeout: Optional[float] = None) -> bool:
        """等待线程结束.

        Args:
            timeout: 最长等待秒数；``None`` 表示一直等。

        Returns:
            bool: True 表示已结束。
        """
        return self._done.wait(timeout)

    def cancel(self, wait: float = 0.0) -> bool:
        """只取消这一个任务.

        Args:
            wait: 取消后最多再等几秒（``0`` 表示不等）。

        Returns:
            bool: True 表示它已经结束（可能本来就结束了）。
        """
        self._request_cancel()
        if not self._done.is_set():
            self._done.wait(max(wait, 0.0))
            if not self._done.is_set():
                self._abandoned = True
        return self._done.is_set()

    def _request_cancel(self):
        """置取消位（幂等）。"""
        self._cancel.set()

    def __repr__(self):
        state = 'done' if self.done else ('abandoned' if self.abandoned else 'running')
        if self.error is not None:
            state += f', error={self.error!r}'
        elif self.cancelled:
            state += ', cancelled'
        return f'<TaskHandle {self.name or "task"} {state} elapsed={self.elapsed:.3f}s>'


class ThreadRunner:
    """自动线程执行器：每个任务一条线程，可并发、可统计、可叫停.

    线程用 **stdlib ``threading.Thread`` 且 ``daemon=True``**，而不是 ``QThread``。
    三条理由：

    1. **不会因为「对象被回收」把进程搞崩** —— ``QThread`` 在运行中被析构是硬崩，
       必须靠模块级列表持引用才能避免；daemon 线程没有这个约束，句柄被丢弃也不影响。
    2. **不需要事件循环** —— 我们只做「跑函数」，不用 ``QThread`` 的信号机制。
    3. **无头模式可用** —— 不依赖 Qt，``--no-gui`` 下照常工作。

    Args:
        name: 线程名前缀（实际线程名形如 ``<name>-12``）。
        max_threads: 并发上限；``None``（默认）表示不限制。超限时 :meth:`start`
            **抛** ``RuntimeError``（不排队、不静默丢弃）。
        dispatch: ``on_done`` 的执行线程。``'auto'``（默认）有 ``QCoreApplication`` 就送回
            GUI 线程、否则就地执行；``'inline'`` 一律在工作线程就地执行；``'gui'`` 强制
            送回 GUI 线程，没有界面就抛 ``RuntimeError``。

    Raises:
        ValueError: ``max_threads`` 不为正（且不为 ``None``），或 ``dispatch`` 取值非法。
    """

    def __init__(self, *, name: str = 'zml-task',
                 max_threads: Optional[int] = None, dispatch: str = 'auto'):
        if max_threads is not None and max_threads <= 0:
            raise ValueError(f'max_threads 必须为正（或 None），收到: {max_threads!r}')
        if dispatch not in ('auto', 'inline', 'gui'):
            raise ValueError(f"dispatch 只能是 'auto' / 'inline' / 'gui'，收到: {dispatch!r}")
        self.name = name
        self.max_threads = max_threads
        self.dispatch = dispatch
        self._lock = threading.RLock()
        self._active = set()      # type: Set[TaskHandle]
        self._closed = False
        self._seq = 0

    # ------------------------------------------------------------------ 查询
    @property
    def count(self) -> int:
        """当前**还在跑**的任务（= 线程）个数。"""
        with self._lock:
            return len(self._active)

    def handles(self) -> Tuple[TaskHandle, ...]:
        """当前还在跑的句柄快照（按启动顺序）。"""
        with self._lock:
            return tuple(sorted(self._active, key=lambda h: h._t0))

    def is_running(self) -> bool:
        """是否有任务在跑（``count > 0``）。"""
        return self.count > 0

    # ------------------------------------------------------------------ 启动
    def start(self, func: Callable, on_done: Optional[Callable] = None, *,
              name: Optional[str] = None, dispatch: Optional[str] = None) -> TaskHandle:
        """起一条新线程执行 ``func``.

        Args:
            func: 任务体。签名可以是零参；若有一个**必选形参**且其名为
                ``task`` / ``handle`` / ``token`` / ``job``，自动注入本次的
                :class:`TaskHandle`。
            on_done: 完成回调。任务真正结束时被调用一次（成功、抛异常、被取消都算；
                被**放弃**的不算）。签名可以是零参，也可以把必选形参命名为
                ``task`` / ``handle`` / ``token`` / ``job`` 来接收本次的
                :class:`TaskHandle`（结果与状态都在里面，不必在闭包里引用外层变量）。
                执行线程见 ``dispatch``。
            name: 任务名（只用于线程名与日志）。
            dispatch: 覆盖本 runner 的默认派发方式（``'auto'`` / ``'inline'`` / ``'gui'``）。

        Returns:
            TaskHandle: 句柄（取消令牌 + 结果容器）。

        Raises:
            TypeError: ``func`` 或 ``on_done`` 不可调用。
            RuntimeError: runner 已 ``close``；或并发已达 ``max_threads``；或
                ``dispatch='gui'`` 但进程里没有界面（无 ``QCoreApplication``）。
        """
        if not callable(func):
            raise TypeError(f'func 必须可调用，收到: {func!r}')
        if on_done is not None and not callable(on_done):
            raise TypeError(f'on_done 必须可调用或 None，收到: {on_done!r}')

        mode = self.dispatch if dispatch is None else dispatch
        if mode not in ('auto', 'inline', 'gui'):
            raise ValueError(f"dispatch 只能是 'auto' / 'inline' / 'gui'，收到: {mode!r}")
        pump = None
        if mode != 'inline':
            pump = _gui_pump()
            if pump is None and mode == 'gui':
                raise RuntimeError(
                    "dispatch='gui' 需要已启动的界面（QCoreApplication + 事件循环）；"
                    "无头模式请用 'inline' 或 'auto'。"
                )

        handle = TaskHandle(func, on_done, name=name,
                            inject=_accepts_handle(func),
                            inject_done=_accepts_handle(on_done))
        handle._pump = pump

        with self._lock:
            if self._closed:
                raise RuntimeError(f'{self!r} 已关闭，不能再启动任务')
            if self.max_threads is not None and len(self._active) >= self.max_threads:
                raise RuntimeError(
                    f'并发已达上限 {self.max_threads}（当前 {len(self._active)} 个任务在跑）；'
                    '请先等待或取消，或调大 max_threads。'
                )
            self._seq += 1
            thread = threading.Thread(
                target=self._run_handle, args=(handle,),
                name=f'{self.name}-{self._seq}', daemon=True,
            )
            handle._thread = thread
            self._active.add(handle)
            thread.start()
        return handle

    # ------------------------------------------------------------------ 收尾
    def cancel_all(self, wait: float = 0.0) -> int:
        """叫停全部任务.

        先给所有在跑的任务置取消位，然后最多等 ``wait`` 秒。

        Args:
            wait: 最多等待秒数。``0``（默认）表示**立即返回**、一个都不等 ——
                这正是「不卡界面」要求的语义。

        Returns:
            int: **未能停下来**的任务个数（它们已被标记为 :attr:`TaskHandle.abandoned`，
            之后收工时不会再触发 ``on_done``）。``0`` 表示全部已结束。

        ⚠️ 「没能停下来」**不一定是 bug**：卡在阻塞调用（DLL、IO、``time.sleep``）里的
        任务无法被中断，只能等它自己走完。它们是 daemon 线程，不会阻止进程退出。
        """
        with self._lock:
            handles = [h for h in self._active if not h.done]
        for h in handles:
            h._request_cancel()
        if handles and wait > 0:
            deadline = time.monotonic() + wait
            for h in handles:
                h.wait(max(deadline - time.monotonic(), 0.0))
        alive = []
        for h in handles:
            if h.done:
                continue
            h._abandoned = True     # 超出窗口：放弃，且不再触发 on_done
            alive.append(h)
        return len(alive)

    def wait_all(self, timeout: Optional[float] = None) -> bool:
        """等待所有任务结束（**不**取消）.

        Args:
            timeout: 最长等待秒数；``None`` 表示一直等。

        Returns:
            bool: True 表示全部已结束。
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        for h in self.handles():
            left = None if deadline is None else max(deadline - time.monotonic(), 0.0)
            h.wait(left)
            if deadline is not None and time.monotonic() >= deadline:
                break
        return self.count == 0

    def close(self, wait: float = 0.0):
        """关闭：取消全部任务，此后 :meth:`start` 抛 ``RuntimeError``.

        Args:
            wait: 与 :meth:`cancel_all` 同义。
        """
        with self._lock:
            self._closed = True
        self.cancel_all(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close(wait=0.0)
        return False

    def __repr__(self):
        return f'<ThreadRunner {self.name} count={self.count} closed={self._closed}>'

    # ------------------------------------------------------------------ 线程体
    def _run_handle(self, handle: TaskHandle):
        """工作线程主体：执行任务、记账、派发完成回调（**可能不在本线程执行**）。"""
        _local.handle = handle
        try:
            try:
                res = _invoke(handle)
            except TaskCancelled:
                handle._cancelled_by_task = True
            except BaseException as err:            # noqa: BLE001 —— 兜住一切，否则线索断在这里
                handle._error = err
                if handle._on_done is None:
                    traceback.print_exc()
            else:
                handle._result = res
        finally:
            handle._t1 = time.monotonic()
            handle._done.set()                      # 先置位：之后 result/error 才算可读
            with self._lock:
                self._active.discard(handle)
            _local.handle = None
            self._finish(handle)

    def _finish(self, handle: TaskHandle):
        """派发 ``on_done``（每个真正结束的任务恰好一次，被放弃的跳过）。"""
        on_done = handle._on_done
        if on_done is None or handle._abandoned:
            return
        call = functools.partial(_call_quietly, handle)
        pump = handle._pump
        if pump is None:
            call()
            return
        try:
            pump.sig.emit(call)      # 跨线程 ⇒ Qt 自动排队到 GUI 线程的事件循环
        except Exception:            # noqa: BLE001
            # Qt 对象已销毁（正在退出）：此时再回投只会碰已死的控件，直接丢弃。
            pass


def _make_pump():
    """在当前（GUI）线程上造一个信号泵；没有 Qt / 没有 app / 不是 GUI 线程时返回 ``None``.

    信号泵的做法：``QObject`` 建在 GUI 线程、``pyqtSignal(object)`` 连到自己的槽。任何
    线程 ``emit`` 一个 callable，Qt 的 ``AutoConnection`` 判定为跨线程 ⇒ 排队到 GUI 线程
    的事件循环里执行。**不需要**调用方持有任何 ``QObject``，也不用 ``QMetaObject``。

    ⚠️ 只在**当前线程就是 GUI 线程**时才造：非 GUI 线程未必跑事件循环，回投进去的回调
    可能永远不执行（那比「就地执行」更糟 —— 静默丢失）。
    """
    try:
        from zmlx.ui.pyqt import QtCore
    except Exception:       # pragma: no cover —— pyqt 模块本身设计成可导入，这里只是双保险
        return None
    if QtCore is None or not hasattr(QtCore, 'QCoreApplication'):
        return None
    app = QtCore.QCoreApplication.instance()
    if app is None:
        return None
    if QtCore.QThread.currentThread() is not app.thread():
        return None     # 当前线程不是 GUI 线程：它未必有事件循环，回投可能永远不执行

    class Pump(QtCore.QObject):
        sig = QtCore.pyqtSignal(object)

        def __init__(self):
            super().__init__()
            self.sig.connect(self._run)

        def _run(self, fn):
            # 槽里再兜一次：派发路径上抛异常会污染 Qt 的事件循环
            try:
                fn()
            except BaseException:       # noqa: BLE001
                traceback.print_exc()

    pump = Pump()
    pump._app = app        # 记下它属于哪个 QApplication，供 _pump_alive 校验
    return pump


def _pump_alive(pump) -> bool:
    """信号泵是否仍然可用（它所属的那个 ``QApplication`` 还没被销毁/替换）."""
    try:
        from zmlx.ui.pyqt import QtCore
    except Exception:       # pragma: no cover
        return False
    if QtCore is None:
        return False
    return QtCore.QCoreApplication.instance() is getattr(pump, '_app', None)


def _gui_pump():
    """取 GUI 线程的信号泵（惰性创建、全局唯一）；不可用时返回 ``None``.

    ⚠️ 会校验「泵所属的 ``QApplication`` 是否还是当前那个」：界面被销毁再重建（测试里
    常见）之后，旧泵再 ``emit`` 会静默丢失回调 —— 那是「按钮永远不恢复」的隐蔽故障，
    所以这里宁可重建。
    """
    global _pump
    if _pump is not None and _pump_alive(_pump):
        return _pump
    with _pump_lock:
        if _pump is not None and _pump_alive(_pump):
            return _pump
        _pump = _make_pump()
        return _pump


def _invoke(handle: TaskHandle):
    """调用任务体，按需注入句柄."""
    if handle._inject:
        return handle._func(handle)
    return handle._func()


def _call_quietly(handle: TaskHandle):
    """执行 ``handle`` 的 ``on_done``；异常只打印堆栈，绝不向外传播（已在线程收尾路径上）."""
    on_done = handle._on_done
    if on_done is None:
        return
    try:
        if handle._inject_done:
            on_done(handle)
        else:
            on_done()
    except BaseException as err:        # noqa: BLE001
        handle._on_done_error = err     # 便于测试与诊断
        traceback.print_exc()


def _accepts_handle(func: Callable) -> bool:
    """``func`` 是否需要注入 :class:`TaskHandle`.

    判据（全部满足才注入）：有一个**必选**位置形参，且其名为 ``task`` / ``handle`` /
    ``token`` / ``job``。刻意保守 —— 「有必选形参就注入」会把 ``def work(path)`` 的
    ``path`` 悄悄换掉。

    ⚠️ 内建函数、``functools.partial`` 等取不到签名的对象一律按「不注入」处理。
    """
    try:
        params = list(inspect.signature(func).parameters.values())
    except (TypeError, ValueError):
        return False
    for p in params:
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty:
            return p.name.lower() in _HANDLE_NAMES
    return False


# ---------------------------------------------------------------------- 模块级便捷 API
#: 默认共享的 runner（模块级单例）。需要独立并发上限/派发策略时自己 ``ThreadRunner()``。
_shared_runner = ThreadRunner(name='zml-task')


def run(func: Callable, on_done: Optional[Callable] = None, *,
        name: Optional[str] = None, dispatch: Optional[str] = None) -> TaskHandle:
    """用共享 runner 起一个任务（参数同 :meth:`ThreadRunner.start`）。"""
    return _shared_runner.start(func, on_done, name=name, dispatch=dispatch)


def count() -> int:
    """共享 runner 里还有几个任务（线程）在跑。"""
    return _shared_runner.count


def cancel_all(wait: float = 0.0) -> int:
    """叫停共享 runner 的全部任务；返回未能停下的个数。"""
    return _shared_runner.cancel_all(wait=wait)


def wait_all(timeout: Optional[float] = None) -> bool:
    """等共享 runner 的全部任务结束（不取消）。"""
    return _shared_runner.wait_all(timeout=timeout)


def current() -> Optional[TaskHandle]:
    """当前线程正在执行的任务句柄；不在任务体里时返回 ``None``.

    用途有两个：① 零参任务体拿取消令牌；② 任务体里查看自己的名字/耗时。
    """
    return getattr(_local, 'handle', None)


# ---------------------------------------------------------------------- 自测
def _self_test():
    """纯 stdlib 自测（无需 Qt）：``python -m zmlx.ui.utils.thread_runner``."""
    ok = [0]

    def wait_until(cond, timeout=3.0):
        """轮询等待条件成立（完成回调可能在线程收尾后极短窗口内才落定）。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cond():
                return True
            time.sleep(0.005)
        return cond()

    def check(cond, label):
        if not cond:
            raise AssertionError(f'FAILED: {label}')
        ok[0] += 1
        print(f'  ok - {label}')

    print('[1] 基本执行与完成回调')
    runner = ThreadRunner(name='t1')
    box = []
    h = runner.start(lambda: (box.append('ran'), 'res')[1], lambda: box.append('done'))
    check(h.wait(5.0), '任务结束')
    check(wait_until(lambda: box == ['ran', 'done']), '任务体先于完成回调执行')
    check(h.result == 'res' and h.error is None, '返回值被记录')
    check(runner.count == 0, '结束后 count 归零')

    print('[2] 并发（无上限）')
    runner = ThreadRunner(name='t2')
    peak = []
    gate = threading.Event()

    def blocker():
        peak.append(runner.count)
        gate.wait(5.0)

    hs = [runner.start(blocker) for _ in range(8)]
    time.sleep(0.3)
    check(runner.count == 8, '8 个任务同时存活')
    check(max(peak) >= 8, '峰值并发达到 8')
    gate.set()
    check(runner.wait_all(5.0), '全部结束')

    print('[3] 并发上限')
    runner = ThreadRunner(name='t3', max_threads=2)
    gate = threading.Event()
    runner.start(lambda: gate.wait(5.0))
    runner.start(lambda: gate.wait(5.0))
    try:
        runner.start(lambda: None)
    except RuntimeError as err:
        check('上限' in str(err), '超限抛 RuntimeError')
    else:
        raise AssertionError('FAILED: 超限没有抛异常')
    gate.set()
    runner.wait_all(5.0)

    print('[4] 异常被记录，完成回调仍执行')
    runner = ThreadRunner(name='t4')
    done = []
    def boom():
        raise ValueError('x')
    h = runner.start(boom, lambda: done.append(1))
    check(h.wait(5.0), '异常任务也结束')
    check(isinstance(h.error, ValueError), 'error 被记录')
    check(h.result is None, 'error 时 result 为 None')
    check(wait_until(lambda: done == [1]), '异常时完成回调仍执行一次')

    print('[5] 取消：协作式（立即返回 + 计数）')
    runner = ThreadRunner(name='t5')
    done = []
    def loop(task):
        while True:
            task.check()
            task.sleep(0.005)
    hs = [runner.start(loop, lambda: done.append(1)) for _ in range(4)]
    time.sleep(0.1)
    check(runner.count == 4, '4 个任务在跑')
    left = runner.cancel_all(wait=2.0)
    check(left == 0, '协作式任务全部停下')
    check(all(h.cancelled and h.done for h in hs), '句柄标记为已取消且已结束')
    check(all(h.error is None for h in hs), '取消不算错误')
    check(wait_until(lambda: len(done) == 4), '结束的（被取消的）任务仍触发完成回调以便收拾界面')

    print('[6] 放弃：不合作的阻塞任务')
    runner = ThreadRunner(name='t6')
    fired = []
    h = runner.start(lambda: time.sleep(0.6), lambda: fired.append(1))
    left = runner.cancel_all(wait=0.05)
    check(left == 1, '阻塞任务无法中断 ⇒ 报告 1 个未停下')
    check(h.abandoned and not h.done, '句柄被标记为放弃')
    h.wait(3.0)
    time.sleep(0.05)        # 给它足够时间去「错误地」触发回调
    check(h.done and not fired, '放弃的线程收工后不再触发完成回调')

    print('[7] current() 与注入')
    runner = ThreadRunner(name='t7')
    seen = []
    def zero_arg():
        seen.append(('current', current() is not None))
        return 1
    def with_token(task):
        seen.append(('injected', isinstance(task, TaskHandle)))
        return 2
    def with_path(path):          # 必选形参但名字不在白名单 ⇒ 不注入（这里会 TypeError）
        return path
    runner.start(zero_arg).wait(5.0)
    runner.start(with_token).wait(5.0)
    h = runner.start(with_path)
    h.wait(5.0)
    check(seen[0][0] == 'current' and seen[0][1], '零参任务里 current() 可用')
    check(seen[1][0] == 'injected' and seen[1][1], '命名形参被注入句柄')
    check(isinstance(h.error, TypeError), '非白名单形参不被注入（按零参调用）')
    check(current() is None, '任务外 current() 为 None')

    echo = []
    runner.start(lambda: 7, lambda task: echo.append((task.result, task.error))).wait(5.0)
    check(wait_until(lambda: echo == [(7, None)]), '完成回调也可用命名形参收到句柄')

    print('[8] 完成回调抛异常不影响其它')
    runner = ThreadRunner(name='t8')
    h = runner.start(lambda: 1, lambda: (_ for _ in ()).throw(RuntimeError('cb')))
    h.wait(5.0)
    check(wait_until(lambda: isinstance(h.on_done_error, RuntimeError)), '回调异常被记录、不外抛')
    check(h.done, '回调异常后任务状态正常')
    check(runner.start(lambda: 2).wait(5.0), '后续任务照常执行')

    print('[9] close 后拒绝启动')
    runner = ThreadRunner(name='t9')
    runner.close()
    try:
        runner.start(lambda: None)
    except RuntimeError:
        check(True, 'close 后 start 抛 RuntimeError')
    else:
        raise AssertionError('FAILED: close 后仍可启动')

    print('[10] 无界面时 dispatch=gui 明确报错，auto 则可就地执行')
    runner = ThreadRunner(name='t10')
    if _gui_pump() is None:
        try:
            runner.start(lambda: None, dispatch='gui')
        except RuntimeError:
            check(True, "无界面时 dispatch='gui' 抛 RuntimeError")
        else:
            raise AssertionError("FAILED: 无界面时 dispatch='gui' 没有报错")
    else:
        print('  skip - 当前进程已启动界面')
    check(runner.start(lambda: 1, dispatch='auto').wait(5.0), "auto 在无界面时就地执行")

    print('[11] 反复启停不泄漏线程')
    runner = ThreadRunner(name='t11')
    base = threading.active_count()
    for _ in range(200):
        runner.start(lambda: None).wait(5.0)
    check(runner.count == 0, '200 次后 count 归零')
    check(threading.active_count() <= base + 1, '线程数回到基线（无泄漏）')

    print(f'\nALL PASSED ({ok[0]} checks)')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(_self_test())

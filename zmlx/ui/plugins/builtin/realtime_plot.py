# ** name = '实时绘图'
# ** desc = '把绘图从计算线程里挪出去：计算线程只调 gui.rtp_push 压数据，独立的泵线程按标签限频重绘'
"""
实时绘图队列：把「画图」从计算线程里挪出去
==========================================

一句话
------
计算线程里调 ``gui.rtp_push(kernel, data, caption='压力')`` 只是**把一帧塞进队列**
（微秒级、不等界面）；真正调用 matplotlib 的是本插件起的**一个常驻泵线程**，
它按标签（= 标签页标题）分别限频、分别退避，再派发到 GUI 线程绘制。

数据流
------

::

   计算线程                        泵线程（常驻，daemon）            GUI 线程
   ---------                       ---------------------            --------
   gui.rtp_push(k, d, '压力')
        │  压入 Queue（O(1)）
        ├──────────────────────────►  轮询各标签的队列
        │                               │ 弹出一帧（FIFO）
        │                               │ 该标签的绘制间隔已到？
        │                               ├── gui.plot(k, d, caption) ──► 建/复用标签页
        │                               │                              跑 k(figure, d)
        │                               │                              canvas.draw()
        │                               ◄────── 阻塞到画完 ─────────────┘
        │                               │ 记下「本标签下次允许绘制的时刻」
   继续算                            （别的标签照常轮询）

   计算线程**从不等待**绘图（``rtp_push`` 被登记成 ``is_direct``，见 §「为什么不派发」）。

四条命令（都带 ``rtp_`` 前缀 = **R**eal**T**ime**P**lot）
---------------------------------------------------------

* ``gui.rtp_push(kernel, data, caption=None, ...)`` —— 压一帧（主接口），返回该标签的待绘帧数；
* ``gui.rtp_queue_n(caption=None)`` —— 尚未绘制的帧数（``None`` = 所有标签求和）；
* ``gui.rtp_queue_clear(caption=None)`` —— 丢弃未绘制的帧（中止一段数据流时用）；
* ``gui.rtp_queue_stat(caption=None)`` —— 队列 / 节流的统计（排查「某帧为什么没画」）。

外加一条**不属于队列**的命令：``gui.show_rtp_panel()`` —— 打开（或切到）右侧的
「实时绘图控制面板」（菜单「显示 → 实时绘图控制面板」也是它）。

⚠️ **为什么必须带前缀**：``gui`` 的命令名是**全局命名空间** —— ``MainWindow`` 的公开方法
会自动变成 ``gui.xxx``，各插件也往这里注册，而**后注册者静默顶掉先注册者**。
``push_plot`` / ``plot_queue_n`` 这种通用名字迟早会撞上别的东西（撞了就是别人的方法
被悄悄换掉，或者自己的被换掉，两种都难查）。``rtp_`` 三个字母标清归属，顺带让
``grep rtp_`` 一次就能捞到本插件的全部入口。

控制面板（菜单「显示 → 实时绘图控制面板」）
--------------------------------------------

右侧标签页里一块面板，200 ms 刷一次（**只在可见时刷**）：状态行（线程在跑 / 目标与实测
帧率 / 标签数 / 待绘·累计绘制·丢弃）+ 三个旋钮（目标帧率、空闲休眠、积压上限）+ 三个
按钮（重启线程、清空队列、演示）+ 每标签统计表 + 「最近绘制了哪些帧」。

三个旋钮**直接改 :data:`_pump` 的字段**（``min_draw_interval`` / ``idle_sleep`` /
``max_pending``），泵线程每轮现读 ⇒ 改完最迟一个轮询周期生效，不需要加锁、
也不涉及跨线程碰 Qt。演示按钮就是 :func:`show_demo`，**不再单独占一条菜单项**。

三个节流数字（**每个标签各算各的**）
------------------------------------

======================  ==========  ==================================================
常量                     默认         含义
======================  ==========  ==================================================
``MIN_DRAW_INTERVAL``   0.1 s       同一标签**两次绘制之间**至少隔这么久（上限约 10 帧/秒）
``POLL_MIN``            0.02 s      队列有数据时的轮询起点
``POLL_MAX``            0.5 s       队列长期为空时退避到的上限（省 CPU；有新数据立刻唤醒）
======================  ==========  ==================================================

「退避」与「唤醒」是一对：队列空 ⇒ 轮询间隔翻倍直到 ``POLL_MAX``；**一旦有新数据压入**，
:func:`rtp_push` 当场把该标签的间隔重置回 ``POLL_MIN`` 并把下次轮询时刻清零 —— 所以
退避只惩罚「长时间没数据」的标签，不会让新数据多等 0.5 s。

回调用法（和 ``gui.plot`` 完全一致）
------------------------------------

::

   def kernel(figure, data):          # data 就是 push 进来的那个对象
       ax = figure.add_subplot(111)
       ax.plot(data['t'], data['p'])

   gui.rtp_push(kernel, {'t': ts, 'p': ps}, caption='压力')

⚠️ **默认 ``clear=True``**：每一帧都是「一整张新图」。这符合「快照式」实时绘图
（数据本身就是全量历史）的习惯，也不会让上一帧的线残留在图上。若要**保留坐标轴状态**
（缩放、图例、多条线各自追加），传 ``clear=False``，回调里自己判::

   def kernel(figure, data):
       ax = figure.axes[0] if figure.axes else figure.add_subplot(111)
       if figure.axes:
           ax.cla()                    # 自己决定怎么复用这个轴
       ax.plot(data['t'], data['p'])

⚠️ **``data`` 必须是快照**。队列里放的是**引用**，泵线程可能在你继续改它之后才画 ——
如果 ``data`` 是仍在被就地修改的列表/数组，画出来的是「画的那一刻的值」，不是「压入
那一刻的值」。压之前 ``list(...)`` / ``numpy`` 切片一下，或者每帧新建一个 dict。

积压与丢弃
----------

生产快于绘制时，队列会涨。每个标签有 ``max_pending``（默认 8 帧）上限，超出**丢最旧**的
（实时绘图要的是「最新」，不是「完整」）。丢弃数在 :func:`rtp_queue_stat` 里可见。
想自己控制就传 ``max_pending=None``？—— 那只是「不改动该标签当前的上限」，
把上限调大请传具体数字。

边界
----

* **单泵线程串行绘制**：两个标签同时有数据时是排队画的，不会并行（GUI 线程本来也只有
  一个）。所以「N 个标签各 10 帧/秒」在重图时会掉帧 —— 掉的是队列里的旧帧，符合预期。
* **GUI 线程仍是瓶颈**：泵线程把活干完了，但 ``canvas.draw()`` 只能在 GUI 线程跑。
  本插件消除的是**计算线程的等待**，不是 GUI 线程的耗时。
* 无界面（headless）时 ``gui.rtp_push`` 什么都不做（命令没有接收方），返回值规则见函数
  文档；泵线程本身也只由插件加载时启动，headless 下插件不会加载。
* 关闭窗口后泵线程可能永远卡在「等 GUI 线程取走命令」上 —— 它是 daemon 线程，
  进程退出时被回收，不会拖住关闭。

为什么不派发（``is_direct``）
----------------------------

``gui.rtp_push`` / ``rtp_queue_n`` / ``rtp_queue_clear`` / ``rtp_queue_stat`` 这四个
函数**一行 Qt 代码都没有**（只碰 ``queue.Queue`` 和一把 ``threading.Lock``），所以它们
被 :meth:`GuiBuffer.mark_direct` 登记为「在调用者线程里直接执行」，不走
``GuiApi`` 的信号派发。这不是图省事：若走派发，**界面正在画重图的那 200 ms 里，
计算线程的每一次 push 都会被挂在那里等**，正好抵消掉本插件存在的意义。
（判据与禁忌见 ``zmlx/ui/gui_buffer.py`` 的 ``mark_direct`` 文档：会建控件、碰窗口、
读标签容器的函数**不能**这么登记。）
"""

import collections
import queue
import threading
import time

from zmlx.system import execute_once, warn
from zmlx.ui.pyqt import QtCore, QtWidgets

# ============================================================ 可调参数（改这里即可）
DEFAULT_CAPTION = '实时绘图'  # caption 为 None 时落到这个标签
MIN_DRAW_INTERVAL = 0.1  # 同一标签两次绘制之间的最小间隔（秒）
POLL_MIN = 0.02  # 有数据时的轮询起点（秒）
POLL_MAX = 0.5  # 空队列退避上限（秒）
POLL_FACTOR = 2.0  # 每次「弹空」时轮询间隔乘的倍数
IDLE_SLEEP = 0.02  # 所有标签都无事可做时，泵线程睡多久（秒）
DEFAULT_MAX_PENDING = 8  # 每个标签最多积压多少帧（超出丢最旧）
DEFAULT_CLEAR = True  # 每帧是否先 figure.clear()
USE_DIRECT_CALL = True  # 见模块文档末节；关掉就走普通派发（不建议）
RECENT_MAX = 50  # 「最近绘制的帧」环形缓冲长度


def _norm_caption(caption):
    """把 caption 规范化成非空 str（队列名与标签页标题是同一个字符串）."""
    if caption is None:
        return DEFAULT_CAPTION
    if not isinstance(caption, str):
        return str(caption)
    caption = caption.strip()
    return caption if len(caption) > 0 else DEFAULT_CAPTION


class _Task:
    """队列里的一帧：**画什么**（kernel）、**画谁**（data）、**怎么画**（选项）."""

    __slots__ = ('kernel', 'data', 'clear', 'suptitle', 'tight_layout', 'seq')

    def __init__(self, kernel, data, clear, suptitle, tight_layout, seq=0):
        self.kernel = kernel
        self.data = data
        self.clear = clear
        self.suptitle = suptitle
        self.tight_layout = tight_layout
        self.seq = seq  # 该标签内的帧序号（从 1 开始，仅用于面板显示）

    def __repr__(self):
        return f'_Task(#{self.seq}, kernel={self.kernel!r}, data={self.data!r})'


class _Slot:
    """一个标签的独立通道：队列 + 节流状态 + 统计.

    ⚠️ 字段由泵线程与 ``rtp_push`` 共同读写，**一律在 :attr:`_PlotPump._lock` 内访问**
    （``stat`` / ``n_pending`` 也照此办）。
    """

    __slots__ = ('caption', 'queue', 'max_pending', 'poll_interval', 'next_poll',
                 'next_draw', 'n_pushed', 'n_drawn', 'n_dropped', 'n_failed',
                 'last_cost', 'error')

    def __init__(self, caption, max_pending=DEFAULT_MAX_PENDING):
        self.caption = caption
        self.queue = queue.Queue()
        self.max_pending = max_pending
        self.poll_interval = POLL_MIN
        self.next_poll = 0.0  # 下次**允许轮询**的时刻（monotonic）
        self.next_draw = 0.0  # 下次**允许绘制**的时刻（monotonic）
        self.n_pushed = 0
        self.n_drawn = 0
        self.n_dropped = 0
        self.n_failed = 0
        self.last_cost = 0.0
        self.error = None

    def __repr__(self):
        return (f'_Slot({self.caption!r}, pending={self.queue.qsize()}, '
                f'drawn={self.n_drawn}, dropped={self.n_dropped})')


def _gui_draw(kernel, data, caption, clear, suptitle, tight_layout):
    """真正的绘制（**泵线程调用，阻塞到 GUI 线程画完**）.

    ⚠️ 这里只用 ``gui.plot`` 这一条 GUI 命令，不直接碰任何控件：建页 / 跑回调 /
    ``canvas.draw()`` 全在那一次命令里完成（见 ``zmlx/ui/gui_buffer.py`` 的
    ``plot`` 文档）。所以本函数不含任何 Qt 代码。
    """
    from zmlx.ui import gui
    return gui.plot(kernel, data, caption=caption, clear=clear,
                    suptitle=suptitle, tight_layout=tight_layout)


class _PlotPump:
    """绘图泵：一个常驻线程，管 N 个标签的队列.

    Args:
        draw: 真正的绘制实现，签名 ``draw(kernel, data, caption, clear, suptitle,
            tight_layout)``。默认 :func:`_gui_draw`；离线自测时注入假的实现。
        autostart: 第一次 ``push`` 时若线程还没起，是否顺手起一个。正常路径由
            :func:`setup_ui` 起线程，这个兜底只为「直接 import 本模块」的场景；
            自测里传 ``False`` 以便只验证队列行为。
    """

    def __init__(self, draw=None, autostart=True):
        self._draw_impl = _gui_draw if draw is None else draw
        self._lock = threading.Lock()
        self._slots = {}  # caption -> _Slot
        self._thread = None
        self._started = False  # ``start`` **只起一次**（``stop`` 之后不复活，要复活用 ``restart``）
        self._autostart = autostart
        self._stop_ev = None  # 当前那一代线程的停止标志（每代一个，见 restart）
        #: 「最近绘制了哪些帧」的环形缓冲：(caption, seq, 完成时刻, 耗时)
        self._recent = collections.deque(maxlen=RECENT_MAX)
        # ---- 三个可在控制面板上现场调的量（泵线程每轮读一次，改了就生效）
        self.min_draw_interval = MIN_DRAW_INTERVAL
        self.idle_sleep = IDLE_SLEEP
        self.max_pending = DEFAULT_MAX_PENDING  # 新建标签时用的积压上限

    # ============================================================ 生产侧
    def push(self, kernel, data, caption=None, *, clear=None, suptitle=None,
             tight_layout=None, max_pending=None):
        """压入一帧（**O(1)，不阻塞界面**）."""
        if not callable(kernel):
            raise TypeError(f'kernel 必须是可调用对象（原型 kernel(figure, data)），'
                            f'收到: {kernel!r}')
        caption = _norm_caption(caption)
        if clear is None:
            clear = DEFAULT_CLEAR
        with self._lock:
            slot = self._slots.get(caption)
            if slot is None:
                slot = _Slot(caption, self.max_pending)
                self._slots[caption] = slot
            if max_pending is not None:
                slot.max_pending = max(int(max_pending), 1)
            slot.n_pushed += 1
            slot.queue.put(_Task(kernel, data, bool(clear), suptitle,
                                 tight_layout, seq=slot.n_pushed))
            _trim(slot)  # 超出上限 ⇒ 丢最旧的
            # 新数据到达 ⇒ 立刻回到密集轮询（退避只惩罚「长时间没数据」的标签）
            slot.poll_interval = POLL_MIN
            slot.next_poll = 0.0
            pending = slot.queue.qsize()
        if self._autostart and not self._started:
            self.start()  # 兜底：正常情况下 setup_ui 已经起过线程
        return pending

    def n_pending(self, caption=None):
        """尚未绘制的帧数（``caption=None`` 时对所有标签求和）."""
        with self._lock:
            if caption is None:
                return sum(slot.queue.qsize() for slot in self._slots.values())
            slot = self._slots.get(_norm_caption(caption))
            return 0 if slot is None else slot.queue.qsize()

    def clear(self, caption=None):
        """丢弃尚未绘制的帧，返回丢弃的帧数（**不终止**标签，后续 push 照常绘制）."""
        with self._lock:
            if caption is None:
                slots = list(self._slots.values())
            else:
                slot = self._slots.get(_norm_caption(caption))
                slots = [] if slot is None else [slot]
            n = 0
            for slot in slots:
                n += _drain(slot)
        return n

    def stat(self, caption=None):
        """返回统计（dict）。``caption=None`` 时返回 ``{caption: 统计}`` 的字典."""
        with self._lock:
            if caption is None:
                return {cap: _slot_stat(slot) for cap, slot in self._slots.items()}
            slot = self._slots.get(_norm_caption(caption))
            return None if slot is None else _slot_stat(slot)

    def recent(self, n=20):
        """最近画完的 ``n`` 帧，**最新在前**：``[(caption, 帧序号, 完成时刻, 耗时)]``.

        「帧序号」是该标签自创建以来的第几次 ``push``（不是第几次绘制）——
        于是「推送 40 帧、只画了 17 帧」会表现为序号上的**跳号**，跳过的就是被丢掉的。
        """
        with self._lock:
            items = list(self._recent)[-max(int(n), 0):]
        return items[::-1]

    def set_max_pending(self, n):
        """设置所有标签的积压上限（含已存在的标签，超出立刻丢最旧）."""
        n = max(int(n), 1)
        with self._lock:
            self.max_pending = n
            for slot in self._slots.values():
                slot.max_pending = n
                _trim(slot)
        return n

    # ============================================================ 泵线程
    @property
    def running(self):
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self):
        """启动泵线程（幂等；``start`` 对**同一代**只生效一次）.

        ⚠️ **每一代线程带自己的停止标志**（``_stop_ev``），而不是共用一个
        ``Event``：:meth:`restart` 先 ``set`` 旧的、再建新的，如果共用一个对象，
        新线程的 ``clear()`` 会把旧的复活 ⇒ 两条线程同时画。
        """
        with self._lock:
            if self._started:
                return self._thread
            self._started = True
            ev = threading.Event()
            self._stop_ev = ev
            thread = threading.Thread(target=self._loop, args=(ev,),
                                      name='zmlx-plot-pump', daemon=True)
            self._thread = thread
        thread.start()
        return thread

    def stop(self):
        """请求泵线程退出（协作式：最多等一个轮询周期）."""
        with self._lock:
            ev = self._stop_ev
        if ev is not None:
            ev.set()

    def restart(self):
        """重启泵线程：旧的置停止、立刻起一代新的（**不 join，故不会与 GUI 互等**）.

        ⚠️ **不能在这里 ``join``**：泵线程可能正阻塞在 ``gui.plot`` 上等 GUI 线程，
        而本方法通常正是**从 GUI 线程**（面板按钮）调用的 —— 一 join 就是互等死锁。
        旧线程会在它当前这一帧画完后自行退出（每轮循环开头查自己的 ``ev``）。
        """
        self.stop()
        with self._lock:
            self._started = False
        return self.start()

    def _loop(self, ev):
        while not ev.is_set():
            try:
                busy = self._tick()
            except Exception as err:  # 兜底：泵线程**绝不允许**因为异常而死掉
                warn(f'实时绘图：泵线程内部异常（已忽略）：{err!r}')
                busy = False
            if not busy:
                time.sleep(self.idle_sleep)

    def _tick(self):
        """扫一遍所有标签、各画至多一帧。返回「这一轮有没有画过东西」."""
        now = time.monotonic()
        due = []
        with self._lock:
            for slot in self._slots.values():
                if now < slot.next_poll:  # 还在退避里
                    continue
                if now < slot.next_draw:  # 本标签两次绘制的间隔还没到
                    continue
                due.append(slot)
        busy = False
        for slot in due:
            with self._lock:
                try:
                    task = slot.queue.get_nowait()
                except queue.Empty:
                    task = None
                    # 弹空 ⇒ 退避：下次更晚再来问这个标签
                    slot.poll_interval = min(slot.poll_interval * POLL_FACTOR,
                                             POLL_MAX)
                    slot.next_poll = time.monotonic() + slot.poll_interval
                else:
                    slot.poll_interval = POLL_MIN
                    slot.next_poll = 0.0
                min_interval = self.min_draw_interval
            if task is None:
                continue
            self._draw(slot, task)
            busy = True
            with self._lock:
                # 「两次绘制之间至少隔 min_draw_interval」按**画完之后**起算
                slot.next_draw = time.monotonic() + min_interval
        return busy

    def _draw(self, slot, task):
        """画一帧（在泵线程里阻塞执行；异常一律就地吞掉并记账）."""
        t0 = time.monotonic()
        try:
            self._draw_impl(task.kernel, task.data, slot.caption,
                            task.clear, task.suptitle, task.tight_layout)
        except Exception as err:
            msg = repr(err)
            with self._lock:
                slot.n_failed += 1
                first = msg != slot.error  # 同样的错只报一次，避免每帧刷屏
                slot.error = msg
            if first:
                warn(f'实时绘图：标签<{slot.caption}>绘制失败：{err!r}')
        else:
            with self._lock:
                slot.n_drawn += 1
                slot.error = None
        finally:
            with self._lock:
                cost = time.monotonic() - t0
                slot.last_cost = cost
                self._recent.append((slot.caption, task.seq, time.time(), cost))


def _slot_stat(slot):
    """把一个 :class:`_Slot` 摊成 dict（调用方**必须**已持锁）."""
    return {
        'caption': slot.caption,
        'pending': slot.queue.qsize(),
        'pushed': slot.n_pushed,
        'drawn': slot.n_drawn,
        'dropped': slot.n_dropped,
        'failed': slot.n_failed,
        'interval': slot.poll_interval,  # 当前轮询间隔（已退避到多少）
        'cost': slot.last_cost,  # 最近一帧的耗时（含等 GUI 的时间）
        'error': slot.error,
    }


def _trim(slot):
    """队列超出 ``max_pending`` 时丢**最旧**的（调用方**必须**已持锁）."""
    n = 0
    while slot.queue.qsize() > slot.max_pending:
        try:
            slot.queue.get_nowait()
        except queue.Empty:
            break
        n += 1
    slot.n_dropped += n
    return n


def _drain(slot):
    """清空一个队列，返回清掉的帧数（调用方**必须**已持锁）."""
    n = 0
    while True:
        try:
            slot.queue.get_nowait()
        except queue.Empty:
            break
        n += 1
    return n


_pump = _PlotPump()


# ============================================================ 对外的四个 gui 命令
def rtp_push(kernel, data, caption=None, *, clear=None, suptitle=None,
              tight_layout=None, max_pending=None):
    """把一帧绘图任务压进 ``caption`` 对应的队列（**计算线程调用，不阻塞**）.

    这是本插件的主接口：调用它只做「入队 + 唤醒」，**不碰界面、不跑 matplotlib**，
    因此可以在逐时间步的循环里放心调用。

    Args:
        kernel: 绘图回调，原型 ``kernel(figure, data)``。在 **GUI 线程**执行，
            收到的是本标签页的 :class:`matplotlib.figure.Figure`。
        data: 传给 ``kernel`` 的第二个参数。⚠️ 必须是**快照**（泵线程稍后才读它）。
        caption: 标签名 = 队列名 = 标签页标题；``None`` 用 ``'实时绘图'``。
            同一个 caption 的多帧**串行**画在同一个标签页上（FIFO，受
            ``MIN_DRAW_INTERVAL`` 节流）。
        clear: 每帧是否先 ``figure.clear()``；``None`` 取 ``DEFAULT_CLEAR``（``True``）。
        suptitle: 透传给 ``gui.plot``（整张图的总标题）。
        tight_layout: 透传给 ``gui.plot``（默认不做 —— 每帧都做会明显更慢）。
        max_pending: 该标签最多积压多少帧，超出丢**最旧**的；``None`` 表示不改动
            当前上限（该标签新建时是 8）。

    Returns:
        int: 压入之后该标签的待绘帧数。**可以据此自己判断是否需要降频**
        （例如连续几帧都 > 0，说明画图跟不上，应当减少推送频率或压缩数据量）。

    Note:
        无界面（headless）时 ``gui`` 没有接收方，本函数不会被执行（命令不存在），
        ``gui.rtp_push(...)`` 返回 ``None``。这是 ``gui`` 缓冲区一贯的语义，
        不是本插件特例。
    """
    return _pump.push(kernel, data, caption, clear=clear, suptitle=suptitle,
                      tight_layout=tight_layout, max_pending=max_pending)


def rtp_queue_n(caption=None):
    """当前队列中**尚未绘制**的帧数.

    Args:
        caption: 标签名；``None`` 表示**所有标签求和**。

    Returns:
        int: 待绘帧数（标签不存在时为 0）。
    """
    return _pump.n_pending(caption)


def rtp_queue_clear(caption=None):
    """丢弃尚未绘制的帧（中止一段数据流时用）.

    Args:
        caption: 标签名；``None`` 表示清空全部标签。

    Returns:
        int: 实际丢弃的帧数。
    """
    return _pump.clear(caption)


def rtp_queue_stat(caption=None):
    """返回队列 / 节流的统计信息（排查「为什么某一帧没画」用）.

    Args:
        caption: 标签名；``None`` 表示返回 ``{caption: 统计}`` 的字典。

    Returns:
        dict | None: 键为 ``caption`` / ``pending`` / ``pushed`` / ``drawn`` /
        ``dropped`` / ``failed`` / ``interval`` / ``cost`` / ``error``；
        标签不存在时为 ``None``。
    """
    return _pump.stat(caption)


# ============================================================ 演示（面板上的按钮）
DEMO_CAPTION = '实时绘图-演示'
DEMO_FRAMES = 200
DEMO_FRAME_INTERVAL = 0.05  # 推送间隔 50 ms（≈20 帧/秒）> 绘制上限 10 帧/秒
DEMO_PRINT_EVERY = 20  # 每 20 帧（≈1 s）打印一行进度


def show_demo():
    """控制面板上的「演示」按钮：在**控制台线程**里连推 200 帧正弦波.

    这就是**推荐用法**的完整示例：计算线程（这里就是控制台任务）只调 ``gui.rtp_push``，
    每帧都把「全量历史」作为快照推过去，回调拿到的是刚清空的 figure。
    20 帧/秒的推送 > 10 帧/秒的绘制上限 ⇒ 队列会稳定积压几帧，正好演示丢弃策略。

    ⚠️ 走 ``gui.start`` 而不是 ``thread_runner``：这是一段**长任务**（要能被「暂停/停止」
    打断），按 ``ui/AGENTS.md`` §6 的分工，长任务只占 ``Console`` 那一个槽位；
    任务体里用 ``gui.break_point()`` 给界面留出插手的机会。
    """
    import math
    import time

    from zmlx.ui import gui

    if gui.is_running():  # Console 单槽位：忙的时候再 start 会被**静默丢弃**（只响一声）
        gui.information('实时绘图', '控制台正在跑别的任务，等它结束后再试。')
        return

    total_seconds = DEMO_FRAMES * DEMO_FRAME_INTERVAL

    def kernel(figure, data):
        ax = figure.add_subplot(111)
        ax.plot(data['t'], data['y'], color='#d9480f', linewidth=1.2)
        ax.set_xlim(0.0, total_seconds)
        ax.set_ylim(-1.6, 1.6)
        ax.set_xlabel('t (s)')
        ax.set_ylabel('y')
        ax.set_title(f'实时绘图队列：第 {data["n"]} 帧（推送 20 帧/秒，绘制上限 10 帧/秒）')
        ax.grid(True, alpha=0.3)

    def body():
        rtp_queue_clear(DEMO_CAPTION)  # 上一次演示没画完的残帧不要了
        t0 = time.monotonic()
        for n in range(1, DEMO_FRAMES + 1):
            gui.break_point()  # 断点：用户点「暂停/继续/停止」都在这里被拦住
            t = [i * DEMO_FRAME_INTERVAL for i in range(n)]
            y = [math.sin(v * 2.0) for v in t]
            pending = gui.rtp_push(kernel, {'t': t, 'y': y, 'n': n},
                                   caption=DEMO_CAPTION)
            gui.progress(label='实时绘图演示', val_range=[0, DEMO_FRAMES], value=n)
            if n == 1 or n % DEMO_PRINT_EVERY == 0:
                st = rtp_queue_stat(DEMO_CAPTION)
                print(f'[实时绘图] 第 {n}/{DEMO_FRAMES} 帧 | 待绘 {pending} 帧 | '
                      f'已绘 {st["drawn"]} 帧、丢弃 {st["dropped"]} 帧 | '
                      f'用时 {time.monotonic() - t0:.1f} s')
            time.sleep(DEMO_FRAME_INTERVAL)
        print(f'[实时绘图] 推送完毕：共 {DEMO_FRAMES} 帧，'
              f'剩余待绘 {rtp_queue_n(DEMO_CAPTION)} 帧')

    gui.start(body,
              text_beg='开始实时绘图演示（推送 20 帧/秒，绘制上限 10 帧/秒）…',
              text_end='实时绘图演示结束',
              post_task=lambda: gui.progress(visible=False),  # 任务抛异常也会执行
              add_history=False)


# ============================================================ 控制面板（右侧标签页）


if QtWidgets is None:  # 没有 Qt（离线自测 / 纯 headless）：只留一个占位名
    RtpPanel = None
else:
    class RtpPanel(QtWidgets.QWidget):
        """实时绘图控制面板（开在**右侧**标签页，菜单「显示 → 实时绘图控制面板」）.

        三块内容，从上到下：

        1. **状态行**：泵线程是否在跑、目标 / 实测帧率、标签数、待绘 / 累计绘制 / 丢弃；
        2. **三个旋钮 + 三个按钮**：目标帧率、空闲休眠、积压上限；重启线程、清空队列、演示；
        3. **两张表**：每个标签的统计（待绘 / 已绘 / 丢弃 / 最近耗时），以及「最近画完的
           哪些帧」（帧序号 + 耗时 + 墙上时刻）。

        ⚠️ **本控件只跑在 GUI 线程**：定时器（``QTimer``，parent 是本控件）每
        :data:`REFRESH_MS` 毫秒读一次 :meth:`_PlotPump.stat`，**只在可见时跑**
        （:meth:`showEvent` 开、:meth:`hideEvent` 关）—— 切走还在刷就是白烧 CPU。
        ``stat`` 内部只持锁拷几个整数，不会阻塞泵线程，更不会调 GUI。

        ⚠️ **旋钮直接改 :data:`_pump` 的字段**（``min_draw_interval`` / ``idle_sleep`` /
        ``max_pending``）：泵线程每轮循环都现读，所以改完最迟一个轮询周期就生效，
        不需要加锁、也不涉及跨线程调 Qt（那几个字段是纯 Python 标量）。
        """

        REFRESH_MS = 200  # 刷新间隔（毫秒）
        RECENT_SHOW = 12  # 「最近绘制的帧」显示多少条

        def __init__(self, parent=None):
            super().__init__(parent)
            #: 让「历史标签页恢复」能在重启后重放回来（与 utils 里其它插件同一手法）
            self.gui_restore = 'gui.show_rtp_panel()'
            self._rows = {}  # caption -> 表格行号
            self._recent_key = None  # 上次渲染的「最新一帧」，用于避免无谓重绘
            self._last_sample = None  # (时刻, 累计绘制数)
            self._fps = 0.0  # 实测帧率（指数平滑）
            self._timer = None
            self._build()
            self.refresh()

        # ---------------------------------------------------------------- 构建
        def _build(self):
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(6)

            self._state = QtWidgets.QLabel('—')
            self._state.setWordWrap(True)
            layout.addWidget(self._state)

            form = QtWidgets.QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            form.setSpacing(4)

            self._spin_fps = QtWidgets.QSpinBox()
            self._spin_fps.setRange(1, 50)
            self._spin_fps.setSuffix(' 帧/秒')
            self._spin_fps.setToolTip(
                '同一标签两次绘制之间的最小间隔 = 1 / 帧率。\n'
                '只限制「画得多快」；推送再快也只会让队列里积压（超出上限丢最旧）。')
            form.addRow('目标帧率', self._spin_fps)

            self._spin_sleep = QtWidgets.QSpinBox()
            self._spin_sleep.setRange(1, 200)
            self._spin_sleep.setSuffix(' ms')
            self._spin_sleep.setToolTip(
                '泵线程在所有队列都空时睡多久。\n'
                '调小 ⇒ 新数据更快被看到（响应快、空转多一点）；调大 ⇒ 更省 CPU。')
            form.addRow('空闲休眠', self._spin_sleep)

            self._spin_pending = QtWidgets.QSpinBox()
            self._spin_pending.setRange(1, 128)
            self._spin_pending.setSuffix(' 帧')
            self._spin_pending.setToolTip(
                '每个标签最多积压多少帧，超出**丢最旧的**（实时绘图要最新，不要完整）。\n'
                '改完对已存在的标签立刻生效。')
            form.addRow('积压上限', self._spin_pending)
            layout.addLayout(form)

            # 先把值填好再连信号，避免初始化时触发写回
            self._spin_fps.setValue(int(round(1.0 / max(_pump.min_draw_interval, 1e-3))))
            self._spin_sleep.setValue(int(round(_pump.idle_sleep * 1000)))
            self._spin_pending.setValue(int(_pump.max_pending))
            self._spin_fps.valueChanged.connect(self._on_fps)
            self._spin_sleep.valueChanged.connect(self._on_sleep)
            self._spin_pending.valueChanged.connect(self._on_pending)

            row = QtWidgets.QHBoxLayout()
            row.setSpacing(4)
            self._btn_restart = QtWidgets.QPushButton('重启线程')
            self._btn_restart.setToolTip('丢掉当前那一代泵线程，立刻换一条新的（不 join，界面不卡）')
            self._btn_restart.clicked.connect(self._on_restart)
            self._btn_clear = QtWidgets.QPushButton('清空队列')
            self._btn_clear.setToolTip('丢弃所有标签里尚未绘制的帧')
            self._btn_clear.clicked.connect(self._on_clear)
            self._btn_demo = QtWidgets.QPushButton('演示')
            self._btn_demo.setToolTip('在控制台里连推 200 帧正弦波（可暂停/停止）')
            self._btn_demo.clicked.connect(show_demo)
            for btn in (self._btn_restart, self._btn_clear, self._btn_demo):
                row.addWidget(btn)
            layout.addLayout(row)

            self._table = QtWidgets.QTableWidget(0, 5)
            self._table.setHorizontalHeaderLabels(
                ['标签', '待绘', '已绘', '丢弃', '耗时 ms'])
            self._table.verticalHeader().setVisible(False)
            # ⚠️ 整表禁编辑：Qt 默认双击就弹行内编辑器（见 viewers.py 里同一处说明）
            self._table.setEditTriggers(
                QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self._table.horizontalHeader().setStretchLastSection(True)
            self._table.setColumnWidth(0, 96)
            self._table.setMinimumHeight(90)
            layout.addWidget(self._table, 1)

            layout.addWidget(QtWidgets.QLabel('最近绘制'))
            self._recent = QtWidgets.QListWidget()
            self._recent.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            # 右侧面板很窄：条目只做右端省略，**不要**长出横向滚动条
            self._recent.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)
            self._recent.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._recent.setMinimumHeight(80)
            self._recent.setToolTip('帧序号是该标签的第几次 push —— 跳号的就是被丢掉的帧')
            layout.addWidget(self._recent, 1)

        # ---------------------------------------------------------------- 旋钮
        def _on_fps(self, value):
            _pump.min_draw_interval = 1.0 / max(value, 1)
            self.refresh()

        def _on_sleep(self, value):
            _pump.idle_sleep = max(value, 1) / 1000.0
            self.refresh()

        def _on_pending(self, value):
            _pump.set_max_pending(value)
            self.refresh()

        def _on_restart(self):
            _pump.restart()
            print(f'[实时绘图] 泵线程已重启：{"在跑" if _pump.running else "未在跑"}')
            self.refresh()

        def _on_clear(self):
            n = _pump.clear()
            print(f'[实时绘图] 已清空队列：丢弃 {n} 帧')
            self.refresh()

        # ---------------------------------------------------------------- 刷新
        def showEvent(self, event):
            """可见时才刷新（切走就停，省 CPU）。"""
            super().showEvent(event)
            self._last_sample = None  # 重新开始测速，避免用「刚才那段空档」算帧率
            if self._timer is None:
                self._timer = QtCore.QTimer(self)
                self._timer.timeout.connect(self.refresh)
            self._timer.start(self.REFRESH_MS)
            self.refresh()

        def hideEvent(self, event):
            """隐藏时停掉定时刷新。"""
            if self._timer is not None:
                self._timer.stop()
            super().hideEvent(event)

        def refresh(self):
            """把泵的最新状态搬到界面上（GUI 线程；200 ms 一次）."""
            stats = _pump.stat()
            total_pending = sum(st['pending'] for st in stats.values())
            total_drawn = sum(st['drawn'] for st in stats.values())
            total_drop = sum(st['dropped'] for st in stats.values())
            total_fail = sum(st['failed'] for st in stats.values())

            now = time.monotonic()
            if self._last_sample is not None:
                dt = now - self._last_sample[0]
                if dt > 1e-3:
                    inst = (total_drawn - self._last_sample[1]) / dt
                    self._fps = inst if self._fps <= 0 else \
                        0.6 * self._fps + 0.4 * inst
            self._last_sample = (now, total_drawn)

            target = 1.0 / max(_pump.min_draw_interval, 1e-3)
            self._state.setText(
                f'泵线程：{"运行中" if _pump.running else "已停止"}　'
                f'目标 {target:.0f} / 实测 {self._fps:.1f} 帧/秒\n'
                f'标签 {len(stats)} 个　待绘 {total_pending} 帧　'
                f'累计绘制 {total_drawn} 帧　丢弃 {total_drop} 帧'
                + (f'　失败 {total_fail} 帧' if total_fail else ''))

            self._sync_table(stats)
            self._sync_recent()

        def _sync_table(self, stats):
            """按 caption 增量更新表格（不重建行，保留用户的滚动与选中）."""
            for caption, st in stats.items():
                row = self._rows.get(caption)
                if row is None:
                    row = self._table.rowCount()
                    self._table.insertRow(row)
                    self._rows[caption] = row
                    for col, text in enumerate([caption, '0', '0', '0', '0.0']):
                        self._table.setItem(row, col, _make_item(text))
                for col, text in enumerate(
                        (f'{st["pending"]}', f'{st["drawn"]}', f'{st["dropped"]}',
                         f'{st["cost"] * 1000:.1f}'), start=1):
                    item = self._table.item(row, col)
                    if item is not None and item.text() != text:
                        item.setText(text)

        def _sync_recent(self):
            """重建「最近绘制」列表 —— 只在真的多画了一帧时动它（否则会闪）."""
            items = _pump.recent(self.RECENT_SHOW)
            key = items[0] if items else None
            if key == self._recent_key:
                return
            self._recent_key = key
            self._recent.clear()
            if not items:
                self._recent.addItem('（还没有绘制）')
                return
            for caption, seq, stamp, cost in items:
                self._recent.addItem(
                    f'{caption} #{seq}　{cost * 1000:.1f} ms　'
                    f'{time.strftime("%H:%M:%S", time.localtime(stamp))}')


def _make_item(text):
    """造一个**只读**单元格（清掉 Qt 默认给的 ``ItemIsEditable`` 标志）."""
    item = QtWidgets.QTableWidgetItem(text)
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item


def show_rtp_panel():
    """打开（或切到）**右侧**的「实时绘图控制面板」标签页.

    ⚠️ 只通过 ``gui.get_widget`` 打开：标签页只有一个，重复调用只是切到前面。

    Returns:
        RtpPanel | None: 打开（或切到）的控件；没有 Qt 时为 ``None``。
    """
    from zmlx.ui import gui

    if RtpPanel is None:
        print('实时绘图：没有可用的 Qt，控制面板打不开。')
        return None
    return gui.get_widget(
        the_type=RtpPanel,
        caption='实时绘图',
        position='right',
        on_top=True,
        icon='matplotlib',
        tooltip='实时绘图队列的控制面板：帧率 / 休眠 / 积压上限、各标签统计、最近绘制的帧',
    )


# ============================================================ 注册
@execute_once(file=__file__)
def setup_ui():
    """注册 gui 命令、登记直连、挂菜单、启动泵线程（本文件作为插件被 ``load_all`` 执行时调用）.

    ⚠️ 本函数在**控制台内核线程**里执行；``gui.add_func`` / ``gui.add_action`` 会被
    GuiApi 派发到主线程执行，所以这里直接写 ``gui.xxx`` 即可。

    ⚠️ 加载期只做「接线 + 起一个空闲线程」这两件轻活（见 ``plugins/AGENTS.md`` §0.5）：
    泵线程启动后立刻进入退避，队列全空时几乎不占 CPU；控制面板是**点了菜单才建**。

    ⚠️ 只有四条纯队列命令登记 ``mark_direct``；``show_rtp_panel`` **不能**登记 ——
    它会 ``gui.get_widget`` 建控件，必须在 GUI 线程执行。
    """
    from zmlx.ui import gui

    commands = {
        'rtp_push': rtp_push,
        'rtp_queue_n': rtp_queue_n,
        'rtp_queue_clear': rtp_queue_clear,
        'rtp_queue_stat': rtp_queue_stat,
    }
    for name, func in commands.items():
        gui.add_func(name, func)

    gui.add_func('show_rtp_panel', show_rtp_panel)

    if USE_DIRECT_CALL:
        # 这四个函数一行 Qt 代码都没有（只碰 queue + threading.Lock），登记成直连后
        # 计算线程的 push 不再等待 GUI 事件循环 —— 正是本插件要的效果。
        # 判据见 zmlx/ui/gui_buffer.py 的 GuiBuffer.mark_direct。
        for name in commands:
            try:
                gui.mark_direct(name)
            except Exception as err:  # 老版本没有 mark_direct 也不影响功能
                warn(f'实时绘图：把 <{name}> 登记为直连失败（退回普通派发）：{err!r}')

    gui.add_action(
        menu='显示',
        name='rtp_panel',
        text='实时绘图控制面板',
        icon='matplotlib',
        tooltip='实时绘图队列的运行状态与控制：帧率、休眠、积压上限、重启线程、各标签统计',
        slot=show_rtp_panel,
        overwrite=False,
    )

    _pump.start()


if __name__ == '__zml_plugin__':
    # 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**。
    setup_ui()


if __name__ == '__main__':
    # 直接运行本文件（__name__ == '__main__'）：离线自测，不需要 Qt、不开窗口。
    # ⚠️ 用独立的 if 而不是 elif：两种运行方式互不相干，各自判断更清楚。
    import sys


    def _wait_until(cond, timeout):
        """轮询等待条件成立，返回是否等到（不依赖事件循环）."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if cond():
                return True
            time.sleep(0.005)
        return cond()


    def _noop_kernel(figure, data):
        """自测用的空回调."""
        return None


    def test_1():
        """离线自测：队列 / FIFO / 限频 / 退避 / 唤醒 / 丢最旧 / 多标签独立."""
        ok = []

        def check(name, cond, extra=''):
            ok.append(bool(cond))
            print(('PASS ' if cond else 'FAIL ') + name +
                  ('' if extra == '' else f'  {extra}'))

        # ---------------------------------------------- 生产侧：积压上限、丢最旧
        p = _PlotPump(draw=lambda *a: None, autostart=False)
        for i in range(5):
            p.push(_noop_kernel, i, 'a', max_pending=2)
        check('max_pending=2 ⇒ 只剩 2 帧', p.n_pending('a') == 2, p.n_pending('a'))
        st = p.stat('a')
        check('丢弃计数 = 3', st['dropped'] == 3, st['dropped'])
        kept = []
        while True:
            try:
                kept.append(p._slots['a'].queue.get_nowait().data)
            except queue.Empty:
                break
        check('丢的是最旧的两帧（留下 3、4）', kept == [3, 4], kept)

        # ---------------------------------------------- 泵线程：FIFO + 限频
        records = []

        def fake_draw(kernel, data, caption, clear, suptitle, tight_layout):
            records.append({'caption': caption, 'data': data,
                            't': time.monotonic(), 'clear': clear})

        p = _PlotPump(draw=fake_draw)
        p.start()
        for i in range(4):
            p.push(_noop_kernel, i, 'x')
        check('泵线程在跑', p.running)
        got = _wait_until(lambda: len(records) >= 4, 3.0)
        check('4 帧全部画出', got and len(records) == 4, len(records))
        gaps = [b['t'] - a['t'] for a, b in zip(records, records[1:])]
        check('同一标签两帧间隔 ≥ 0.1 s（限频）',
              len(gaps) > 0 and min(gaps) >= MIN_DRAW_INTERVAL - 0.01,
              f'{min(gaps):.3f}' if gaps else 'no gaps')
        check('FIFO：数据顺序 0,1,2,3',
              [r['data'] for r in records] == [0, 1, 2, 3],
              [r['data'] for r in records])
        check('clear 默认 True 传到底', all(r['clear'] is True for r in records))

        # ---------------------------------------------- 退避与唤醒
        slot = p._slots['x']
        far = _wait_until(lambda: slot.poll_interval >= POLL_MAX - 1e-9, 4.0)
        check('空队列 ⇒ 轮询间隔退避到上限', far, f'{slot.poll_interval:.3f}')

        n0 = len(records)
        t_push = time.monotonic()
        p.push(_noop_kernel, 99, 'x')
        check('push 之后立刻回到密集轮询', slot.poll_interval == POLL_MIN,
              f'{slot.poll_interval:.3f}')
        woke = _wait_until(lambda: len(records) > n0, 2.0)
        delay = records[-1]['t'] - t_push if len(records) > n0 else -1.0
        check('新数据不被退避拖住（延迟 < 0.3 s）', woke and delay < 0.3,
              f'{delay:.3f}')

        # ---------------------------------------------- 多标签互不干扰
        rec2 = []

        def fake_draw2(kernel, data, caption, clear, suptitle, tight_layout):
            rec2.append((caption, data, time.monotonic()))

        p2 = _PlotPump(draw=fake_draw2)
        p2.start()
        for i in range(3):
            p2.push(_noop_kernel, i, '甲')
            p2.push(_noop_kernel, i, '乙')
        _wait_until(lambda: len(rec2) >= 6, 6.0)
        by_cap = {}
        for cap, data, stamp in rec2:
            by_cap.setdefault(cap, []).append((data, stamp))
        check('两个标签各画 3 帧',
              len(by_cap.get('甲', [])) == 3 and len(by_cap.get('乙', [])) == 3,
              {k: len(v) for k, v in by_cap.items()})
        both_ok = True
        for cap, items in by_cap.items():
            gs = [b[1] - a[1] for a, b in zip(items, items[1:])]
            if gs and min(gs) < MIN_DRAW_INTERVAL - 0.01:
                both_ok = False
        check('限频按标签各自计算', both_ok)
        check('rtp_queue_n(None) 求和',
              p2.n_pending(None) == p2.n_pending('甲') + p2.n_pending('乙'),
              p2.n_pending(None))
        p2.stop()

        # ---------------------------------------------- caption 规范化与清空
        p3 = _PlotPump(draw=fake_draw, autostart=False)  # 不启动：队列内容可控
        p3.push(_noop_kernel, 0, None)
        check('caption=None ⇒ 默认标签', p3.n_pending(DEFAULT_CAPTION) == 1,
              p3.n_pending(DEFAULT_CAPTION))
        p3.push(_noop_kernel, 0, '  ')
        check('空字符串 ⇒ 默认标签', p3.n_pending(DEFAULT_CAPTION) == 2)
        n_cleared = p3.clear()
        check('clear 返回清掉的帧数', n_cleared == 2, n_cleared)
        check('清空后为 0', p3.n_pending(None) == 0)
        try:
            p3.push(None, 0, 'x')
            check('kernel 不可调用 ⇒ TypeError', False)
        except TypeError:
            check('kernel 不可调用 ⇒ TypeError', True)

        # ---------------------------------------------- 停止后不再绘制
        p3.start()
        p3.stop()
        stopped = _wait_until(lambda: not p3.running, 1.0)
        n_before = len(records)
        p3.push(_noop_kernel, 0, 'stopped')
        time.sleep(0.3)
        check('stop 之后不再绘制（push 也不会复活线程）',
              stopped and len(records) == n_before, len(records) - n_before)

        p.stop()
        print(f'---- {sum(ok)}/{len(ok)} ----')
        return 0 if all(ok) else 1


    sys.exit(test_1())
